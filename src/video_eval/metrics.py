"""ROC-AUC helpers. Video-level AUC averages frame scores per video first."""

from __future__ import annotations

from collections import defaultdict


def roc_auc(labels: list[int], scores: list[float]) -> float:
    if len(labels) != len(scores) or len(labels) < 2:
        raise ValueError("need paired labels and scores, n>=2")
    if len(set(labels)) < 2:
        raise ValueError("need both real and fake labels")
    pos_scores = [s for s, y in zip(scores, labels) if y == 1]
    neg_scores = [s for s, y in zip(scores, labels) if y == 0]
    wins = 0.0
    for p in pos_scores:
        for n in neg_scores:
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return wins / (len(pos_scores) * len(neg_scores))


def video_level_scores(
    video_ids: list[str],
    frame_scores: list[float],
) -> dict[str, float]:
    buckets: dict[str, list[float]] = defaultdict(list)
    for vid, score in zip(video_ids, frame_scores):
        buckets[vid].append(score)
    return {vid: sum(vals) / len(vals) for vid, vals in buckets.items()}


def video_level_auc(
    video_ids: list[str],
    frame_scores: list[float],
    video_labels: dict[str, int],
) -> float:
    agg = video_level_scores(video_ids, frame_scores)
    labels = [video_labels[v] for v in agg]
    scores = [agg[v] for v in agg]
    return roc_auc(labels, scores)
