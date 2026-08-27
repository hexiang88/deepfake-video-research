"""Parse official eval stdout / score files into ResultRecord rows."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.video_eval.schema import ResultRecord

# Matches LipForensics: "CelebDF AUC (video-level): 0.824"
AUC_RE = re.compile(
    r"(?P<set>Celeb-?DF(?:-v2)?|CDF(?:-v2)?|DFDC(?:P)?|FaceShifter|DeeperForensics|"
    r"DeepFakeDetection|DFD|FF\+\+|Deepfakes|FaceSwap|Face2Face|NeuralTextures)"
    r"[:\s,]+(?:video(?:[- ]level)?\s+)?(?:AUC|AUROC)(?:\s*\([^)]+\))?\s*[:=]\s*(?P<val>\d+(?:\.\d+)?)",
    re.I,
)
BARE_AUC_RE = re.compile(
    r"\b(?:AUC|AUROC)(?:\s*\([^)]+\))?\s*[:=]\s*(?P<val>\d+(?:\.\d+)?)",
    re.I,
)

SET_ALIASES = {
    "celebdf": "celebdf_v2",
    "celeb-df": "celebdf_v2",
    "celeb-df-v2": "celebdf_v2",
    "celebdf-v2": "celebdf_v2",
    "cdf": "celebdf_v2",
    "cdf-v2": "celebdf_v2",
    "dfdc": "dfdc",
    "dfdcp": "dfdc_preview",
    "faceshifter": "faceshifter",
    "deeperforensics": "deeperforensics",
    "dfd": "dfd",
    "deepfakedetection": "dfd",
    "ff++": "ffpp",
    "deepfakes": "Deepfakes",
    "faceswap": "FaceSwap",
    "face2face": "Face2Face",
    "neuraltextures": "NeuralTextures",
}


def normalize_set_name(raw: str) -> str:
    key = raw.lower().replace("_", "-")
    return SET_ALIASES.get(key, raw)


def _to_unit_interval(value: float) -> float:
    """Store AUC on 0-100 scale to match the paper tables in this repo."""
    if value <= 1.0:
        return round(value * 100.0, 4)
    return value


def parse_auc_lines(
    text: str,
    *,
    track: str,
    model: str,
    train_domain: str,
    compression: str,
    granularity: str,
    default_test_set: str | None = None,
    notes: str = "",
    commit: str | None = None,
    gpu: str | None = None,
    metric: str = "auc",
) -> list[ResultRecord]:
    records: list[ResultRecord] = []
    for match in AUC_RE.finditer(text):
        records.append(
            ResultRecord(
                track=track,
                model=model,
                train_domain=train_domain,
                test_set=normalize_set_name(match.group("set")),
                compression=compression,
                granularity=granularity,
                metric=metric,
                value=_to_unit_interval(float(match.group("val"))),
                notes=notes,
                commit=commit,
                gpu=gpu,
            )
        )
    if records:
        return records
    bare = BARE_AUC_RE.search(text)
    if bare and default_test_set:
        return [
            ResultRecord(
                track=track,
                model=model,
                train_domain=train_domain,
                test_set=default_test_set,
                compression=compression,
                granularity=granularity,
                metric=metric,
                value=_to_unit_interval(float(bare.group("val"))),
                notes=notes,
                commit=commit,
                gpu=gpu,
            )
        ]
    return []


def parse_score_csv(
    path: Path,
    *,
    track: str,
    model: str,
    train_domain: str,
    test_set: str,
    compression: str,
    granularity: str,
    notes: str = "",
    commit: str | None = None,
    gpu: str | None = None,
) -> list[ResultRecord]:
    """CSV with header containing score and label columns."""
    import csv

    from src.video_eval.metrics import roc_auc, video_level_auc

    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if not rows:
        return []
    keys = {k.lower(): k for k in rows[0]}
    score_key = keys.get("score") or keys.get("pred") or keys.get("prob")
    label_key = keys.get("label") or keys.get("y")
    video_key = keys.get("video") or keys.get("video_id") or keys.get("id")
    if not score_key or not label_key:
        raise ValueError(f"{path} needs score/label columns, got {list(rows[0])}")
    scores = [float(r[score_key]) for r in rows]
    labels = [int(float(r[label_key])) for r in rows]
    if granularity == "video" and video_key:
        video_ids = [str(r[video_key]) for r in rows]
        label_map = {}
        for vid, lab in zip(video_ids, labels):
            label_map[vid] = lab
        value = video_level_auc(video_ids, scores, label_map) * 100.0
        n_videos = len(label_map)
    else:
        value = roc_auc(labels, scores) * 100.0
        n_videos = len({str(r[video_key]) for r in rows}) if video_key else len(rows)
    return [
        ResultRecord(
            track=track,
            model=model,
            train_domain=train_domain,
            test_set=test_set,
            compression=compression,
            granularity=granularity,
            metric="auc",
            value=value,
            n_videos=n_videos,
            notes=notes,
            commit=commit,
            gpu=gpu,
            extra={"score_file": str(path)},
        )
    ]


def parse_json_metrics(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


MEVER_SET_ALIASES = {
    "lavdf": "lav_df",
    "avdeepfake1m": "av_deepfake1m",
    "fakeavceleb": "fakeavceleb",
    "dfdc": "dfdc",
    "kodf": "kodf",
}

MEVER_DFD_METRICS = {
    "tauc": "auc",
    "tap": "ap",
    "tacc": "acc",
}

_TFL_METRIC_RE = re.compile(r"^t(?P<kind>ap|ar)@(?P<iou>[\d.]+)$", re.I)


def map_mever_set(name: str) -> str:
    key = str(name).strip()
    lower = key.lower()
    if lower in MEVER_SET_ALIASES:
        return MEVER_SET_ALIASES[lower]
    return key


def _mever_metric_value(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 1.0:
        return round(value * 100.0, 4)
    return value


def _iter_mever_cells(payload: dict[str, Any]) -> list[tuple[str, str, dict[str, Any]]]:
    cells: list[tuple[str, str, dict[str, Any]]] = []
    if not isinstance(payload, dict):
        return cells
    for train_key, nested in payload.items():
        if not isinstance(nested, dict):
            continue
        if any(k in nested for k in ("tauc", "tap", "tacc")) or any(
            str(k).lower().startswith("tap@") or str(k).lower().startswith("tar@")
            for k in nested
        ):
            continue
        for test_key, metrics in nested.items():
            if isinstance(metrics, dict):
                cells.append((str(train_key), str(test_key), metrics))
    return cells


def parse_mever_result_json(
    path: Path,
    *,
    track: str,
    model: str,
    compression: str = "n/a",
    granularity: str = "video",
    notes: str = "",
    commit: str | None = None,
    gpu: str | None = None,
    default_train_domain: str | None = None,
) -> list[ResultRecord]:
    """Flatten MEVER nested JSON (train_domain → test_set → tacc/tap/tauc or tap@IoU)."""
    payload = parse_json_metrics(path)
    records: list[ResultRecord] = []
    for train_key, test_key, metrics in _iter_mever_cells(payload):
        train_domain = map_mever_set(train_key)
        if default_train_domain and train_domain == train_key:
            train_domain = default_train_domain
        test_set = map_mever_set(test_key)
        extra = {"source_json": str(path), "raw_train": train_key, "raw_test": test_key}
        if track == "talking_face":
            for raw_name, metric in MEVER_DFD_METRICS.items():
                if raw_name not in metrics:
                    continue
                value = _mever_metric_value(metrics[raw_name])
                if value is None:
                    continue
                records.append(
                    ResultRecord(
                        track=track,
                        model=model,
                        train_domain=train_domain,
                        test_set=test_set,
                        compression=compression,
                        granularity=granularity,
                        metric=metric,
                        value=value,
                        notes=notes,
                        commit=commit,
                        gpu=gpu,
                        extra=extra,
                    )
                )
        elif track == "tfl":
            for raw_name, raw_val in metrics.items():
                match = _TFL_METRIC_RE.match(str(raw_name))
                if not match:
                    continue
                kind = match.group("kind").lower()
                iou = match.group("iou")
                metric = f"{'ap' if kind == 'ap' else 'ar'}@{iou}"
                value = _mever_metric_value(raw_val)
                if value is None:
                    continue
                records.append(
                    ResultRecord(
                        track=track,
                        model=model,
                        train_domain=train_domain,
                        test_set=test_set,
                        compression=compression,
                        granularity=granularity,
                        metric=metric,
                        value=value,
                        notes=notes,
                        commit=commit,
                        gpu=gpu,
                        extra=extra,
                    )
                )
    return records
