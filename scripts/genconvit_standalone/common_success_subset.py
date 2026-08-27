#!/usr/bin/env python3
"""Create a supplemental common-success-ID appendix without ranking models."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Sequence

from genconvit_dataset_eval import average_precision, roc_auc


class SubsetError(RuntimeError):
    pass


def canonical_video_id(raw: str, label: int) -> str:
    normalized = raw.strip().replace("\\", "/").rstrip("/")
    parts = [part for part in normalized.split("/") if part]
    class_name = "fake" if label == 1 else "real"
    class_positions = [i for i, part in enumerate(parts) if part.lower() in {"real", "fake"}]
    if class_positions:
        index = class_positions[-1]
        declared = parts[index].lower()
        if declared != class_name:
            raise SubsetError(
                f"path class {declared!r} conflicts with label {label}: {raw!r}"
            )
        return "/".join([class_name, *parts[index + 1 :]])
    if not parts:
        raise SubsetError("empty video identifier")
    return f"{class_name}/{parts[-1]}"


def read_model_scores(path: Path) -> dict[str, tuple[int, float, str]]:
    if not path.is_file():
        raise SubsetError(f"scores file missing: {path}")
    result: dict[str, tuple[int, float, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise SubsetError(f"scores file has no header: {path}")
        id_column = next(
            (name for name in ("video", "video_id", "path") if name in reader.fieldnames),
            None,
        )
        if (
            id_column is None
            or "label" not in reader.fieldnames
            or "score" not in reader.fieldnames
        ):
            raise SubsetError(
                f"{path} must contain video/video_id/path, label, and score columns"
            )
        for row_number, row in enumerate(reader, start=2):
            try:
                label_value = float(row["label"])
                if not math.isfinite(label_value) or not label_value.is_integer():
                    raise ValueError(f"label must be exactly 0 or 1, got {row['label']!r}")
                label = int(label_value)
                score = float(row["score"])
                canonical = canonical_video_id(row[id_column], label)
            except (TypeError, ValueError, SubsetError) as exc:
                raise SubsetError(f"{path}:{row_number}: {exc}") from exc
            if label not in (0, 1) or not math.isfinite(score):
                raise SubsetError(f"{path}:{row_number}: invalid label or non-finite score")
            if canonical in result:
                raise SubsetError(f"duplicate canonical ID in {path}: {canonical}")
            result[canonical] = (label, score, row[id_column])
    if not result:
        raise SubsetError(f"no score rows found: {path}")
    return result


def parse_named_score(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("use MODEL=/absolute/path/to/scores.csv")
    name, raw_path = value.split("=", 1)
    name = name.strip()
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    if not name or any(character not in allowed for character in name):
        raise argparse.ArgumentTypeError(f"invalid model name: {name!r}")
    return name, Path(raw_path).expanduser()


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a four-model common-success-ID supplemental appendix."
    )
    parser.add_argument(
        "--scores",
        action="append",
        type=parse_named_score,
        required=True,
        metavar="MODEL=CSV",
    )
    parser.add_argument("--out-dir", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if len(args.scores) < 2:
        print("ERROR: provide at least two --scores inputs", file=sys.stderr)
        return 2
    names = [name for name, _ in args.scores]
    if len(names) != len(set(names)):
        print("ERROR: duplicate model names", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir).expanduser().resolve()
    if out_dir.exists():
        print(f"ERROR: output directory already exists: {out_dir}", file=sys.stderr)
        return 2

    try:
        tables = {
            name: read_model_scores(path.expanduser().resolve())
            for name, path in args.scores
        }
        common_ids = set.intersection(*(set(table) for table in tables.values()))
        if not common_ids:
            raise SubsetError("the supplied score files have no common canonical IDs")
        ordered_ids = sorted(common_ids)
        for video_id in ordered_ids:
            labels = {tables[name][video_id][0] for name in names}
            if len(labels) != 1:
                raise SubsetError(f"conflicting labels across models for {video_id}")
        if len({tables[names[0]][video_id][0] for video_id in ordered_ids}) != 2:
            raise SubsetError("the common subset must contain both real and fake videos")
    except (OSError, ValueError, SubsetError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir()
    (out_dir / "common_ids.txt").write_text(
        "\n".join(ordered_ids) + "\n", encoding="utf-8"
    )

    metrics: dict[str, dict[str, float | int]] = {}
    for name in names:
        rows = [tables[name][video_id] for video_id in ordered_ids]
        labels = [row[0] for row in rows]
        scores = [row[1] for row in rows]
        metrics[name] = {
            "n_videos": len(rows),
            "n_real": sum(label == 0 for label in labels),
            "n_fake": sum(label == 1 for label in labels),
            "auc_pct": 100.0 * roc_auc(labels, scores),
            "ap_pct": 100.0 * average_precision(labels, scores),
        }
        with (out_dir / f"{name}_common_scores.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=["video", "label", "score"])
            writer.writeheader()
            for video_id, (label, score, _) in zip(ordered_ids, rows):
                writer.writerow(
                    {"video": video_id, "label": label, "score": format(score, ".17g")}
                )

    payload = {
        "status": "supplemental_common_success_subset",
        "ranking_permitted": False,
        "note": (
            "Fairness appendix only. Preserve every model's native successful-set "
            "result; this common subset cannot replace the main result or form a leaderboard."
        ),
        "models": names,
        "common_n_videos": len(ordered_ids),
        "metrics": metrics,
    }
    (out_dir / "common_success_metrics.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"WROTE supplemental common subset: n={len(ordered_ids)} -> {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
