from __future__ import annotations

from app.schemas.query import RetrievedChunk


def retrieval_metrics(
    *,
    chunks: list[RetrievedChunk],
    latency_ms: int,
    rbac_leakage_count: int,
) -> dict:
    if not chunks:
        return {
            "context_precision": 0.0,
            "context_recall": 0.0,
            "average_similarity": 0.0,
            "irrelevant_chunk_rate": 1.0,
            "citation_coverage": 0.0,
            "rbac_leakage_count": rbac_leakage_count,
            "latency_ms": latency_ms,
            "estimated_cost": 0.0,
            "overall_score": 0.0,
            "warnings": ["No chunks were retrieved."],
        }

    average_similarity = sum(chunk.scores.dense_score for chunk in chunks) / len(chunks)
    relevant_count = sum(1 for chunk in chunks if chunk.scores.hybrid_score >= 0.35)
    cited_count = sum(
        1 for chunk in chunks if chunk.document_id and (chunk.page_number or chunk.section_heading)
    )
    context_precision = relevant_count / len(chunks)
    context_recall = min(1.0, relevant_count / max(3, len(chunks)))
    irrelevant_rate = 1.0 - context_precision
    citation_coverage = cited_count / len(chunks)
    estimated_cost = round(sum(chunk.token_count for chunk in chunks) * 0.0000001, 6)
    latency_penalty = min(0.25, latency_ms / 4000)
    cost_penalty = min(0.15, estimated_cost / 0.05)
    warnings: list[str] = []
    if rbac_leakage_count:
        warnings.append("RBAC leakage detected. Results should not be used.")
    if irrelevant_rate > 0.5:
        warnings.append("High irrelevant chunk rate.")
    if citation_coverage < 0.5:
        warnings.append("Citation coverage is low.")
    if rbac_leakage_count:
        overall_score = 0.0
    else:
        overall_score = max(
            0.0,
            (
                0.35 * context_precision
                + 0.25 * context_recall
                + 0.2 * average_similarity
                + 0.15 * citation_coverage
                - latency_penalty
                - cost_penalty
            ),
        )
    return {
        "context_precision": round(context_precision, 6),
        "context_recall": round(context_recall, 6),
        "average_similarity": round(average_similarity, 6),
        "irrelevant_chunk_rate": round(irrelevant_rate, 6),
        "citation_coverage": round(citation_coverage, 6),
        "rbac_leakage_count": rbac_leakage_count,
        "latency_ms": latency_ms,
        "estimated_cost": estimated_cost,
        "overall_score": round(overall_score, 6),
        "warnings": warnings,
    }
