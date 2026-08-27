#!/usr/bin/env python3
"""Score raw mp4/mkv in real/fake dirs with official RealForensics stage2 weights.

Does not call stage2/eval.py and never maps the set name to CelebDF.

Official test_step: logits = df_head(backbone(video_clip)). This wrapper loads
CSN-R101 + MeanLinear from the checkpoint, crops faces with official
extract_faces.py (150x150), then CenterCrop 140 / Resize 112 / ImageNet norm,
25-frame non-overlapping clips, mean logit per video.

``--smoke-limit`` slices the concatenated real-then-fake list (all reals first).
Use mentor_swap_200_smoke (8+8) for smoke; do not slice the 200+200 set.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch
from torchvision.transforms import CenterCrop, Resize

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.raw_video_infer import (  # noqa: E402
    FACE_ALIGN_HINT,
    align_frames_and_landmarks,
    clip_starts,
    crop_faces_realforensics,
    landmarks_68,
    load_frames_rgb,
)
from src.video_eval.dataset_io import (  # noqa: E402
    apply_smoke_limit,
    discover_labeled_videos,
    print_video_auc,
    write_scores_csv,
)

PYTORCHVIDEO_HINT = (
    "Install into the realforensics env without upgrading torch:\n"
    "  python -m pip install pytorchvideo==0.1.2 iopath==0.1.9 "
    "fvcore==0.1.5.post20221221 yacs==0.1.8 einops==0.3.2 av==8.0.3 "
    "--no-deps -i https://pypi.tuna.tsinghua.edu.cn/simple --default-timeout=1000"
)


def resolve_weights(weights: Path, repo_dir: Path) -> Path:
    candidates = [
        weights,
        repo_dir / "stage2" / "weights" / weights.name,
        repo_dir / "stage2" / "weights" / Path(weights).name,
    ]
    for path in candidates:
        if path.is_file():
            return path
    print(f"ERROR: weights not found; tried {candidates}", file=sys.stderr)
    raise SystemExit(6)


def _strip_prefix(state: dict, prefix: str) -> dict:
    out = {}
    for key, value in state.items():
        if key.startswith(prefix):
            out[key[len(prefix) :]] = value
        elif key.startswith("model." + prefix):
            out[key[len("model." + prefix) :]] = value
    return out


def load_realforensics(repo_dir: Path, weights: Path, device: str):
    stage2 = repo_dir / "stage2"
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))
    if str(stage2) not in sys.path:
        sys.path.insert(0, str(stage2))
    os.chdir(repo_dir)
    try:
        from models.backbones.csn import csn_temporal_no_head
        from models.linear import MeanLinear
    except ImportError as exc:
        print(
            f"ERROR: cannot import RealForensics CSN/MeanLinear from {repo_dir}: {exc}\n"
            f"{PYTORCHVIDEO_HINT}",
            file=sys.stderr,
        )
        raise SystemExit(6) from exc
    ckpt = torch.load(str(weights), map_location="cpu")
    if not isinstance(ckpt, dict):
        print(f"ERROR: unexpected checkpoint type {type(ckpt)}", file=sys.stderr)
        raise SystemExit(6)
    if "state_dict" in ckpt and isinstance(ckpt["state_dict"], dict):
        ckpt = ckpt["state_dict"]
    backbone = csn_temporal_no_head(model_depth=101, input_channel=3)
    df_head = MeanLinear(2048, out_dim=1, norm_linear=True, scale=64)
    bb_w = _strip_prefix(ckpt, "backbone.")
    head_w = _strip_prefix(ckpt, "df_head.")
    if not bb_w or not head_w:
        print(
            "ERROR: checkpoint missing backbone./df_head. keys "
            f"(got {list(ckpt)[:8]}...).",
            file=sys.stderr,
        )
        raise SystemExit(6)
    backbone.load_state_dict(bb_w, strict=True)
    df_head.load_state_dict(head_w, strict=True)
    backbone.to(device).eval()
    df_head.to(device).eval()
    return backbone, df_head


def _clip_tensor(faces: list[np.ndarray], device: str) -> torch.Tensor:
    clip = np.stack(faces, axis=0)
    tensor = torch.from_numpy(clip).permute(3, 0, 1, 2).float() / 255.0
    tensor = Resize(112)(CenterCrop(140)(tensor))
    mean = torch.tensor([0.485, 0.456, 0.406], dtype=tensor.dtype)[:, None, None, None]
    std = torch.tensor([0.229, 0.224, 0.225], dtype=tensor.dtype)[:, None, None, None]
    tensor = (tensor - mean) / std
    return tensor.unsqueeze(0).to(device)


def score_video(
    video_path: Path,
    *,
    backbone,
    df_head,
    repo_dir: Path,
    device: str,
    frames_per_clip: int,
    max_frames: int,
) -> float:
    frames = load_frames_rgb(video_path, max_frames)
    raw_lm = landmarks_68(frames, device=device)
    frames, lms = align_frames_and_landmarks(frames, raw_lm)
    # Official extract_faces.py reads cv2 BGR; convert back to RGB for ImageNet.
    bgr = [frame[:, :, ::-1].copy() for frame in frames]
    faces_bgr = crop_faces_realforensics(bgr, lms, repo_dir)
    faces = [
        crop[:, :, ::-1].copy() if crop.ndim == 3 else crop for crop in faces_bgr
    ]
    starts = clip_starts(len(faces), frames_per_clip, max_frames)
    if not starts:
        raise RuntimeError(
            f"need >= {frames_per_clip} face crops, got {len(faces)}"
        )
    clip_logits: list[torch.Tensor] = []
    with torch.no_grad():
        for start in starts:
            tensor = _clip_tensor(faces[start : start + frames_per_clip], device)
            logit = df_head(backbone(tensor))
            clip_logits.append(logit.reshape(-1)[0].detach().float().cpu())
    return float(torch.stack(clip_logits).mean().item())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RealForensics raw-video loop (mentor real/fake dirs)."
    )
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--dataset-dir", default="")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dataset-name", default="dataset")
    parser.add_argument("--smoke-limit", type=int, default=0)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--frames-per-clip", type=int, default=25)
    parser.add_argument("--max-frames", type=int, default=110)
    parser.add_argument("--video", default="", help="Score a single raw video.")
    parser.add_argument("--label", type=int, default=-1, help="Label for --video.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_dir = Path(args.repo_dir)
    if not repo_dir.is_dir():
        print(f"repo missing: {repo_dir}", file=sys.stderr)
        return 2
    device = args.device
    if str(device).startswith("cuda") and not torch.cuda.is_available():
        print("ERROR: CUDA not available; RealForensics CSN expects GPU.", file=sys.stderr)
        return 5

    videos: list[tuple[Path, int]]
    if args.video:
        videos = [(Path(args.video), args.label)]
    else:
        dataset_dir = Path(args.dataset_dir)
        if not dataset_dir.exists():
            print(f"dataset missing: {dataset_dir}", file=sys.stderr)
            return 2
        videos = apply_smoke_limit(
            discover_labeled_videos(dataset_dir), args.smoke_limit
        )
        if not videos:
            print("no labeled videos (need labels.csv or real/fake dirs)", file=sys.stderr)
            return 3

    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    weights = resolve_weights(Path(args.weights), repo_dir)
    backbone, df_head = load_realforensics(repo_dir, weights, device)

    rows: list[dict[str, str]] = []
    labels: list[int] = []
    scores: list[float] = []
    for video_path, label in videos:
        clip_out = out_root / video_path.stem
        clip_out.mkdir(parents=True, exist_ok=True)
        log_path = clip_out / "infer.log"
        try:
            score = score_video(
                video_path,
                backbone=backbone,
                df_head=df_head,
                repo_dir=repo_dir,
                device=device,
                frames_per_clip=args.frames_per_clip,
                max_frames=args.max_frames,
            )
        except SystemExit:
            raise
        except Exception as exc:
            msg = f"FAILED {video_path}: {exc}\n{FACE_ALIGN_HINT}\n{PYTORCHVIDEO_HINT}\n"
            log_path.write_text(msg, encoding="utf-8")
            print(msg, file=sys.stderr)
            continue
        line = f"Average prediction score: {score:.6f}\n"
        log_path.write_text(line, encoding="utf-8")
        print(f"{video_path} {line.strip()}")
        if label < 0:
            continue
        labels.append(label)
        scores.append(score)
        rows.append({"video": str(video_path), "label": str(label), "score": str(score)})

    write_scores_csv(out_root / "scores.csv", rows)
    if args.video and args.label < 0:
        return 0
    return print_video_auc(args.dataset_name, labels, scores)


if __name__ == "__main__":
    raise SystemExit(main())
