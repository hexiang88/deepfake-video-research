#!/usr/bin/env python3
"""Auditable standalone GenConViT evaluation for ``real/`` and ``fake/`` videos.

This file deliberately lives outside the official GenConViT clone and does not
write to the deepfake-video-research result schema.  It reuses the official
frame extraction, face crop, normalization, ED model, VAE model, and ensemble
score direction while making failures and run metadata explicit.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import hashlib
import importlib.metadata
import json
import logging
import math
import os
import platform
import random
import subprocess
import sys
import time
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Sequence

import numpy as np

# Required by deterministic CUDA matrix multiplication on CUDA 10.2+.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
# Importing the official clone must not create untracked __pycache__ files.
sys.dont_write_bytecode = True

OFFICIAL_REPO_URL = "https://github.com/erprogs/GenConViT.git"
OFFICIAL_COMMIT = "2c1d0bd7eecea94926595781a744e3f4b8b55290"
HF_REPO_ID = "Deressa/GenConViT"
HF_REVISION = "32d6e9e3c931a37971cc756da706cf1eef643372"
ED_FILENAME = "genconvit_ed_inference.pth"
VAE_FILENAME = "genconvit_vae_inference.pth"
ED_SHA256 = "86f0c2e875016435def7d031b357bda5dc0061367290d73de121186df3f03f8c"
VAE_SHA256 = "53c627c82d1439fc80e18ac462c1ed6969a3babe5376124a5c38d1c0c88c9042"
CODE_LICENSE = "MIT"
WEIGHTS_LICENSE = "CC-BY-NC-4.0"
VIDEO_EXTENSIONS = {".avi", ".mp4", ".mpg", ".mpeg", ".mov", ".mkv", ".webm"}
THRESHOLD = 0.5
SCHEMA_VERSION = "genconvit-custom-eval/1.0"
METRIC_NAMES = (
    "auc",
    "ap",
    "accuracy_at_0_5",
    "macro_f1_at_0_5",
    "precision_fake_at_0_5",
    "recall_fake_at_0_5",
    "eer",
)


class PreflightError(RuntimeError):
    """A run-level input, environment, or integrity check failed."""


class SampleFailure(RuntimeError):
    """One video failed in a known stage and should not receive a score."""

    def __init__(
        self,
        stage: str,
        code: str,
        message: str,
        *,
        n_frames_sampled: int = 0,
        n_faces_used: int = 0,
    ):
        super().__init__(message)
        self.stage = stage
        self.code = code
        self.n_frames_sampled = n_frames_sampled
        self.n_faces_used = n_faces_used


class FatalEvaluationError(RuntimeError):
    """A run-level inference failure, such as CUDA OOM, requires stopping."""


@dataclass(frozen=True)
class VideoItem:
    path: Path
    video_id: str
    label: int
    size_bytes: int
    sha256: str | None = None


@dataclass(frozen=True)
class FailureRecord:
    video_id: str
    label: int
    failure_stage: str
    error_code: str
    error_message: str
    n_frames_sampled: int
    n_faces_used: int


@dataclass(frozen=True)
class ScoreRecord:
    video_id: str
    label: int
    score: float
    pred_at_0_5: int
    official_argmax_pred: int
    n_frames_sampled: int
    n_faces_used: int
    per_video_seed: int


@contextlib.contextmanager
def pushd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def short_message(exc: BaseException, limit: int = 500) -> str:
    text = " ".join(str(exc).split()) or exc.__class__.__name__
    return text[:limit]


def run_checked(command: Sequence[str], cwd: Path | None = None) -> str:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = short_message(RuntimeError(completed.stderr or completed.stdout))
        raise PreflightError(f"command failed ({' '.join(command)}): {stderr}")
    return completed.stdout.strip()


def verify_official_repo(repo_dir: Path) -> dict[str, Any]:
    if not repo_dir.is_dir() or not (repo_dir / ".git").exists():
        raise PreflightError(f"official clone missing or not a Git checkout: {repo_dir}")
    commit = run_checked(["git", "rev-parse", "HEAD"], cwd=repo_dir)
    if commit != OFFICIAL_COMMIT:
        raise PreflightError(
            f"official clone commit mismatch: expected {OFFICIAL_COMMIT}, got {commit}"
        )
    dirty = run_checked(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo_dir
    )
    if dirty:
        raise PreflightError(
            "official clone is not clean; keep the standalone runner and weights "
            f"outside it. First status line: {dirty.splitlines()[0]}"
        )
    remote = ""
    try:
        remote = run_checked(["git", "remote", "get-url", "origin"], cwd=repo_dir)
    except PreflightError:
        pass
    return {"repo_url": remote or OFFICIAL_REPO_URL, "commit": commit, "dirty": False}


def verify_weight(path: Path, expected_sha256: str, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise PreflightError(f"{label} weights missing: {path}")
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise PreflightError(
            f"{label} SHA256 mismatch: expected {expected_sha256}, got {actual}"
        )
    return {"path": str(path), "sha256": actual, "size_bytes": path.stat().st_size}


def discover_videos(
    dataset_dir: Path,
    *,
    expected_real: int | None,
    expected_fake: int | None,
    hash_videos: bool,
) -> tuple[list[VideoItem], str]:
    if not dataset_dir.is_dir():
        raise PreflightError(f"dataset directory missing: {dataset_dir}")

    items: list[VideoItem] = []
    for class_name, label, expected in (
        ("real", 0, expected_real),
        ("fake", 1, expected_fake),
    ):
        class_dir = dataset_dir / class_name
        if not class_dir.is_dir():
            raise PreflightError(f"required class directory missing: {class_dir}")
        paths = sorted(
            (
                path
                for path in class_dir.rglob("*")
                if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
            ),
            key=lambda path: path.relative_to(dataset_dir).as_posix(),
        )
        if not paths:
            raise PreflightError(f"no supported videos found in {class_dir}")
        if expected is not None and len(paths) != expected:
            raise PreflightError(
                f"{class_name} count mismatch: expected {expected}, discovered {len(paths)}"
            )
        for path in paths:
            relative = path.relative_to(dataset_dir).as_posix()
            items.append(
                VideoItem(
                    path=path,
                    video_id=relative,
                    label=label,
                    size_bytes=path.stat().st_size,
                    sha256=sha256_file(path) if hash_videos else None,
                )
            )

    ids = [item.video_id for item in items]
    if len(ids) != len(set(ids)):
        raise PreflightError("duplicate video_id values discovered")

    canonical = "".join(
        json.dumps(
            {
                "video_id": item.video_id,
                "label": item.label,
                "size_bytes": item.size_bytes,
                "sha256": item.sha256,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
        for item in items
    )
    manifest_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return items, manifest_sha256


def per_video_seed(global_seed: int, video_id: str) -> int:
    digest = hashlib.sha256(f"{global_seed}\0{video_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") % (2**31)


def _validate_binary_inputs(
    labels: Sequence[int],
    scores: Sequence[float],
    *,
    require_unit_interval: bool = True,
) -> None:
    if len(labels) != len(scores):
        raise ValueError("labels and scores lengths differ")
    if len(labels) == 0:
        raise ValueError("no scored videos")
    if any(label not in (0, 1) for label in labels):
        raise ValueError("labels must be 0 (real) or 1 (fake)")
    for score in scores:
        if not math.isfinite(float(score)):
            raise ValueError(f"score must be finite, got {score!r}")
        if require_unit_interval and not 0.0 <= float(score) <= 1.0:
            raise ValueError(f"score must be in [0,1], got {score!r}")


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Tie-aware ROC AUC in [0, 1], with fake (1) as the positive class."""
    _validate_binary_inputs(labels, scores, require_unit_interval=False)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("ROC AUC requires both classes")

    pairs = sorted(zip(scores, labels), key=lambda pair: float(pair[0]))
    rank_sum_pos = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and float(pairs[end][0]) == float(pairs[index][0]):
            end += 1
        average_rank = ((index + 1) + end) / 2.0
        rank_sum_pos += average_rank * sum(label for _, label in pairs[index:end])
        index = end
    return (rank_sum_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)


