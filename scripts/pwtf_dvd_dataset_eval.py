#!/usr/bin/env python3
"""Loop official PwTF-DVD per-video inference and print video-level AUC.

Does not download data. Labels come from labels.csv or real/fake subdirectories.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm"}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def roc_auc(labels: list[int], scores: list[float]) -> float:
    sys.path.insert(0, str(_repo_root()))
    from src.video_eval.metrics import roc_auc as _auc

    return _auc(labels, scores)


def discover_labeled_videos(dataset_dir: Path) -> list[tuple[Path, int]]:
    labels_csv = dataset_dir / "labels.csv"
    if labels_csv.exists():
        rows: list[tuple[Path, int]] = []
        with labels_csv.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                path = Path(row.get("path") or row.get("video") or "")
                if not path.is_absolute():
                    path = dataset_dir / path
                label = int(float(row.get("label") or row.get("y") or "0"))
                rows.append((path, label))
        return rows
    found: list[tuple[Path, int]] = []
    for split, label in (("real", 0), ("fake", 1)):
        folder = dataset_dir / split
        if not folder.is_dir():
            continue
        for path in sorted(folder.rglob("*")):
            if path.suffix.lower() in VIDEO_EXTS:
                found.append((path, label))
    return found


def parse_score(stdout: str, out_dir: Path) -> float | None:
    for line in reversed(stdout.splitlines()):
        lower = line.lower()
        if "score" in lower or "logit" in lower or "prob" in lower:
            parts = line.replace("=", " ").replace(":", " ").split()
            for token in reversed(parts):
                try:
                    return float(token)
                except ValueError:
                    continue
    for name in ("score.json", "result.json", "pred.json"):
        candidate = out_dir / name
        if candidate.exists():
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                for key in ("score", "pred", "prob", "logit"):
                    if key in payload:
                        return float(payload[key])
    scores_txt = list(out_dir.glob("*.txt"))
    if len(scores_txt) == 1:
        text = scores_txt[0].read_text(encoding="utf-8").strip().split()
        if text:
            try:
                return float(text[-1])
            except ValueError:
                return None
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PwTF-DVD dataset loop around official inference.")
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--weights", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--dataset-name", default="dataset")
    parser.add_argument("--smoke-limit", type=int, default=0)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)

    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.exists():
        print(f"dataset missing: {dataset_dir}", file=sys.stderr)
        return 2
    videos = discover_labeled_videos(dataset_dir)
    if args.smoke_limit and args.smoke_limit > 0:
        videos = videos[: args.smoke_limit]
    if not videos:
        print("no labeled videos (need labels.csv or real/fake dirs)", file=sys.stderr)
        return 3

    repo_dir = Path(args.repo_dir)
    infer = repo_dir / "inference" / "test_on_raw_video.py"
    out_root = Path(args.out_dir)
    out_root.mkdir(parents=True, exist_ok=True)
    score_csv = out_root / "scores.csv"
    rows: list[dict[str, str]] = []
    labels: list[int] = []
    scores: list[float] = []

    for video_path, label in videos:
        clip_out = out_root / video_path.stem
        clip_out.mkdir(parents=True, exist_ok=True)
        cmd = [
            args.python,
            str(infer),
            "--video",
            str(video_path),
            "--out_dir",
            str(clip_out),
            "--model_path",
            args.weights,
        ]
        proc = subprocess.run(
            cmd, cwd=repo_dir, capture_output=True, text=True, check=False
        )
        combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
        (clip_out / "infer.log").write_text(combined, encoding="utf-8")
        score = parse_score(combined, clip_out)
        if score is None or proc.returncode != 0:
            continue
        labels.append(label)
        scores.append(score)
        rows.append(
            {
                "video": str(video_path),
                "label": str(label),
                "score": str(score),
            }
        )

    with score_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video", "label", "score"])
        writer.writeheader()
        writer.writerows(rows)

    if len(set(labels)) < 2 or len(scores) < 2:
        print("not enough scored real/fake videos for AUC", file=sys.stderr)
        return 4
    auc = roc_auc(labels, scores)
    print(f"{args.dataset_name} AUC (video-level): {auc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
