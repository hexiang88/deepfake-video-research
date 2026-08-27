from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest
import numpy as np

PACKAGE_DIR = Path(__file__).resolve().parents[1]
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from common_success_subset import (  # noqa: E402
    SubsetError,
    canonical_video_id,
    main as common_subset_main,
)
from genconvit_dataset_eval import (  # noqa: E402
    FailureRecord,
    ED_SHA256,
    HF_REVISION,
    OFFICIAL_COMMIT,
    ScoreRecord,
    VAE_SHA256,
    VideoItem,
    average_precision,
    build_coverage,
    compute_metrics_pct,
    discover_videos,
    equal_error_rate,
    official_fake_score,
    per_video_seed,
    is_out_of_memory_error,
    roc_auc,
    stratified_bootstrap_ci,
    write_dataset_manifest,
    write_outputs,
)
from verify_genconvit_result import (  # noqa: E402
    VerificationError,
    compare_repeat_context,
    validate_run,
)


def assert_metric(actual: float, expected: float) -> None:
    assert math.isclose(actual, expected, rel_tol=0.0, abs_tol=1e-8)


def test_perfect_separation_metrics_and_ci() -> None:
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.4, 0.6, 0.9]

    metrics, confusion = compute_metrics_pct(labels, scores)

    assert confusion == {"tp": 2, "tn": 2, "fp": 0, "fn": 0}
    for name, value in metrics.items():
        assert_metric(value, 0.0 if name == "eer" else 100.0)

    ci, valid = stratified_bootstrap_ci(
        labels, scores, n_resamples=100, seed=20260818
    )
    assert valid == 100
    for name, interval in ci.items():
        expected = [0.0, 0.0] if name == "eer" else [100.0, 100.0]
        assert interval == expected


def test_nonperfect_hand_computed_vector() -> None:
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.8, 0.4, 0.9]

    metrics, confusion = compute_metrics_pct(labels, scores)

    assert confusion == {"tp": 1, "tn": 1, "fp": 1, "fn": 1}
    assert_metric(metrics["auc"], 75.0)
    assert_metric(metrics["ap"], 83.33333333333333)
    assert_metric(metrics["accuracy_at_0_5"], 50.0)
    assert_metric(metrics["macro_f1_at_0_5"], 50.0)
    assert_metric(metrics["precision_fake_at_0_5"], 50.0)
    assert_metric(metrics["recall_fake_at_0_5"], 50.0)
    assert_metric(metrics["eer"], 50.0)


def test_tied_scores_and_threshold_are_order_independent() -> None:
    labels = [0, 1]
    scores = [0.5, 0.5]

    metrics, confusion = compute_metrics_pct(labels, scores)

    assert confusion == {"tp": 1, "tn": 0, "fp": 1, "fn": 0}
    assert_metric(metrics["auc"], 50.0)
    assert_metric(metrics["ap"], 50.0)
    assert_metric(metrics["accuracy_at_0_5"], 50.0)
    assert_metric(metrics["macro_f1_at_0_5"], 33.33333333333333)
    assert_metric(metrics["precision_fake_at_0_5"], 50.0)
    assert_metric(metrics["recall_fake_at_0_5"], 100.0)
    assert_metric(metrics["eer"], 50.0)
    assert_metric(roc_auc(list(reversed(labels)), scores), 0.5)
    assert_metric(average_precision(list(reversed(labels)), scores), 0.5)


class _FakeTensor:
    def __init__(self, values: object):
        self.values = np.asarray(values, dtype=float)

    @property
    def ndim(self) -> int:
        return self.values.ndim

    @property
    def shape(self) -> tuple[int, ...]:
        return self.values.shape

    def float(self) -> "_FakeTensor":
        return self

    def mean(self, dim: int) -> "_FakeTensor":
        return _FakeTensor(self.values.mean(axis=dim))

    def __getitem__(self, index: int) -> "_FakeTensor":
        return _FakeTensor(self.values[index])

    def item(self) -> float:
        return float(self.values.item())


