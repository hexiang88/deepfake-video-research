"""Adapter command construction (no official repos required)."""

from __future__ import annotations

from src.video_eval.adapters import get_adapter

CFG = {
    "default_compression": "c23",
    "train_domain": "ffpp_c23",
    "smoke_limit": 16,
    "results_dir": "results",
}


def _model(name: str) -> dict:
    return {
        "repo_dir": f"/data/models/{name}",
        "weights_dir": f"/data/weights/{name}",
        "python": "python",
    }


def test_lipforensics_official_flags() -> None:
    cmd = get_adapter("lipforensics").build_command(
        CFG,
        {**_model("lipforensics"), "weights_file": "/w/lipforensics_ff.pth"},
        track="cross_dataset",
        test_set="celebdf_v2",
        smoke=False,
    )
    assert cmd[:2] == ["python", "evaluate.py"]
    assert "--dataset" in cmd and "CelebDF" in cmd
    assert "--weights_forgery" in cmd
    assert "--compression" in cmd and "c23" in cmd


def test_realforensics_leave_one_out_weight() -> None:
    cmd = get_adapter("realforensics").build_command(
        CFG,
        _model("realforensics"),
        track="cross_manipulation",
        test_set="Face2Face",
        smoke=False,
        extra={"manipulation": "Face2Face"},
    )
    joined = " ".join(cmd)
    assert "stage2/eval.py" in joined
    assert "realforensics_allbutf2f.pth" in joined


def test_realforensics_f2f_note() -> None:
    records = get_adapter("realforensics").parse(
        "Face2Face AUC (video-level): 0.997",
        cfg=CFG,
        model_cfg=_model("realforensics"),
        track="cross_manipulation",
        test_set="Face2Face",
        extra={"manipulation": "Face2Face"},
    )
    assert records[0].value == 99.7
    assert "不是独立重演检测器" in records[0].notes


def test_vlaforge_video_note() -> None:
    records = get_adapter("vlaforge").parse(
        "Celeb-DF-v2 AUC: 0.91",
        cfg=CFG,
        model_cfg=_model("vlaforge"),
        track="cross_dataset",
        test_set="celebdf_v2",
        extra={"granularity": "video"},
    )
    assert records[0].notes.startswith("视频级分数为帧级平均")
    assert records[0].granularity == "video"


def test_pwtf_uses_dataset_runner() -> None:
    cmd = get_adapter("pwtf_dvd").build_command(
        CFG,
        _model("pwtf_dvd"),
        track="cross_dataset",
        test_set="dfd",
        smoke=True,
        extra={"dataset_dir": "/data/datasets/DFD", "output_dir": "results/tmp"},
    )
    joined = " ".join(cmd)
    assert "pwtf_dvd_dataset_eval.py" in joined
    assert "--smoke-limit" in joined


def test_lipforensics_mentor_uses_raw_runner() -> None:
    cmd = get_adapter("lipforensics").build_command(
        CFG,
        {**_model("lipforensics"), "weights_file": "/w/lipforensics_ff.pth"},
        track="cross_dataset",
        test_set="mentor_swap_200_smoke",
        smoke=True,
        extra={"dataset_dir": "/data/mentor_swap_200_smoke", "output_dir": "results/tmp"},
    )
    joined = " ".join(cmd)
    assert "lipforensics_dataset_eval.py" in joined
    assert "CelebDF" not in joined
    assert "evaluate.py" not in joined
    assert "--dataset-name" in cmd and "mentor_swap_200_smoke" in cmd
    # Dedicated smoke dir: do not slice real-then-fake again.
    assert cmd[cmd.index("--smoke-limit") + 1] == "0"


def test_lipforensics_mentor_stdout_keeps_set_name() -> None:
    records = get_adapter("lipforensics").parse(
        "mentor_swap_200_smoke AUC (video-level): 0.91",
        cfg=CFG,
        model_cfg=_model("lipforensics"),
        track="cross_dataset",
        test_set="mentor_swap_200_smoke",
    )
    assert records[0].test_set == "mentor_swap_200_smoke"
    assert records[0].value == 91.0
    assert "Celeb" not in records[0].test_set


def test_realforensics_mentor_stdout_keeps_set_name() -> None:
    records = get_adapter("realforensics").parse(
        "mentor_swap_200 AUC (video-level): 0.77",
        cfg=CFG,
        model_cfg=_model("realforensics"),
        track="cross_dataset",
        test_set="mentor_swap_200",
    )
    assert records[0].test_set == "mentor_swap_200"
    assert records[0].value == 77.0


def test_realforensics_mentor_uses_raw_runner() -> None:
    cmd = get_adapter("realforensics").build_command(
        CFG,
        {**_model("realforensics"), "weights_file": "realforensics_ff.pth"},
        track="cross_dataset",
        test_set="mentor_swap_200",
        smoke=False,
        extra={"dataset_dir": "/data/mentor_swap_200", "output_dir": "results/tmp"},
    )
    joined = " ".join(cmd)
    assert "realforensics_dataset_eval.py" in joined
    assert "stage2/eval.py" not in joined
    assert "mentor_swap_200" in joined
    assert "CelebDF" not in joined
