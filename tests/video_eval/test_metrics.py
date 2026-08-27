"""ROC-AUC helpers; video-level averages frames first."""

from __future__ import annotations

import pytest

from src.video_eval.metrics import roc_auc, video_level_auc, video_level_scores


def test_roc_auc_separable() -> None:
    labels = [0, 0, 1, 1]
    scores = [0.1, 0.2, 0.8, 0.9]
    assert roc_auc(labels, scores) == pytest.approx(1.0)


def test_roc_auc_tie() -> None:
    labels = [0, 1]
    scores = [0.5, 0.5]
    assert roc_auc(labels, scores) == pytest.approx(0.5)


def test_video_level_mean_then_auc() -> None:
    video_ids = ["a", "a", "b", "b"]
    frame_scores = [0.0, 1.0, 0.9, 1.0]
    agg = video_level_scores(video_ids, frame_scores)
    assert agg["a"] == pytest.approx(0.5)
    assert agg["b"] == pytest.approx(0.95)
    auc = video_level_auc(video_ids, frame_scores, {"a": 0, "b": 1})
    assert auc == pytest.approx(1.0)


def test_roc_auc_rejects_single_class() -> None:
    with pytest.raises(ValueError, match="both real and fake"):
        roc_auc([1, 1], [0.2, 0.9])
