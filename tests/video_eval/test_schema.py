"""Tests for result schema: mixed tracks are refused."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.video_eval.schema import ResultRecord, append_results, data_missing_record


def _record(track: str, test_set: str = "celebdf_v2") -> ResultRecord:
    return ResultRecord(
        track=track,
        model="lipforensics",
        train_domain="ffpp_c23",
        test_set=test_set,
        compression="c23",
        granularity="video",
        metric="auc",
        value=82.4,
        n_videos=518,
    )


def test_append_same_track(tmp_path: Path) -> None:
    path = append_results(tmp_path, [_record("cross_dataset")])
    assert path.name == "cross_dataset.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload[0]["value"] == 82.4
    assert payload[0]["granularity"] == "video"


def test_refuse_mixed_tracks(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="mixed tracks"):
        append_results(
            tmp_path,
            [_record("cross_dataset"), _record("vlaforge_frame")],
        )


def test_data_missing_has_no_value() -> None:
    rec = data_missing_record(
        track="cross_dataset",
        model="pwtf_dvd",
        train_domain="ffpp_c23",
        test_set="faceshifter",
        compression="c23",
    )
    assert rec.status == "data_missing"
    assert rec.value is None


def test_tfl_data_missing_metric() -> None:
    rec = data_missing_record(
        track="tfl",
        model="auvire",
        train_domain="lav_df",
        test_set="lav_df",
        compression="n/a",
        metric="ap@0.5",
    )
    assert rec.metric == "ap@0.5"
    assert rec.value is None
