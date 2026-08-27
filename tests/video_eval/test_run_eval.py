"""run_eval dry-run does not merge tracks or require GPU data."""

from __future__ import annotations

from pathlib import Path

from src.video_eval.run_eval import main, plan_jobs


def test_dry_run_missing_data(tmp_path: Path, capsys) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"datasets": {"celebdf_v2": {"path": "/no/such/celebdf"}}}',
        encoding="utf-8",
    )
    config = tmp_path / "video_eval.yaml"
    config.write_text(
        "\n".join(
            [
                f'manifest: "{manifest.as_posix()}"',
                f'results_dir: "{(tmp_path / "results").as_posix()}"',
                "default_compression: c23",
                "train_domain: ffpp_c23",
                "models:",
                "  lipforensics:",
                '    repo_dir: "/tmp/LipForensics"',
                '    weights_dir: "/tmp/weights"',
                "    python: python",
                "    tracks: [cross_dataset]",
                "    test_sets: [celebdf_v2]",
            ]
        ),
        encoding="utf-8",
    )
    code = main(
        [
            "--config",
            str(config),
            "--track",
            "cross_dataset",
            "--model",
            "lipforensics",
            "--dry-run",
        ]
    )
    assert code == 0
    err = capsys.readouterr().err
    assert "data_missing" in err
    assert not list((tmp_path / "results").glob("*.json"))


def test_dry_run_mentor_lipforensics_not_celebdf(tmp_path: Path, capsys) -> None:
    data = tmp_path / "mentor_swap_200_smoke"
    (data / "real").mkdir(parents=True)
    (data / "fake").mkdir()
    (data / "real" / "a.mp4").write_bytes(b"")
    (data / "fake" / "b.mp4").write_bytes(b"")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        '{"datasets": {"mentor_swap_200_smoke": {"path": "%s"}}}'
        % data.as_posix(),
        encoding="utf-8",
    )
    config = tmp_path / "video_eval.yaml"
    config.write_text(
        "\n".join(
            [
                f'manifest: "{manifest.as_posix()}"',
                f'results_dir: "{(tmp_path / "results").as_posix()}"',
                "default_compression: c23",
                "train_domain: ffpp_c23",
                "gpu: cuda:0",
                "models:",
                "  lipforensics:",
                '    repo_dir: "/tmp/LipForensics"',
                '    weights_dir: "/tmp/weights"',
                '    weights_file: "/tmp/weights/lipforensics_ff.pth"',
                "    python: python",
                "    tracks: [cross_dataset]",
                "    test_sets: [mentor_swap_200_smoke]",
            ]
        ),
        encoding="utf-8",
    )
    code = main(
        [
            "--config",
            str(config),
            "--track",
            "cross_dataset",
            "--model",
            "lipforensics",
            "--dry-run",
        ]
    )
    assert code == 0
    err = capsys.readouterr().err
    assert "lipforensics_dataset_eval.py" in err
    assert "CelebDF" not in err
    assert "evaluate.py" not in err


def test_plan_jobs_disables_eval_once_for_mentor() -> None:
    jobs = plan_jobs(
        {},
        {
            "eval_once": True,
            "test_sets": ["mentor_swap_200_smoke", "mentor_swap_200"],
        },
        track="cross_dataset",
        manifest={"datasets": {}},
        smoke=False,
    )
    assert len(jobs) == 2
    assert jobs[0]["test_set"] == "mentor_swap_200_smoke"
    assert not jobs[0].get("eval_once")
    assert jobs[1]["test_set"] == "mentor_swap_200"
