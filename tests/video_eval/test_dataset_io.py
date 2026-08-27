"""Raw-video discovery and score-line helpers (no media, no official repos)."""

from __future__ import annotations

from pathlib import Path

from src.video_eval.dataset_io import (
    apply_smoke_limit,
    discover_labeled_videos,
    parse_average_prediction_score,
    runner_smoke_limit,
    uses_custom_raw_runner,
)


def test_discover_real_fake_dirs(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    (tmp_path / "fake").mkdir()
    (tmp_path / "real" / "a.mp4").write_bytes(b"")
    (tmp_path / "real" / "nested").mkdir()
    (tmp_path / "real" / "nested" / "b.mkv").write_bytes(b"")
    (tmp_path / "fake" / "c.mp4").write_bytes(b"")
    (tmp_path / "ignore.txt").write_text("nope", encoding="utf-8")
    found = discover_labeled_videos(tmp_path)
    labels = {path.name: lab for path, lab in found}
    assert labels["a.mp4"] == 0
    assert labels["b.mkv"] == 0
    assert labels["c.mp4"] == 1
    assert len(found) == 3


def test_discover_labels_csv(tmp_path: Path) -> None:
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"")
    (tmp_path / "labels.csv").write_text(
        "path,label\nclip.mp4,1\n", encoding="utf-8"
    )
    found = discover_labeled_videos(tmp_path)
    assert len(found) == 1
    assert found[0][0] == video
    assert found[0][1] == 1


def test_smoke_limit_slices_real_then_fake(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    (tmp_path / "fake").mkdir()
    for i in range(3):
        (tmp_path / "real" / f"r{i}.mp4").write_bytes(b"")
        (tmp_path / "fake" / f"f{i}.mp4").write_bytes(b"")
    videos = discover_labeled_videos(tmp_path)
    sliced = apply_smoke_limit(videos, 2)
    assert [lab for _, lab in sliced] == [0, 0]


def test_uses_custom_raw_runner_mentor_key() -> None:
    assert uses_custom_raw_runner("mentor_swap_200_smoke", extra={})
    assert uses_custom_raw_runner("mentor_swap_200", extra={})
    assert not uses_custom_raw_runner("celebdf_v2", extra={})


def test_runner_smoke_limit_skips_named_smoke_set() -> None:
    cfg = {"smoke_limit": 16}
    assert runner_smoke_limit("mentor_swap_200_smoke", smoke=True, cfg=cfg) == 0
    assert runner_smoke_limit("mentor_swap_200", smoke=True, cfg=cfg) == 16
    assert runner_smoke_limit("mentor_swap_200", smoke=False, cfg=cfg) == 0


def test_parse_average_prediction_score() -> None:
    text = "noise\nAverage prediction score: 0.4321\n"
    assert parse_average_prediction_score(text) == 0.4321
    assert parse_average_prediction_score("no score here") is None
