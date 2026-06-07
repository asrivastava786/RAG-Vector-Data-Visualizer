from __future__ import annotations

import math

from app.services.embedding_service import sparse_terms


def sparse_score(query: str, terms: dict[str, int]) -> float:
    query_terms = sparse_terms(query)
    if not query_terms or not terms:
        return 0.0
    score = 0.0
    query_norm = 0.0
    chunk_norm = 0.0
    for term, query_count in query_terms.items():
        chunk_count = int(terms.get(term, 0) or 0)
        if chunk_count:
            score += (1.0 + math.log(query_count)) * (1.0 + math.log(chunk_count))
        query_norm += query_count * query_count
    for chunk_count in terms.values():
        count = int(chunk_count or 0)
        chunk_norm += count * count
    if query_norm == 0 or chunk_norm == 0:
        return 0.0
    return min(1.0, score / math.sqrt(query_norm * chunk_norm))


def score_sparse_candidates(query: str, candidates: list[object]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for candidate in candidates:
        chunk_id = str(candidate.id)
        terms = getattr(candidate, "sparse_terms_json", {}) or {}
        scores[chunk_id] = sparse_score(query, terms)
    return scores
