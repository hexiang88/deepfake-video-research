#!/usr/bin/env python3
"""Validate GenConViT standalone artifacts and optionally compare repeat scores."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any, Sequence

from genconvit_dataset_eval import (
    ED_SHA256,
    HF_REVISION,
    OFFICIAL_COMMIT,
    VAE_SHA256,
    compute_metrics_pct,
)


class VerificationError(RuntimeError):
    pass


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise VerificationError(f"missing artifact: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_summary(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "summary.json"
    if not path.is_file():
        raise VerificationError(f"missing artifact: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise VerificationError("summary.json must be a JSON object")
    return payload


def close(left: float, right: float, atol: float = 1e-9) -> bool:
    return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=atol)


def binary_label(value: Any, *, context: str) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise VerificationError(f"invalid label for {context}: {value!r}") from exc
    if not math.isfinite(numeric) or not numeric.is_integer():
        raise VerificationError(f"invalid label for {context}: {value!r}")
    label = int(numeric)
    if label not in (0, 1):
        raise VerificationError(f"invalid label for {context}: {value!r}")
    return label


def index_rows(
    rows: Sequence[dict[str, Any]], *, id_field: str, artifact: str
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row_number, row in enumerate(rows, start=2):
        if not isinstance(row, dict):
            raise VerificationError(f"{artifact} row {row_number} is not an object")
        video_id = str(row.get(id_field, ""))
        if not video_id:
            raise VerificationError(
                f"{artifact} row {row_number} has no {id_field}"
            )
        if video_id in indexed:
            raise VerificationError(f"duplicate ID in {artifact}: {video_id}")
        indexed[video_id] = row
    return indexed


def validate_run(
    run_dir: Path,
    *,
    expected_real: int | None,
    expected_fake: int | None,
    allow_pipeline_smoke: bool,
) -> tuple[dict[str, Any], dict[str, float]]:
    summary = read_summary(run_dir)
    scores = read_csv(run_dir / "scores.csv")
    predictions = read_csv(run_dir / "predictions.csv")
    failures_path = run_dir / "failures.json"
    manifest = read_csv(run_dir / "dataset_manifest.csv")
    required_files = (failures_path, run_dir / "eval.log", run_dir / "progress.jsonl")
    if any(not path.is_file() for path in required_files):
        raise VerificationError("failures.json, progress.jsonl, or eval.log is missing")
    failures = json.loads(failures_path.read_text(encoding="utf-8"))
    if not isinstance(failures, list):
        raise VerificationError("failures.json must contain a list")

    coverage = summary.get("coverage") or {}
    n_requested = int(coverage.get("n_requested", -1))
    n_scored = int(coverage.get("n_scored", -1))
    n_failed = int(coverage.get("n_failed", -1))
    if len(predictions) != n_requested or len(manifest) != n_requested:
        raise VerificationError("predictions/manifest row count does not equal n_requested")
    if len(scores) != n_scored or len(failures) != n_failed:
        raise VerificationError("scores/failures row count does not equal summary coverage")
    if n_scored + n_failed != n_requested:
        raise VerificationError("n_scored + n_failed does not equal n_requested")

    manifest_by_id = index_rows(
        manifest, id_field="video_id", artifact="dataset_manifest.csv"
    )
    prediction_by_id = index_rows(
        predictions, id_field="video_id", artifact="predictions.csv"
    )
    score_by_id = index_rows(scores, id_field="video", artifact="scores.csv")
    failure_by_id = index_rows(
        failures, id_field="video_id", artifact="failures.json"
    )
    requested_ids = set(manifest_by_id)
    if set(prediction_by_id) != requested_ids:
        raise VerificationError(
            "predictions.csv IDs do not exactly match dataset_manifest.csv"
        )
    scored_ids = {
        video_id
        for video_id, row in prediction_by_id.items()
        if row.get("status") == "scored"
    }
    failed_ids = {
        video_id
        for video_id, row in prediction_by_id.items()
        if row.get("status") == "failed"
    }
    if set(score_by_id) != scored_ids:
        raise VerificationError("scores.csv IDs do not exactly match scored predictions")
    if set(failure_by_id) != failed_ids:
        raise VerificationError(
            "failures.json IDs do not exactly match failed predictions"
        )
    if scored_ids & failed_ids or scored_ids | failed_ids != requested_ids:
        raise VerificationError("prediction status partition is inconsistent")

    manifest_lines: list[str] = []
    manifest_labels: dict[str, int] = {}
    for video_id, row in manifest_by_id.items():
        try:
            size_bytes = int(row["size_bytes"])
        except (KeyError, TypeError, ValueError) as exc:
            raise VerificationError(
                f"invalid manifest metadata for {video_id}: {exc}"
            ) from exc
        label = binary_label(row.get("label"), context=f"manifest {video_id}")
        digest = str(row.get("sha256", ""))
        if size_bytes < 0:
            raise VerificationError(f"invalid manifest size for {video_id}")
        if (summary.get("dataset") or {}).get("content_sha256_included") is True:
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise VerificationError(f"invalid or missing video SHA256 for {video_id}")
        manifest_labels[video_id] = label
        manifest_lines.append(
            json.dumps(
                {
                    "video_id": video_id,
                    "label": label,
                    "size_bytes": size_bytes,
                    "sha256": digest or None,
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        )
    calculated_manifest_sha256 = hashlib.sha256(
        "".join(manifest_lines).encode("utf-8")
    ).hexdigest()
    if calculated_manifest_sha256 != (summary.get("dataset") or {}).get(
        "manifest_sha256"
    ):
        raise VerificationError("dataset manifest SHA256 does not match summary")

    for video_id, prediction in prediction_by_id.items():
        prediction_label = binary_label(
            prediction.get("label"), context=f"prediction {video_id}"
        )
        if prediction_label != manifest_labels[video_id]:
            raise VerificationError(f"manifest/prediction label mismatch for {video_id}")
        linked = score_by_id.get(video_id) or failure_by_id.get(video_id)
        linked_label = binary_label(
            linked.get("label"), context=f"linked artifact {video_id}"
        )
        if linked_label != prediction_label:
            raise VerificationError(f"artifact label mismatch for {video_id}")
        if prediction.get("status") == "scored":
            if not prediction.get("score") or not close(
                float(prediction["score"]), float(score_by_id[video_id]["score"]), 0.0
            ):
                raise VerificationError(f"prediction/score value mismatch for {video_id}")

    real_requested = int(coverage.get("n_real_requested", -1))
    fake_requested = int(coverage.get("n_fake_requested", -1))
    if expected_real is not None and real_requested != expected_real:
        raise VerificationError(
            f"expected {expected_real} real requests, summary has {real_requested}"
        )
    if expected_fake is not None and fake_requested != expected_fake:
        raise VerificationError(
            f"expected {expected_fake} fake requests, summary has {fake_requested}"
        )
    if real_requested + fake_requested != n_requested:
        raise VerificationError("per-class requested counts do not sum to total")

    if {row["status"] for row in predictions} - {"scored", "failed"}:
        raise VerificationError("unexpected status in predictions.csv")
    for row in predictions:
        label = int(row["label"])
        if label not in (0, 1):
            raise VerificationError(f"invalid label for {row['video_id']}")
        if row["status"] == "failed" and row["score"]:
            raise VerificationError(f"failed video has an imputed score: {row['video_id']}")

    model = summary.get("model") or {}
    repo = model.get("official_repository") or {}
    if (
        repo.get("commit") != OFFICIAL_COMMIT
        or repo.get("dirty") is not False
        or repo.get("post_run_dirty") is not False
    ):
        raise VerificationError("official repository commit/clean metadata mismatch")
    if model.get("weights_revision") != HF_REVISION:
        raise VerificationError("Hugging Face revision mismatch")
    if (model.get("ed_weights") or {}).get("sha256") != ED_SHA256:
        raise VerificationError("ED weight hash mismatch")
    if (model.get("vae_weights") or {}).get("sha256") != VAE_SHA256:
        raise VerificationError("VAE weight hash mismatch")
    if model.get("strict_load") is not True:
        raise VerificationError("strict_load was not recorded as true")

    label_text = str(summary.get("evaluation_label", ""))
    if not label_text.endswith("custom evaluation / OOD status unverified"):
        raise VerificationError("evaluation label violates the reporting guardrail")
    evidence_role = (summary.get("run") or {}).get("evidence_role")
    if evidence_role == "pipeline_smoke_only" and not allow_pipeline_smoke:
        raise VerificationError("smoke output cannot be accepted as performance evidence")

    score_map: dict[str, float] = {}
    labels: list[int] = []
    values: list[float] = []
    for row in scores:
        video_id = row["video"]
        if video_id in score_map:
            raise VerificationError(f"duplicate score video id: {video_id}")
        label = binary_label(row.get("label"), context=f"score {video_id}")
        score = float(row["score"])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise VerificationError(f"invalid label/score for {video_id}")
        score_map[video_id] = score
        labels.append(label)
        values.append(score)

    for class_name, class_label in (("real", 0), ("fake", 1)):
        requested = sum(label == class_label for label in manifest_labels.values())
        scored = sum(
            binary_label(row.get("label"), context="scores.csv") == class_label
            for row in scores
        )
        failed = sum(
            binary_label(row.get("label"), context="failures.json") == class_label
            for row in failures
        )
        for suffix, actual in (
            ("requested", requested),
            ("scored", scored),
            ("failed", failed),
        ):
            recorded = int(coverage.get(f"n_{class_name}_{suffix}", -1))
            if recorded != actual:
                raise VerificationError(
                    f"coverage mismatch for n_{class_name}_{suffix}: "
                    f"recorded={recorded}, actual={actual}"
                )
    expected_coverage_pct = 100.0 * n_scored / n_requested if n_requested else 0.0
    if not close(expected_coverage_pct, float(coverage.get("coverage_pct", -1))):
        raise VerificationError("coverage_pct does not match scored/requested counts")

    status = (summary.get("run") or {}).get("status")
    if status not in {"ok", "partial", "eval_failed"}:
        raise VerificationError(f"unknown run status: {status!r}")
    if len(set(labels)) == 2:
        recomputed, confusion = compute_metrics_pct(labels, values)
        summary_metrics = summary.get("metrics") or {}
        for name, value in recomputed.items():
            recorded = (summary_metrics.get(name) or {}).get("value_pct")
            if recorded is None or not close(value, float(recorded)):
                raise VerificationError(
                    f"metric mismatch for {name}: recomputed={value}, recorded={recorded}"
                )
        if summary.get("confusion_matrix_at_0_5") != confusion:
            raise VerificationError("confusion matrix mismatch")
        if status == "eval_failed":
            raise VerificationError("two-class scored output should not be eval_failed")
    elif status != "eval_failed":
        raise VerificationError("single-class scored output must be eval_failed")
    if status == "eval_failed":
        raise VerificationError("run status is eval_failed; this run is not acceptable")

    print(
        f"VERIFIED {run_dir}: status={status} requested={n_requested} "
        f"scored={n_scored} failed={n_failed}"
    )
    return summary, score_map


def compare_repeat(
    original: dict[str, float], repeat: dict[str, float], *, atol: float
) -> None:
    if set(original) != set(repeat):
        missing = sorted(set(original) - set(repeat))[:5]
        extra = sorted(set(repeat) - set(original))[:5]
        raise VerificationError(
            f"repeat scored-ID mismatch; missing={missing}, extra={extra}"
        )
    mismatches = [
        video_id
        for video_id in sorted(original)
        if not math.isclose(
            original[video_id], repeat[video_id], rel_tol=0.0, abs_tol=atol
        )
    ]
    if mismatches:
        first = mismatches[0]
        raise VerificationError(
            f"repeat score mismatch for {first}: "
            f"{original[first]:.17g} vs {repeat[first]:.17g} (atol={atol})"
        )
    print(f"REPEAT VERIFIED: {len(original)} scores identical within atol={atol}")


def compare_repeat_context(
    original: dict[str, Any], repeat: dict[str, Any]
) -> None:
    """Require the repeat to use the same input, seed, GPU, and environment."""

    fields = (
        ("dataset", "name"),
        ("dataset", "path"),
        ("dataset", "manifest_sha256"),
        ("dataset", "content_sha256_included"),
        ("run", "evidence_role"),
        ("inference", "frames_requested_per_video"),
        ("inference", "seed"),
        ("inference", "precision"),
        ("model", "state_dict_key_counts"),
    )
    runtime_fields = (
        "python",
        "platform",
        "packages",
        "cuda_visible_devices",
        "genconvit_gpu",
        "torch_cuda_version",
        "cudnn_version",
        "visible_gpu_count",
        "visible_gpu_name",
        "visible_gpu_uuid",
        "nvidia_smi",
        "dlib_use_cuda",
        "dlib_face_detector_mode",
        "deterministic_algorithms",
        "cublas_workspace_config",
        "precision",
    )

    def nested(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
        value: Any = payload
        for key in path:
            if not isinstance(value, dict) or key not in value:
                raise VerificationError(
                    f"repeat context field is missing: {'.'.join(path)}"
                )
            value = value[key]
        return value

    for path in fields:
        first_value = nested(original, path)
        repeat_value = nested(repeat, path)
        if first_value != repeat_value:
            raise VerificationError(
                f"repeat context mismatch for {'.'.join(path)}: "
                f"{first_value!r} vs {repeat_value!r}"
            )

    if nested(original, ("dataset", "content_sha256_included")) is not True:
        raise VerificationError(
            "repeat verification requires content-hashed dataset manifests"
        )

    for key in runtime_fields:
        path = ("inference", "runtime", key)
        first_value = nested(original, path)
        repeat_value = nested(repeat, path)
        if first_value != repeat_value:
            raise VerificationError(
                f"repeat environment mismatch for {key}: "
                f"{first_value!r} vs {repeat_value!r}"
            )

    print("REPEAT CONTEXT VERIFIED: input, seed, GPU, and environment match")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify GenConViT standalone outputs.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--expected-real", type=int)
    parser.add_argument("--expected-fake", type=int)
    parser.add_argument("--allow-pipeline-smoke", action="store_true")
    parser.add_argument("--repeat-run-dir", default="")
    parser.add_argument("--repeat-atol", type=float, default=0.0)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        first_summary, first_scores = validate_run(
            Path(args.run_dir).expanduser().resolve(),
            expected_real=args.expected_real,
            expected_fake=args.expected_fake,
            allow_pipeline_smoke=args.allow_pipeline_smoke,
        )
        if args.repeat_run_dir:
            repeat_summary, repeat_scores = validate_run(
                Path(args.repeat_run_dir).expanduser().resolve(),
                expected_real=args.expected_real,
                expected_fake=args.expected_fake,
                allow_pipeline_smoke=True,
            )
            compare_repeat_context(first_summary, repeat_summary)
            compare_repeat(first_scores, repeat_scores, atol=args.repeat_atol)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, VerificationError) as exc:
        print(f"VERIFICATION FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