class _FakeTorch:
    @staticmethod
    def sigmoid(tensor: _FakeTensor) -> _FakeTensor:
        return _FakeTensor(1.0 / (1.0 + np.exp(-tensor.values)))

    @staticmethod
    def isfinite(tensor: _FakeTensor) -> np.ndarray:
        return np.isfinite(tensor.values)


def test_official_fake_score_direction_for_ed_vae_rows() -> None:
    fake_wins = _FakeTensor([[2.0, -1.0], [1.0, 0.0]])
    fake_score, fake_pred, fake_means = official_fake_score(_FakeTorch, fake_wins)
    assert fake_pred == 1
    assert_metric(fake_score, fake_means[0])

    real_wins = _FakeTensor([[-1.0, 2.0], [0.0, 1.0]])
    real_score, real_pred, real_means = official_fake_score(_FakeTorch, real_wins)
    assert real_pred == 0
    assert_metric(real_score, 1.0 - real_means[1])


def test_oom_detection_covers_pytorch_and_dlib_cuda_messages() -> None:
    class TorchOOM(RuntimeError):
        pass

    class FakeCuda:
        OutOfMemoryError = TorchOOM

    class FakeTorch:
        OutOfMemoryError = TorchOOM
        cuda = FakeCuda()

    assert is_out_of_memory_error(FakeTorch, TorchOOM("allocation failed"))
    assert is_out_of_memory_error(
        FakeTorch, RuntimeError("cudaErrorMemoryAllocation while detecting faces")
    )
    assert not is_out_of_memory_error(FakeTorch, RuntimeError("bad frame"))


@pytest.mark.parametrize("bad_score", [float("nan"), float("inf"), -0.01, 1.01])
def test_invalid_scores_are_rejected(bad_score: float) -> None:
    with pytest.raises(ValueError):
        compute_metrics_pct([0, 1], [0.1, bad_score])


def test_ranking_metrics_accept_finite_logits_for_legacy_common_subset() -> None:
    labels = [0, 0, 1, 1]
    logits = [-4.0, -1.0, 1.0, 7.0]
    assert_metric(roc_auc(labels, logits), 1.0)
    assert_metric(average_precision(labels, logits), 1.0)


def test_single_class_is_rejected_and_has_no_ci() -> None:
    with pytest.raises(ValueError):
        compute_metrics_pct([0, 0], [0.1, 0.2])
    ci, valid = stratified_bootstrap_ci(
        [0, 0], [0.1, 0.2], n_resamples=10, seed=1
    )
    assert valid == 0
    assert all(interval is None for interval in ci.values())


def test_ci_is_deterministic() -> None:
    labels = [0, 0, 0, 1, 1, 1]
    scores = [0.1, 0.5, 0.8, 0.2, 0.7, 0.9]
    first, first_valid = stratified_bootstrap_ci(
        labels, scores, n_resamples=50, seed=20260818
    )
    second, second_valid = stratified_bootstrap_ci(
        labels, scores, n_resamples=50, seed=20260818
    )
    assert first_valid == second_valid == 50
    assert first == second


def test_eer_extremes() -> None:
    assert_metric(equal_error_rate([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]), 0.0)
    assert_metric(equal_error_rate([0, 0, 1, 1], [0.8, 0.9, 0.1, 0.2]), 1.0)


def test_discovery_is_sorted_and_manifest_is_stable(tmp_path: Path) -> None:
    for class_name in ("real", "fake"):
        (tmp_path / class_name).mkdir()
    (tmp_path / "real" / "b.mp4").write_bytes(b"real-b")
    (tmp_path / "real" / "a.mp4").write_bytes(b"real-a")
    (tmp_path / "fake" / "z.mp4").write_bytes(b"fake-z")
    (tmp_path / "fake" / "y.mkv").write_bytes(b"fake-y")
    (tmp_path / "fake" / "x.webm").write_bytes(b"fake-x")

    first, first_hash = discover_videos(
        tmp_path, expected_real=2, expected_fake=3, hash_videos=True
    )
    second, second_hash = discover_videos(
        tmp_path, expected_real=2, expected_fake=3, hash_videos=True
    )

    assert [item.video_id for item in first] == [
        "real/a.mp4",
        "real/b.mp4",
        "fake/x.webm",
        "fake/y.mkv",
        "fake/z.mp4",
    ]
    assert first == second
    assert first_hash == second_hash
    assert all(item.sha256 for item in first)


