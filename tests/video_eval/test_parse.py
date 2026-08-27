"""Stdout / CSV parsers for official eval logs."""

from __future__ import annotations

from pathlib import Path

from src.video_eval.parse import parse_auc_lines, parse_score_csv


def test_lipforensics_video_level_line() -> None:
    text = "CelebDF AUC (video-level): 0.824"
    records = parse_auc_lines(
        text,
        track="cross_dataset",
        model="lipforensics",
        train_domain="ffpp_c23",
        compression="c23",
        granularity="video",
    )
    assert len(records) == 1
    assert records[0].test_set == "celebdf_v2"
    assert records[0].value == 82.4
    assert records[0].metric == "auc"


def test_bare_auc_uses_default_set() -> None:
    text = "AUC (video-level): 0.735"
    records = parse_auc_lines(
        text,
        track="cross_dataset",
        model="lipforensics",
        train_domain="ffpp_c23",
        compression="c23",
        granularity="video",
        default_test_set="dfdc",
    )
    assert records[0].test_set == "dfdc"
    assert records[0].value == 73.5


def test_percent_not_rescaled() -> None:
    text = "FaceShifter AUC: 97.1"
    records = parse_auc_lines(
        text,
        track="cross_dataset",
        model="lipforensics",
        train_domain="ffpp_c23",
        compression="c23",
        granularity="video",
    )
    assert records[0].value == 97.1


def test_mentor_auc_line_keeps_set_name() -> None:
    text = "mentor_swap_200 AUC (video-level): 0.82"
    records = parse_auc_lines(
        text,
        track="cross_dataset",
        model="lipforensics",
        train_domain="ffpp_c23",
        compression="c23",
        granularity="video",
        default_test_set="mentor_swap_200",
    )
    assert len(records) == 1
    assert records[0].test_set == "mentor_swap_200"
    assert records[0].value == 82.0


def test_score_csv_video_level(tmp_path: Path) -> None:
    path = tmp_path / "scores.csv"
    path.write_text(
        "video,label,score\n"
        "v1,0,0.1\n"
        "v1,0,0.3\n"
        "v2,1,0.8\n"
        "v2,1,0.9\n",
        encoding="utf-8",
    )
    records = parse_score_csv(
        path,
        track="cross_dataset",
        model="pwtf_dvd",
        train_domain="ffpp_c23",
        test_set="celebdf_v2",
        compression="c23",
        granularity="video",
    )
    assert records[0].n_videos == 2
    assert records[0].value == 100.0
