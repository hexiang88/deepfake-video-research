"""Discover labeled raw videos (labels.csv or real/fake dirs) for custom eval loops."""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov", ".webm"}
MENTOR_PREFIX = "mentor_swap_200"


def is_raw_video_dir(path: str | Path) -> bool:
    folder = Path(path)
    if (folder / "labels.csv").is_file():
        return True
    return (folder / "real").is_dir() and (folder / "fake").is_dir()


def uses_custom_raw_runner(test_set: str, extra: dict[str, Any] | None = None) -> bool:
    """True for mentor keys, or a local dir that already has labels.csv / real+fake."""
    if str(test_set).startswith(MENTOR_PREFIX):
        return True
    extra = extra or {}
    dataset_dir = extra.get("dataset_dir") or ""
    if not dataset_dir:
        return False
    folder = Path(dataset_dir)
    try:
        if not folder.exists():
            return False
    except OSError:
        return False
    return is_raw_video_dir(folder)


def runner_smoke_limit(test_set: str, *, smoke: bool, cfg: dict[str, Any]) -> int:
    """``--smoke-limit`` slices the concatenated real-then-fake list.

    Prefer a dedicated ``*_smoke`` directory (balanced 8+8) instead of slicing
    the 200+200 set, which would keep only the first N real videos.
    """
    if not smoke:
        return 0
    if "smoke" in str(test_set).lower():
        return 0
    return int(cfg.get("smoke_limit", 16))


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


def apply_smoke_limit(
    videos: list[tuple[Path, int]], smoke_limit: int
) -> list[tuple[Path, int]]:
    if smoke_limit and smoke_limit > 0:
        return videos[:smoke_limit]
    return videos


def write_scores_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video", "label", "score"])
        writer.writeheader()
        writer.writerows(rows)


def print_video_auc(dataset_name: str, labels: list[int], scores: list[float]) -> int:
    if len(set(labels)) < 2 or len(scores) < 2:
        print("not enough scored real/fake videos for AUC", file=sys.stderr)
        return 4
    from src.video_eval.metrics import roc_auc as _auc

    auc = _auc(labels, scores)
    print(f"{dataset_name} AUC (video-level): {auc}")
    return 0


def parse_average_prediction_score(stdout: str) -> float | None:
    for line in reversed(stdout.splitlines()):
        if "average prediction score" not in line.lower():
            continue
        parts = line.replace("=", " ").replace(":", " ").split()
        for token in reversed(parts):
            try:
                return float(token)
            except ValueError:
                continue
    return None