def test_failed_video_is_preserved_without_imputed_score(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output = tmp_path / "output"
    source.mkdir()
    output.mkdir()
    real_path = source / "real.mp4"
    fake_path = source / "fake.mp4"
    real_path.write_bytes(b"real")
    fake_path.write_bytes(b"fake")
    items = [
        VideoItem(real_path, "real/real.mp4", 0, 4),
        VideoItem(fake_path, "fake/fake.mp4", 1, 4),
    ]
    scores = [ScoreRecord("real/real.mp4", 0, 0.1, 0, 0, 15, 15, 123)]
    failures = [
        FailureRecord("fake/fake.mp4", 1, "decode", "decode_error", "bad", 0, 0)
    ]

    write_outputs(output, items, scores, failures)
    coverage = build_coverage(items, scores, failures)

    predictions = (output / "predictions.csv").read_text(encoding="utf-8")
    score_lines = (output / "scores.csv").read_text(encoding="utf-8").splitlines()
    assert coverage["n_requested"] == 2
    assert coverage["n_scored"] == 1
    assert coverage["n_fake_failed"] == 1
    assert len(score_lines) == 2  # header + one successful real video
    assert "fake/fake.mp4,1,failed,," in predictions


def test_verifier_cross_checks_artifact_ids_and_labels(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    (dataset / "real").mkdir(parents=True)
    (dataset / "fake").mkdir()
    (dataset / "real" / "a.mp4").write_bytes(b"real")
    (dataset / "fake" / "b.mp4").write_bytes(b"fake")
    items, manifest_sha256 = discover_videos(
        dataset, expected_real=1, expected_fake=1, hash_videos=True
    )

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    scores = [
        ScoreRecord("real/a.mp4", 0, 0.1, 0, 0, 15, 15, 1),
        ScoreRecord("fake/b.mp4", 1, 0.9, 1, 1, 15, 15, 2),
    ]
    write_dataset_manifest(run_dir / "dataset_manifest.csv", items)
    write_outputs(run_dir, items, scores, [])
    (run_dir / "eval.log").write_text("ok\n", encoding="utf-8")
    (run_dir / "progress.jsonl").write_text("{}\n{}\n", encoding="utf-8")
    metrics, confusion = compute_metrics_pct([0, 1], [0.1, 0.9])
    summary = {
        "run": {"status": "ok", "evidence_role": "custom_evaluation"},
        "evaluation_label": (
            "mentor_swap_200 custom evaluation / OOD status unverified"
        ),
        "dataset": {
            "manifest_sha256": manifest_sha256,
            "content_sha256_included": True,
        },
        "model": {
            "official_repository": {
                "commit": OFFICIAL_COMMIT,
                "dirty": False,
                "post_run_dirty": False,
            },
            "weights_revision": HF_REVISION,
            "ed_weights": {"sha256": ED_SHA256},
            "vae_weights": {"sha256": VAE_SHA256},
            "strict_load": True,
        },
        "coverage": build_coverage(items, scores, []),
        "confusion_matrix_at_0_5": confusion,
        "metrics": {
            name: {"value_pct": value} for name, value in metrics.items()
        },
    }
    (run_dir / "summary.json").write_text(
        json.dumps(summary), encoding="utf-8"
    )

    validate_run(
        run_dir,
        expected_real=1,
        expected_fake=1,
        allow_pipeline_smoke=False,
    )

    (run_dir / "scores.csv").write_text(
        "video,label,score\nreal/a.mp4,0,0.1\nfake/not-b.mp4,1,0.9\n",
        encoding="utf-8",
    )
    with pytest.raises(VerificationError, match="scores.csv IDs"):
        validate_run(
            run_dir,
            expected_real=1,
            expected_fake=1,
            allow_pipeline_smoke=False,
        )


def test_per_video_seed_is_stable_and_order_independent() -> None:
    assert per_video_seed(20260818, "real/a.mp4") == per_video_seed(
        20260818, "real/a.mp4"
    )
    assert per_video_seed(20260818, "real/a.mp4") != per_video_seed(
        20260818, "fake/a.mp4"
    )


def _repeat_summary() -> dict[str, object]:
    return {
        "dataset": {
            "name": "mentor_swap_200_smoke",
            "path": "/data/mentor_swap_200_smoke",
            "manifest_sha256": "abc",
            "content_sha256_included": True,
        },
        "run": {"evidence_role": "pipeline_smoke_only"},
        "model": {"state_dict_key_counts": {"ed": 10, "vae": 20}},
        "inference": {
            "frames_requested_per_video": 15,
            "seed": 20260818,
            "precision": "fp32",
            "runtime": {
                "python": "3.10",
                "platform": "linux",
                "packages": {"torch": "2.1.2"},
                "cuda_visible_devices": "2",
                "genconvit_gpu": "2",
                "torch_cuda_version": "11.8",
                "cudnn_version": 8700,
                "visible_gpu_count": 1,
                "visible_gpu_name": "GPU",
                "visible_gpu_uuid": "GPU-123",
                "nvidia_smi": "2, GPU-123, GPU, 555.55",
                "dlib_use_cuda": False,
                "dlib_face_detector_mode": "hog",
                "deterministic_algorithms": True,
                "cublas_workspace_config": ":4096:8",
                "precision": "fp32",
            },
        },
    }


def test_repeat_context_requires_same_input_seed_gpu_and_environment() -> None:
    first = _repeat_summary()
    repeat = _repeat_summary()
    compare_repeat_context(first, repeat)

    repeat["inference"]["runtime"]["genconvit_gpu"] = "3"  # type: ignore[index]
    with pytest.raises(VerificationError, match="genconvit_gpu"):
        compare_repeat_context(first, repeat)


def test_common_subset_id_normalization() -> None:
    assert canonical_video_id(
        "/data/USER/deepfake-bench/datasets/mentor_swap_200/real/a.mp4", 0
    ) == "real/a.mp4"
    assert canonical_video_id("fake\\nested\\b.mp4", 1) == "fake/nested/b.mp4"
    assert canonical_video_id("/some/old/output/c.mp4", 1) == "fake/c.mp4"
    with pytest.raises(SubsetError):
        canonical_video_id("real/wrong.mp4", 1)


def test_common_subset_end_to_end_accepts_legacy_logits(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text(
        "video,label,score\n"
        "/data/real/a.mp4,0,-3.0\n"
        "/data/fake/b.mp4,1,4.0\n",
        encoding="utf-8",
    )
    second.write_text(
        "video,label,score\n"
        "real/a.mp4,0,0.1\n"
        "fake/b.mp4,1,0.9\n",
        encoding="utf-8",
    )
    output = tmp_path / "appendix"

    code = common_subset_main(
        [
            "--scores",
            f"legacy={first}",
            "--scores",
            f"genconvit={second}",
            "--out-dir",
            str(output),
        ]
    )

    assert code == 0
    payload = (output / "common_success_metrics.json").read_text(encoding="utf-8")
    assert '"ranking_permitted": false' in payload
    assert '"common_n_videos": 2' in payload


def test_common_subset_rejects_fractional_labels(tmp_path: Path) -> None:
    bad = tmp_path / "bad.csv"
    other = tmp_path / "other.csv"
    bad.write_text(
        "video,label,score\nreal/a.mp4,0.5,0.1\nfake/b.mp4,1,0.9\n",
        encoding="utf-8",
    )
    other.write_text(
        "video,label,score\nreal/a.mp4,0,0.1\nfake/b.mp4,1,0.9\n",
        encoding="utf-8",
    )

    code = common_subset_main(
        [
            "--scores",
            f"bad={bad}",
            "--scores",
            f"other={other}",
            "--out-dir",
            str(tmp_path / "appendix"),
        ]
    )

    assert code == 2
    assert not (tmp_path / "appendix").exists()
