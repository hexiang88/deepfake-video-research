"""Result records for video face-swap evaluation tracks."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

Granularity = Literal["frame", "video"]
Track = Literal[
    "cross_dataset",
    "cross_manipulation",
    "vlaforge_frame",
    "indomain",
    "talking_face",
    "tfl",
]

TRACK_FILES: dict[str, str] = {
    "cross_dataset": "cross_dataset.json",
    "cross_manipulation": "cross_manipulation.json",
    "vlaforge_frame": "vlaforge_frame.json",
    "indomain": "indomain.json",
    "talking_face": "talking_face.json",
    "tfl": "tfl.json",
}

MANIPULATION_NOTES = {
    "Face2Face": "候选为 RealForensics；评测对象是 FF++ Face2Face 与 NeuralTextures，不是独立重演检测器。",
    "NeuralTextures": "候选为 RealForensics；评测对象是 FF++ Face2Face 与 NeuralTextures，不是独立重演检测器。",
}

TALKING_FACE_LIPSYNC_NOTE = (
    "候选为 AuViRe / DiMoDif；指标为音视频检测 AUC 与伪造区间 AP，不是唇音偏移毫秒/帧误差。"
)
AUVIRe_NO_FAKEAVCELEB_NOTE = (
    "AuViRe 官方表只绑定 LAV-DF × AV-Deepfake1M，无 FakeAVCeleb 行；本机不编造该行。"
)
DIMODIF_RVFA_NOTE = (
    "跨操纵必须保留 RVFA（真视频假音频）列；论文对照 Table 6 AUC 51.6。"
)


@dataclass
class ResultRecord:
    track: str
    model: str
    train_domain: str
    test_set: str
    compression: str
    granularity: str
    metric: str
    value: float | None
    n_videos: int | None = None
    commit: str | None = None
    gpu: str | None = None
    notes: str = ""
    status: str = "ok"
    extra: dict[str, Any] = field(default_factory=dict)
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return payload


def result_path(results_dir: Path, track: str) -> Path:
    if track not in TRACK_FILES:
        raise ValueError(f"unknown track {track}; refuse to merge tables")
    return results_dir / TRACK_FILES[track]


def append_results(results_dir: Path, records: list[ResultRecord]) -> Path:
    if not records:
        raise ValueError("no records")
    tracks = {r.track for r in records}
    if len(tracks) != 1:
        raise ValueError(f"refuse to write mixed tracks in one file: {tracks}")
    track = records[0].track
    path = result_path(results_dir, track)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict[str, Any]] = []
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(existing, list):
            raise ValueError(f"{path} is not a JSON list")
    existing.extend(r.to_dict() for r in records)
    path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def data_missing_record(
    *,
    track: str,
    model: str,
    train_domain: str,
    test_set: str,
    compression: str,
    granularity: str = "video",
    notes: str = "data_missing",
    metric: str = "auc",
) -> ResultRecord:
    return ResultRecord(
        track=track,
        model=model,
        train_domain=train_domain,
        test_set=test_set,
        compression=compression,
        granularity=granularity,
        metric=metric,
        value=None,
        status="data_missing",
        notes=notes,
    )
