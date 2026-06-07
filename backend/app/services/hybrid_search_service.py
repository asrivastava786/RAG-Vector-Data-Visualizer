from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FusedScore:
    dense_score: float
    sparse_score: float
    hybrid_score: float


def fuse_scores(
    *,
    dense_score: float,
    sparse_score: float,
    dense_weight: float,
    sparse_weight: float,
) -> FusedScore:
    total = dense_weight + sparse_weight
    if total <= 0:
        dense_weight = 0.7
        sparse_weight = 0.3
        total = 1.0
    dense_weight = dense_weight / total
    sparse_weight = sparse_weight / total
    normalized_dense = max(0.0, min(1.0, (dense_score + 1.0) / 2.0))
    normalized_sparse = max(0.0, min(1.0, sparse_score))
    hybrid = (dense_weight * normalized_dense) + (sparse_weight * normalized_sparse)
    return FusedScore(
        dense_score=round(normalized_dense, 6),
        sparse_score=round(normalized_sparse, 6),
        hybrid_score=round(hybrid, 6),
    )