def average_precision(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Grouped-threshold average precision in [0, 1]."""
    _validate_binary_inputs(labels, scores, require_unit_interval=False)
    n_pos = sum(labels)
    if n_pos == 0 or n_pos == len(labels):
        raise ValueError("average precision requires both classes")

    pairs = sorted(zip(scores, labels), key=lambda pair: float(pair[0]), reverse=True)
    tp = 0
    fp = 0
    previous_recall = 0.0
    ap = 0.0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and float(pairs[end][0]) == float(pairs[index][0]):
            end += 1
        group = pairs[index:end]
        tp += sum(label for _, label in group)
        fp += len(group) - sum(label for _, label in group)
        recall = tp / n_pos
        precision = tp / (tp + fp)
        ap += (recall - previous_recall) * precision
        previous_recall = recall
        index = end
    return ap


def equal_error_rate(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Linearly interpolate the FPR/FNR crossing on grouped ROC points."""
    _validate_binary_inputs(labels, scores, require_unit_interval=False)
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("EER requires both classes")

    pairs = sorted(zip(scores, labels), key=lambda pair: float(pair[0]), reverse=True)
    points: list[tuple[float, float]] = [(0.0, 1.0)]  # (FPR, FNR)
    tp = 0
    fp = 0
    index = 0
    while index < len(pairs):
        end = index + 1
        while end < len(pairs) and float(pairs[end][0]) == float(pairs[index][0]):
            end += 1
        group = pairs[index:end]
        tp += sum(label for _, label in group)
        fp += len(group) - sum(label for _, label in group)
        points.append((fp / n_neg, 1.0 - tp / n_pos))
        index = end

    for point_index in range(1, len(points)):
        fpr0, fnr0 = points[point_index - 1]
        fpr1, fnr1 = points[point_index]
        diff0 = fnr0 - fpr0
        diff1 = fnr1 - fpr1
        if diff0 == 0:
            return fpr0
        if diff1 == 0:
            return fpr1
        if diff0 > 0 > diff1:
            fraction = diff0 / (diff0 - diff1)
            fpr = fpr0 + fraction * (fpr1 - fpr0)
            fnr = fnr0 + fraction * (fnr1 - fnr0)
            return (fpr + fnr) / 2.0
    raise ValueError("could not locate an EER crossing")


def confusion_counts(
    labels: Sequence[int], scores: Sequence[float], threshold: float = THRESHOLD
) -> dict[str, int]:
    _validate_binary_inputs(labels, scores)
    tp = tn = fp = fn = 0
    for label, score in zip(labels, scores):
        pred = int(float(score) >= threshold)
        if label == 1 and pred == 1:
            tp += 1
        elif label == 0 and pred == 0:
            tn += 1
        elif label == 0 and pred == 1:
            fp += 1
        else:
            fn += 1
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def compute_metrics_pct(
    labels: Sequence[int], scores: Sequence[float]
) -> tuple[dict[str, float], dict[str, int]]:
    _validate_binary_inputs(labels, scores)
    if len(set(labels)) != 2:
        raise ValueError("all formal metrics require both classes")
    cm = confusion_counts(labels, scores)
    tp, tn, fp, fn = cm["tp"], cm["tn"], cm["fp"], cm["fn"]
    n = len(labels)
    precision_fake = tp / (tp + fp) if (tp + fp) else 0.0
    recall_fake = tp / (tp + fn) if (tp + fn) else 0.0
    f1_fake = 2 * tp / (2 * tp + fp + fn) if (2 * tp + fp + fn) else 0.0
    f1_real = 2 * tn / (2 * tn + fp + fn) if (2 * tn + fp + fn) else 0.0
    values = {
        "auc": 100.0 * roc_auc(labels, scores),
        "ap": 100.0 * average_precision(labels, scores),
        "accuracy_at_0_5": 100.0 * (tp + tn) / n,
        "macro_f1_at_0_5": 100.0 * (f1_fake + f1_real) / 2.0,
        "precision_fake_at_0_5": 100.0 * precision_fake,
        "recall_fake_at_0_5": 100.0 * recall_fake,
        "eer": 100.0 * equal_error_rate(labels, scores),
    }
    return values, cm


def stratified_bootstrap_ci(
    labels: Sequence[int],
    scores: Sequence[float],
    *,
    n_resamples: int,
    seed: int,
) -> tuple[dict[str, list[float] | None], int]:
    _validate_binary_inputs(labels, scores)
    real_indices = np.asarray([i for i, label in enumerate(labels) if label == 0])
    fake_indices = np.asarray([i for i, label in enumerate(labels) if label == 1])
    if len(real_indices) < 2 or len(fake_indices) < 2 or n_resamples <= 0:
        return {name: None for name in METRIC_NAMES}, 0

    labels_array = np.asarray(labels, dtype=np.int64)
    scores_array = np.asarray(scores, dtype=np.float64)
    rng = np.random.default_rng(seed)
    samples: dict[str, list[float]] = {name: [] for name in METRIC_NAMES}
    for _ in range(n_resamples):
        selected = np.concatenate(
            (
                rng.choice(real_indices, size=len(real_indices), replace=True),
                rng.choice(fake_indices, size=len(fake_indices), replace=True),
            )
        )
        metric_values, _ = compute_metrics_pct(
            labels_array[selected].tolist(), scores_array[selected].tolist()
        )
        for name, value in metric_values.items():
            samples[name].append(value)

    ci: dict[str, list[float] | None] = {}
    for name, values in samples.items():
        low, high = np.percentile(np.asarray(values), [2.5, 97.5]).tolist()
        ci[name] = [float(low), float(high)]
    return ci, n_resamples


def package_versions() -> dict[str, str | None]:
    names = (
        "torch",
        "torchvision",
        "numpy",
        "timm",
        "decord",
        "dlib",
        "face-recognition",
        "opencv-python",
        "opencv-python-headless",
        "albumentations",
        "scikit-learn",
        "huggingface-hub",
    )
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def configure_determinism(torch: Any, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False


def set_sample_seed(torch: Any, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed % (2**32))
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def is_out_of_memory_error(torch: Any, exc: BaseException) -> bool:
    """Recognize PyTorch and CUDA/dlib memory exhaustion across all stages."""
    oom_types = tuple(
        oom_type
        for oom_type in (
            getattr(torch, "OutOfMemoryError", None),
            getattr(torch.cuda, "OutOfMemoryError", None),
        )
        if isinstance(oom_type, type)
    )
    message = str(exc).lower().replace("_", "")
    return bool(
        (oom_types and isinstance(exc, oom_types))
        or "out of memory" in message
        or "cudaerrormemoryallocation" in message
    )


def raise_if_out_of_memory(torch: Any, exc: BaseException) -> None:
    if is_out_of_memory_error(torch, exc):
        raise FatalEvaluationError(
            "CUDA or accelerator memory exhaustion. Stop and choose a "
            "higher-memory GPU; do not change precision or frame count silently."
        ) from exc


def load_models(
    repo_dir: Path,
    ed_weights: Path,
    vae_weights: Path,
    *,
    global_seed: int,
) -> tuple[Any, Any, Any, Any, dict[str, int]]:
    """Build official ED/VAE models without timm downloads and strict-load weights."""
    try:
        import torch
        import timm
    except ImportError as exc:
        raise PreflightError(f"required model dependency is missing: {exc}") from exc

    if not torch.cuda.is_available():
        raise PreflightError("CUDA is not available; GenConViT formal evaluation requires GPU")
    visible = os.environ.get("CUDA_VISIBLE_DEVICES", "").strip()
    if not visible:
        raise PreflightError("CUDA_VISIBLE_DEVICES is empty; choose GENCONVIT_GPU explicitly")
    if "," in visible:
        raise PreflightError("expose exactly one GPU in CUDA_VISIBLE_DEVICES")

    configure_determinism(torch, global_seed)
    repo_text = str(repo_dir)
    if repo_text not in sys.path:
        sys.path.insert(0, repo_text)

    original_create_model = timm.create_model

    def no_pretrained_create_model(model_name: str, *args: Any, **kwargs: Any) -> Any:
        kwargs["pretrained"] = False
        return original_create_model(model_name, *args, **kwargs)

    with pushd(repo_dir):
        timm.create_model = no_pretrained_create_model
        try:
            from model.config import load_config
            from model.genconvit_ed import GenConViTED
            from model.genconvit_vae import GenConViTVAE
            from model import pred_func

            config = load_config()
            model_ed = GenConViTED(config, pretrained=False)
            # The official VAE constructor ignores its ``pretrained`` argument and
            # hardcodes True; the temporary timm wrapper above forces False.
            model_vae = GenConViTVAE(config, pretrained=False)
        finally:
            timm.create_model = original_create_model

    key_counts: dict[str, int] = {}
    for name, model, weight_path in (
        ("ed", model_ed, ed_weights),
        ("vae", model_vae, vae_weights),
    ):
        checkpoint = torch.load(str(weight_path), map_location=torch.device("cpu"))
        state_dict = (
            checkpoint.get("state_dict", checkpoint)
            if isinstance(checkpoint, dict)
            else checkpoint
        )
        if not isinstance(state_dict, dict):
            raise PreflightError(f"{name} checkpoint does not contain a state dict")
        incompatible = model.load_state_dict(state_dict, strict=True)
        if incompatible.missing_keys or incompatible.unexpected_keys:
            raise PreflightError(
                f"{name} strict load reported missing={incompatible.missing_keys} "
                f"unexpected={incompatible.unexpected_keys}"
            )
        key_counts[name] = len(state_dict)
        del checkpoint, state_dict

    device = torch.device("cuda:0")
    model_ed.to(device=device, dtype=torch.float32).eval()
    model_vae.to(device=device, dtype=torch.float32).eval()
    return torch, model_ed, model_vae, pred_func, key_counts


def official_fake_score(torch: Any, logits: Any) -> tuple[float, int, list[float]]:
    """Reproduce official ``pred_vid`` score semantics without its squeeze bug.

    Official class index 0 is FAKE and index 1 is REAL.  The published code
    applies sigmoid per logit, averages over ED/VAE and faces, then emits either
    mean(fake) or 1-mean(real), whichever class wins the argmax.
    """
    if logits.ndim != 2 or logits.shape[1] != 2 or logits.shape[0] < 1:
        raise SampleFailure(
            "output_validation",
            "invalid_logits_shape",
            f"expected [N,2] logits, got {tuple(logits.shape)}",
        )
    probabilities = torch.sigmoid(logits.float())
    mean_values = probabilities.mean(dim=0)
    if not bool(torch.isfinite(mean_values).all()):
        raise SampleFailure(
            "output_validation", "non_finite_output", "model output is NaN or Inf"
        )
    fake_mean = float(mean_values[0].item())
    real_mean = float(mean_values[1].item())
    official_argmax_pred = 1 if fake_mean >= real_mean else 0
    score = fake_mean if fake_mean > real_mean else 1.0 - real_mean
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise SampleFailure(
            "output_validation", "invalid_score", f"invalid fake score: {score!r}"
        )
    return score, official_argmax_pred, [fake_mean, real_mean]


def score_one_video(
    item: VideoItem,
    *,
    torch: Any,
    model_ed: Any,
    model_vae: Any,
    pred_func: Any,
    num_frames: int,
    global_seed: int,
) -> tuple[ScoreRecord, list[float]]:
    sampled = 0
    faces_used = 0
    sample_seed = per_video_seed(global_seed, item.video_id)
    set_sample_seed(torch, sample_seed)

    try:
        frames = pred_func.extract_frames(str(item.path), num_frames)
        sampled = len(frames)
    except Exception as exc:
        raise_if_out_of_memory(torch, exc)
        raise SampleFailure("decode", "decode_error", short_message(exc)) from exc
    if sampled == 0:
        raise SampleFailure("decode", "empty_video", "no frames were decoded")

    try:
        faces, faces_used = pred_func.face_rec(frames)
    except Exception as exc:
        raise_if_out_of_memory(torch, exc)
        raise SampleFailure(
            "preprocess",
            "face_detection_error",
            short_message(exc),
            n_frames_sampled=sampled,
        ) from exc
    if faces_used == 0:
        raise SampleFailure(
            "preprocess",
            "no_face",
            "no face detected in sampled frames",
            n_frames_sampled=sampled,
        )

    try:
        tensor = pred_func.preprocess_frame(faces)
    except Exception as exc:
        raise_if_out_of_memory(torch, exc)
        raise SampleFailure(
            "preprocess",
            "normalization_error",
            short_message(exc),
            n_frames_sampled=sampled,
            n_faces_used=faces_used,
        ) from exc
    if not hasattr(tensor, "shape") or tensor.shape[0] == 0:
        raise SampleFailure(
            "preprocess",
            "empty_tensor",
            "preprocessing returned no faces",
            n_frames_sampled=sampled,
            n_faces_used=faces_used,
        )
    if tensor.dtype != torch.float32:
        tensor = tensor.float()

    try:
        with torch.inference_mode():
            ed_logits = model_ed(tensor)
            vae_logits, _ = model_vae(tensor)
            combined_logits = torch.cat((ed_logits, vae_logits), dim=0)
            score, official_pred, mean_values = official_fake_score(torch, combined_logits)
    except SampleFailure as exc:
        exc.n_frames_sampled = sampled
        exc.n_faces_used = faces_used
        raise
    except Exception as exc:
        raise_if_out_of_memory(torch, exc)
        raise SampleFailure(
            "model",
            "model_error",
            short_message(exc),
            n_frames_sampled=sampled,
            n_faces_used=faces_used,
        ) from exc

    record = ScoreRecord(
        video_id=item.video_id,
        label=item.label,
        score=score,
        pred_at_0_5=int(score >= THRESHOLD),
        official_argmax_pred=official_pred,
        n_frames_sampled=sampled,
        n_faces_used=faces_used,
        per_video_seed=sample_seed,
    )
    return record, mean_values


def write_dataset_manifest(path: Path, items: Sequence[VideoItem]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["video_id", "label", "size_bytes", "sha256"],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "video_id": item.video_id,
                    "label": item.label,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256 or "",
                }
            )


def write_outputs(
    out_dir: Path,
    items: Sequence[VideoItem],
    scores: Sequence[ScoreRecord],
    failures: Sequence[FailureRecord],
) -> None:
    score_by_id = {record.video_id: record for record in scores}
    failure_by_id = {record.video_id: record for record in failures}
    if set(score_by_id) & set(failure_by_id):
        raise RuntimeError("a video cannot be both scored and failed")

    with (out_dir / "scores.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["video", "label", "score"])
        writer.writeheader()
        for record in scores:
            writer.writerow(
                {
                    "video": record.video_id,
                    "label": record.label,
                    "score": format(record.score, ".17g"),
                }
            )

    prediction_fields = [
        "video_id",
        "label",
        "status",
        "score",
        "pred_at_0_5",
        "official_argmax_pred",
        "failure_stage",
        "error_code",
        "error_message",
        "n_frames_sampled",
        "n_faces_used",
        "per_video_seed",
    ]
    with (out_dir / "predictions.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=prediction_fields)
        writer.writeheader()
        for item in items:
            if item.video_id in score_by_id:
                record = score_by_id[item.video_id]
                writer.writerow(
                    {
                        "video_id": record.video_id,
                        "label": record.label,
                        "status": "scored",
                        "score": format(record.score, ".17g"),
                        "pred_at_0_5": record.pred_at_0_5,
                        "official_argmax_pred": record.official_argmax_pred,
                        "failure_stage": "",
                        "error_code": "",
                        "error_message": "",
                        "n_frames_sampled": record.n_frames_sampled,
                        "n_faces_used": record.n_faces_used,
                        "per_video_seed": record.per_video_seed,
                    }
                )
            else:
                record = failure_by_id[item.video_id]
                writer.writerow(
                    {
                        "video_id": record.video_id,
                        "label": record.label,
                        "status": "failed",
                        "score": "",
                        "pred_at_0_5": "",
                        "official_argmax_pred": "",
                        "failure_stage": record.failure_stage,
                        "error_code": record.error_code,
                        "error_message": record.error_message,
                        "n_frames_sampled": record.n_frames_sampled,
                        "n_faces_used": record.n_faces_used,
                        "per_video_seed": "",
                    }
                )

    (out_dir / "failures.json").write_text(
        json.dumps([asdict(record) for record in failures], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )


def build_coverage(
    items: Sequence[VideoItem],
    scores: Sequence[ScoreRecord],
    failures: Sequence[FailureRecord],
) -> dict[str, Any]:
    coverage: dict[str, Any] = {
        "n_requested": len(items),
        "n_scored": len(scores),
        "n_failed": len(failures),
    }
    for name, label in (("real", 0), ("fake", 1)):
        requested = sum(item.label == label for item in items)
        scored = sum(item.label == label for item in scores)
        failed = sum(item.label == label for item in failures)
        coverage[f"n_{name}_requested"] = requested
        coverage[f"n_{name}_scored"] = scored
        coverage[f"n_{name}_failed"] = failed
    coverage["coverage_pct"] = (
        100.0 * coverage["n_scored"] / coverage["n_requested"]
        if coverage["n_requested"]
        else 0.0
    )
    if coverage["n_scored"] + coverage["n_failed"] != coverage["n_requested"]:
        raise RuntimeError("coverage accounting mismatch")
    return coverage


def collect_runtime_metadata(torch: Any) -> dict[str, Any]:
    import dlib

    nvidia_smi = ""
    try:
        nvidia_smi = run_checked(
            [
                "nvidia-smi",
                "--query-gpu=index,uuid,name,driver_version",
                "--format=csv,noheader",
            ]
        )
    except PreflightError as exc:
        nvidia_smi = f"unavailable: {exc}"
    gpu_uuid = getattr(torch.cuda.get_device_properties(0), "uuid", None)
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "packages": package_versions(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "genconvit_gpu": os.environ.get("GENCONVIT_GPU"),
        "torch_cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version(),
        "visible_gpu_count": torch.cuda.device_count(),
        "visible_gpu_name": torch.cuda.get_device_name(0),
        "visible_gpu_uuid": str(gpu_uuid) if gpu_uuid is not None else None,
        "nvidia_smi": nvidia_smi,
        "dlib_use_cuda": bool(dlib.DLIB_USE_CUDA),
        "dlib_face_detector_mode": "cnn" if dlib.DLIB_USE_CUDA else "hog",
        "deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        "precision": "fp32",
    }


def default_weight_path(repo_dir: Path, filename: str) -> Path:
    # $BENCH_ROOT/models/GenConViT -> $BENCH_ROOT/weights/genconvit/<file>
    try:
        bench_root = repo_dir.parents[1]
    except IndexError as exc:
        raise PreflightError("cannot infer BENCH_ROOT from --repo-dir") from exc
    return bench_root / "weights" / "genconvit" / filename


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Standalone GenConViT real/fake custom-set evaluation."
    )
    parser.add_argument("--repo-dir", required=True)
    parser.add_argument("--dataset-dir", required=True)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--ed-weights", default="")
    parser.add_argument("--vae-weights", default="")
    parser.add_argument("--frames", type=int, default=15)
    parser.add_argument("--seed", type=int, default=20260818)
    parser.add_argument("--precision", choices=("fp32",), default="fp32")
    parser.add_argument("--expected-real", type=int)
    parser.add_argument("--expected-fake", type=int)
    parser.add_argument("--hash-videos", action="store_true")
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260818)
    parser.add_argument(
        "--evidence-role",
        choices=("pipeline_smoke_only", "custom_evaluation"),
        default="custom_evaluation",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.frames <= 0:
        print("ERROR: --frames must be positive", file=sys.stderr)
        return 2
    if args.bootstrap_resamples < 0:
        print("ERROR: --bootstrap-resamples cannot be negative", file=sys.stderr)
        return 2

    repo_dir = Path(args.repo_dir).expanduser().resolve()
    dataset_dir = Path(args.dataset_dir).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    ed_weights = (
        Path(args.ed_weights).expanduser().resolve()
        if args.ed_weights
        else default_weight_path(repo_dir, ED_FILENAME).resolve()
    )
    vae_weights = (
        Path(args.vae_weights).expanduser().resolve()
        if args.vae_weights
        else default_weight_path(repo_dir, VAE_FILENAME).resolve()
    )

    if out_dir == dataset_dir or dataset_dir in out_dir.parents:
        print("ERROR: --out-dir must not be inside the read-only dataset", file=sys.stderr)
        return 2
    if out_dir.exists():
        print(f"ERROR: output directory already exists: {out_dir}", file=sys.stderr)
        return 2

    start_time = time.perf_counter()
    started_at = utc_now()
    try:
        repo_meta = verify_official_repo(repo_dir)
        ed_meta = verify_weight(ed_weights, ED_SHA256, "ED")
        vae_meta = verify_weight(vae_weights, VAE_SHA256, "VAE")
        items, manifest_sha256 = discover_videos(
            dataset_dir,
            expected_real=args.expected_real,
            expected_fake=args.expected_fake,
            hash_videos=args.hash_videos,
        )
    except PreflightError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)sZ %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(out_dir / "eval.log", encoding="utf-8"),
            logging.StreamHandler(sys.stderr),
        ],
        force=True,
    )
    logging.Formatter.converter = time.gmtime
    logger = logging.getLogger("genconvit_eval")
    write_dataset_manifest(out_dir / "dataset_manifest.csv", items)
    logger.info(
        "discovered dataset=%s requested=%d real=%d fake=%d manifest_sha256=%s",
        args.dataset_name,
        len(items),
        sum(item.label == 0 for item in items),
        sum(item.label == 1 for item in items),
        manifest_sha256,
    )

    scores: list[ScoreRecord] = []
    failures: list[FailureRecord] = []
    progress_path = out_dir / "progress.jsonl"
    fatal_error: str | None = None
    runtime_meta: dict[str, Any] = {}
    key_counts: dict[str, int] = {}

    try:
        torch, model_ed, model_vae, pred_func, key_counts = load_models(
            repo_dir,
            ed_weights,
            vae_weights,
            global_seed=args.seed,
        )
        runtime_meta = collect_runtime_metadata(torch)
        logger.info(
            "strict model load passed ed_keys=%d vae_keys=%d gpu=%s detector=%s",
            key_counts["ed"],
            key_counts["vae"],
            runtime_meta["visible_gpu_name"],
            runtime_meta["dlib_face_detector_mode"],
        )

        with progress_path.open("a", encoding="utf-8") as progress:
            for index, item in enumerate(items, start=1):
                try:
                    record, mean_values = score_one_video(
                        item,
                        torch=torch,
                        model_ed=model_ed,
                        model_vae=model_vae,
                        pred_func=pred_func,
                        num_frames=args.frames,
                        global_seed=args.seed,
                    )
                    scores.append(record)
                    progress.write(
                        json.dumps(
                            {"status": "scored", **asdict(record)},
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n"
                    )
                    progress.flush()
                    logger.info(
                        "[%d/%d] scored %s label=%d score=%.9f mean_fake=%.9f "
                        "mean_real=%.9f faces=%d",
                        index,
                        len(items),
                        item.video_id,
                        item.label,
                        record.score,
                        mean_values[0],
                        mean_values[1],
                        record.n_faces_used,
                    )
                except SampleFailure as exc:
                    failure = FailureRecord(
                        video_id=item.video_id,
                        label=item.label,
                        failure_stage=exc.stage,
                        error_code=exc.code,
                        error_message=short_message(exc),
                        n_frames_sampled=exc.n_frames_sampled,
                        n_faces_used=exc.n_faces_used,
                    )
                    failures.append(failure)
                    progress.write(
                        json.dumps(
                            {"status": "failed", **asdict(failure)},
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        + "\n"
                    )
                    progress.flush()
                    logger.exception(
                        "[%d/%d] failed %s stage=%s code=%s",
                        index,
                        len(items),
                        item.video_id,
                        exc.stage,
                        exc.code,
                    )
                except FatalEvaluationError:
                    raise
    except FatalEvaluationError as exc:
        fatal_error = short_message(exc)
        logger.exception("fatal evaluation error: %s", fatal_error)
    except Exception as exc:
        fatal_error = short_message(exc)
        logger.exception("fatal model load or run error: %s", fatal_error)

    try:
        post_run_dirty = run_checked(
            ["git", "status", "--porcelain", "--untracked-files=all"], cwd=repo_dir
        )
        repo_meta["post_run_dirty"] = bool(post_run_dirty)
        if post_run_dirty:
            fatal_error = (
                "official clone changed during evaluation: "
                f"{post_run_dirty.splitlines()[0]}"
            )
            logger.error("%s", fatal_error)
    except PreflightError as exc:
        repo_meta["post_run_dirty"] = True
        fatal_error = short_message(exc)
        logger.error("could not verify post-run clone cleanliness: %s", fatal_error)

    # If a fatal error stopped the loop, unvisited inputs must remain auditable.
    visited = {record.video_id for record in scores} | {record.video_id for record in failures}
    if fatal_error:
        for item in items:
            if item.video_id not in visited:
                failures.append(
                    FailureRecord(
                        video_id=item.video_id,
                        label=item.label,
                        failure_stage="model",
                        error_code="run_aborted",
                        error_message=fatal_error,
                        n_frames_sampled=0,
                        n_faces_used=0,
                    )
                )

    write_outputs(out_dir, items, scores, failures)
    coverage = build_coverage(items, scores, failures)
    labels = [record.label for record in scores]
    score_values = [record.score for record in scores]

    point_metrics: dict[str, float | None] = {name: None for name in METRIC_NAMES}
    ci: dict[str, list[float] | None] = {name: None for name in METRIC_NAMES}
    confusion: dict[str, int] | None = None
    valid_resamples = 0
    if len(set(labels)) == 2:
        point_metrics, confusion = compute_metrics_pct(labels, score_values)
        ci, valid_resamples = stratified_bootstrap_ci(
            labels,
            score_values,
            n_resamples=args.bootstrap_resamples,
            seed=args.bootstrap_seed,
        )

    if fatal_error or len(set(labels)) != 2:
        status = "eval_failed"
    elif failures:
        status = "partial"
    else:
        status = "ok"

    metric_payload = {
        name: {
            "value_pct": point_metrics[name],
            "ci95_pct": ci[name],
            "unit": "percent",
        }
        for name in METRIC_NAMES
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "run": {
            "status": status,
            "fatal_error": fatal_error,
            "started_at_utc": started_at,
            "completed_at_utc": utc_now(),
            "duration_seconds": time.perf_counter() - start_time,
            "command": [sys.executable, *sys.argv],
            "evidence_role": args.evidence_role,
        },
        "evaluation_label": (
            f"{args.dataset_name} custom evaluation / OOD status unverified"
        ),
        "dataset": {
            "name": args.dataset_name,
            "path": str(dataset_dir),
            "layout": "real=0,fake=1",
            "manifest_sha256": manifest_sha256,
            "content_sha256_included": bool(args.hash_videos),
            "split": "custom",
            "generator": "unverified",
            "degradation": "unverified",
            "ood_status": "unverified",
        },
        "model": {
            "name": "GenConViT ED+VAE official ensemble",
            "official_repository": repo_meta,
            "code_license": CODE_LICENSE,
            "weights_repository": HF_REPO_ID,
            "weights_revision": HF_REVISION,
            "weights_license": WEIGHTS_LICENSE,
            "ed_weights": ed_meta,
            "vae_weights": vae_meta,
            "strict_load": True,
            "state_dict_key_counts": key_counts,
            "timm_pretrained_during_construction": False,
        },
        "inference": {
            "frames_requested_per_video": args.frames,
            "seed": args.seed,
            "per_video_seed_derivation": "sha256(global_seed\\0video_id) first 64 bits mod 2^31",
            "precision": args.precision,
            "threshold": THRESHOLD,
            "threshold_source": "benchmark protocol fixed 0.5; not tuned on this dataset",
            "threshold_note": (
                "Fixed-threshold metrics intentionally use score >= 0.5. The official "
                "argmax decision is preserved separately in predictions.csv and can differ."
            ),
            "positive_label": 1,
            "score_semantics": (
                "official GenConViT fake score: sigmoid logits; mean over faces and "
                "ED/VAE; class 0 is fake; emit mean(fake) if fake wins else 1-mean(real)"
            ),
            "frame_sampling": "official decord + numpy.linspace",
            "face_crop": "official face_recognition/dlib path",
            "failed_video_policy": "exclude from metrics and list explicitly; never impute 0.5",
            "runtime": runtime_meta,
        },
        "coverage": coverage,
        "confusion_matrix_at_0_5": confusion,
        "metrics": metric_payload,
        "bootstrap": {
            "method": "video-level stratified percentile",
            "requested_resamples": args.bootstrap_resamples,
            "valid_resamples": valid_resamples,
            "seed": args.bootstrap_seed,
            "percentiles": [2.5, 97.5],
            "conditioned_on": "successfully scored videos",
        },
        "artifacts": {
            "scores_csv": str(out_dir / "scores.csv"),
            "predictions_csv": str(out_dir / "predictions.csv"),
            "failures_json": str(out_dir / "failures.json"),
            "dataset_manifest_csv": str(out_dir / "dataset_manifest.csv"),
            "progress_jsonl": str(progress_path),
            "log": str(out_dir / "eval.log"),
        },
        "reporting_guardrail": (
            "Do not write this result to indomain.json and do not compare it as an "
            "official Celeb-DF, FF++, DFDC, or paper split reproduction."
        ),
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    logger.info(
        "completed status=%s scored=%d failed=%d output=%s",
        status,
        len(scores),
        len(failures),
        out_dir,
    )
    if point_metrics["auc"] is not None:
        logger.info(
            "video metrics pct AUC=%.4f AP=%.4f Acc=%.4f macro-F1=%.4f EER=%.4f",
            point_metrics["auc"],
            point_metrics["ap"],
            point_metrics["accuracy_at_0_5"],
            point_metrics["macro_f1_at_0_5"],
            point_metrics["eer"],
        )
    return 0 if status in {"ok", "partial"} else 5


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        raise SystemExit(130)
    except Exception:
        traceback.print_exc()
        raise SystemExit(70)
