#!/usr/bin/env python3
"""Score raw mp4/mkv in real/fake dirs with official LipForensics weights.

Does not call evaluate.py and never maps the set name to CelebDF.

Official path (evaluate.py): logits = model(mouth_clips, lengths=[25]*B), then
mean clip logits per video. This wrapper does the same after FAN landmarks +
official mouth crop (preprocessing/utils.py).

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
from torchvision.transforms import CenterCrop, Compose

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.raw_video_infer import (  # noqa: E402
    FACE_ALIGN_HINT,
    align_frames_and_landmarks,
    clip_starts,
    crop_mouths_lipforensics,
    landmarks_68,
    load_frames_rgb,
)
from src.video_eval.dataset_io import (  # noqa: E402
    apply_smoke_limit,
    discover_labeled_videos,
    print_video_auc,
    write_scores_csv,
)


def _add_repo_to_path(repo_dir: Path) -> None:
    os.chdir(repo_dir)
    if str(repo_dir) not in sys.path:
        sys.path.insert(0, str(repo_dir))


def load_lipforensics(repo_dir: Path, weights: Path, device: str):
    _add_repo_to_path(repo_dir)
    try:
        from data.transforms import NormalizeVideo, ToTensorVideo
        from models.spatiotemporal_net import get_model
    except ImportError as exc:
        print(
            f"ERROR: cannot import LipForensics modules from {repo_dir}: {exc}\n"
            "Clone ahaliassos/LipForensics and install its requirements.txt.",
            file=sys.stderr,
        )
        raise SystemExit(6) from exc
    if not weights.is_file():
        print(f"ERROR: weights missing: {weights}", file=sys.stderr)
        raise SystemExit(6)
    try:
        model = get_model(weights_forgery_path=str(weights), device=device)
    except Exception as exc:
        print(
            f"ERROR: LipForensics get_model failed ({exc}). Need CUDA and "
            "models/configs/lrw_resnet18_mstcn.json in the clone.",
            file=sys.stderr,
        )
        raise SystemExit(6) from exc
    model.eval()
    transform = Compose(
        [ToTensorVideo(), CenterCrop((88, 88)), NormalizeVideo((0.421,), (0.165,))]
    )
    return model, transform


def score_video(
    video_path: Path,
    *,
    model,
    transform,
    repo_dir: Path,
    device: str,
    frames_per_clip: int,
    max_frames: int,
) -> float:
    frames = load_frames_rgb(video_path, max_frames)
    raw_lm = landmarks_68(frames, device=device)
    frames, lms = align_frames_and_landmarks(frames, raw_lm)
    mouths = crop_mouths_lipforensics(frames, lms, repo_dir)
    starts = clip_starts(len(mouths), frames_per_clip, max_frames)
    if not starts:
        raise RuntimeError(
            f"need >= {frames_per_clip} mouth crops, got {len(mouths)}"
        )
    clip_logits: list[torch.Tensor] = []
    with torch.no_grad():
        for start in starts:
            clip = mouths[start : start + frames_per_clip]
            sample = np.stack(clip, axis=0)
            tensor = torch.from_numpy(sample).unsqueeze(-1)
            tensor = transform(tensor).unsqueeze(0).to(device)
            logit = model(tensor, lengths=[frames_per_clip])
            clip_logits.append(logit.reshape(-1)[0].detach().float().cpu())
    return float(torch.stack(clip_logits).mean().item())


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LipForensics raw-video loop (mentor real/fake dirs)."
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
        print("ERROR: CUDA not available; LipForensics weights expect GPU.", file=sys.stderr)
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
    model, transform = load_lipforensics(repo_dir, Path(args.weights), device)

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
                model=model,
                transform=transform,
                repo_dir=repo_dir,
                device=device,
                frames_per_clip=args.frames_per_clip,
                max_frames=args.max_frames,
            )
        except SystemExit:
            raise
        except Exception as exc:
            msg = f"FAILED {video_path}: {exc}\n{FACE_ALIGN_HINT}\n"
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
