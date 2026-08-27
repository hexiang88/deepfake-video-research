"""Talking Face / TFL adapters parse official MEVER JSON (no media)."""

from __future__ import annotations

import json
from pathlib import Path

from src.video_eval.adapters import get_adapter
from src.video_eval.parse import parse_mever_result_json
from src.video_eval.run_eval import main
from src.video_eval.schema import TRACK_FILES, append_results, ResultRecord


CFG = {
    "default_compression": "c23",
    "train_domain": "ffpp_c23",
    "gpu": "cuda:0",
}


def _model(name: str) -> dict:
    return {
        "repo_dir": f"/data/models/{name}",
        "weights_dir": f"/data/weights/{name}",
        "python": "/home/USER/miniconda3/envs/auvire/bin/python",
    }


def test_auvire_official_test_py() -> None:
    cmd = get_adapter("auvire").build_command(
        CFG,
        _model("AuViRe"),
        track="tfl",
        test_set="lav_df",
        smoke=False,
    )
    joined = " ".join(cmd)
    assert "scripts/test.py" in joined
    assert cmd[0].endswith("python")
    assert "FakeAVCeleb" not in joined
    assert "cuda:1" not in joined


def test_dimodif_official_eval_py() -> None:
    cmd = get_adapter("dimodif").build_command(
        CFG,
        {**_model("DiMoDif"), "python": "/home/USER/miniconda3/envs/dimodif/bin/python"},
        track="talking_face",
        test_set="fakeavceleb",
        smoke=False,
    )
    joined = " ".join(cmd)
    assert "scripts/eval.py" in joined
    assert "dimodif/bin/python" in joined


def test_parse_auvire_dfd_json(tmp_path: Path) -> None:
    path = tmp_path / "task_dfd_training_on_lavdf.json"
    path.write_text(
        json.dumps(
            {
                "lavdf": {
                    "lavdf": {"tacc": 73.5429, "tap": 99.9815, "tauc": 99.9398},
                    "avdeepfake1m": {"tacc": 74.9663, "tap": 86.8499, "tauc": 65.7084},
                }
            }
        ),
        encoding="utf-8",
    )
    records = parse_mever_result_json(
        path, track="talking_face", model="auvire", notes="n"
    )
    auc = [r for r in records if r.metric == "auc"]
    assert {(r.train_domain, r.test_set, r.value) for r in auc} == {
        ("lav_df", "lav_df", 99.9398),
        ("lav_df", "av_deepfake1m", 65.7084),
    }


def test_parse_dimodif_keeps_rvfa(tmp_path: Path) -> None:
    path = tmp_path / "dfd_fakeavceleb.json"
    path.write_text(
        json.dumps(
            {
                "fakeavceleb": {
                    "fakeavceleb": {"tacc": 99.4, "tap": 99.99, "tauc": 99.7},
                    "fakeavceleb-wo-rvfa": {"tacc": 50.0, "tap": 51.0, "tauc": 51.6},
                }
            }
        ),
        encoding="utf-8",
    )
    records = parse_mever_result_json(
        path, track="talking_face", model="dimodif"
    )
    rvfa = [
        r
        for r in records
        if r.test_set == "fakeavceleb-wo-rvfa" and r.metric == "auc"
    ]
    assert len(rvfa) == 1
    assert rvfa[0].value == 51.6
    assert rvfa[0].train_domain == "fakeavceleb"


def test_parse_tfl_ap_at_iou(tmp_path: Path) -> None:
    path = tmp_path / "task_tfl.json"
    path.write_text(
        json.dumps(
            {
                "lavdf": {
                    "lavdf": {
                        "tap@0.5": 95.5,
                        "tap@0.75": 87.9,
                        "tap@0.95": 20.6,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    records = parse_mever_result_json(path, track="tfl", model="auvire")
    by_metric = {r.metric: r.value for r in records}
    assert by_metric["ap@0.5"] == 95.5
    assert by_metric["ap@0.75"] == 87.9
    assert by_metric["ap@0.95"] == 20.6


def test_talking_face_track_file(tmp_path: Path) -> None:
    rec = ResultRecord(
        track="talking_face",
        model="auvire",
        train_domain="lav_df",
        test_set="lav_df",
        compression="n/a",
        granularity="video",
        metric="auc",
        value=None,
        status="data_missing",
    )
    path = append_results(tmp_path, [rec])
    assert path.name == TRACK_FILES["talking_face"] == "talking_face.json"


def test_tfl_missing_writes_json_not_cross_dataset(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "datasets": {
                    "lav_df": {"path": "/no/lavdf"},
                    "av_deepfake1m": {"path": "/no/avd1m"},
                }
            }
        ),
        encoding="utf-8",
    )
    config = tmp_path / "video_eval.yaml"
    results = tmp_path / "results"
    config.write_text(
        "\n".join(
            [
                f'manifest: "{manifest.as_posix()}"',
                f'results_dir: "{results.as_posix()}"',
                "default_compression: c23",
                "train_domain: ffpp_c23",
                "gpu: cuda:0",
                "models:",
                "  auvire:",
                '    repo_dir: "/tmp/AuViRe"',
                '    weights_dir: "/tmp/weights/auvire"',
                "    python: python",
                "    tracks: [talking_face, tfl]",
                "    test_sets: [lav_df, av_deepfake1m]",
                "    eval_once: true",
                "    require_all_datasets: true",
                "    train_domain: lav_df",
                "    compression: n/a",
            ]
        ),
        encoding="utf-8",
    )
    code = main(
        [
            "--config",
            str(config),
            "--track",
            "tfl",
            "--model",
            "auvire",
        ]
    )
    assert code == 0
    assert not (results / "cross_dataset.json").exists()
    payload = json.loads((results / "tfl.json").read_text(encoding="utf-8"))
    assert payload
    assert all(row["status"] == "data_missing" for row in payload)
    assert all(row["metric"] == "ap@0.5" for row in payload)
    assert all(row["value"] is None for row in payload)
