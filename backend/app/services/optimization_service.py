from __future__ import annotations

from app.schemas.query import OptimizedQuery, QueryOptimizeResponse
from app.services.embedding_service import tokenize

DOMAIN_TERMS = {
    "hr": ["policy", "eligibility", "approval", "employee", "leave", "benefits"],
    "hr policy assistant": ["policy", "eligibility", "approval", "employee", "leave", "benefits"],
    "legal": ["clause", "termination", "liability", "obligation", "effective date"],
    "legal contract qa": ["clause", "termination", "liability", "obligation", "effective date"],
    "finance": ["report", "amount", "period", "variance", "invoice"],
    "finance reports": ["report", "amount", "period", "variance", "invoice"],
    "technical": ["api", "configuration", "deployment", "error", "endpoint"],
    "technical documentation": ["api", "configuration", "deployment", "error", "endpoint"],
}

SYNONYMS = {
    "leave": ["pto", "vacation", "absence"],
    "benefits": ["coverage", "eligibility"],
    "termination": ["cancellation", "end date"],
    "error": ["failure", "exception"],
    "invoice": ["bill", "payment"],
}


def optimize_query(query: str, use_case: str | None = None) -> QueryOptimizeResponse:
    cleaned = " ".join(query.strip().split())
    tokens = tokenize(cleaned)
    additions: list[str] = []
    for token in tokens:
        additions.extend(SYNONYMS.get(token, []))
    if len(tokens) < 5:
        additions.extend(_domain_terms(use_case))
    deduped = _dedupe([*tokens, *additions])
    expanded = " ".join(deduped)
    optimized = []
    if expanded and expanded != cleaned.lower():
        optimized.append(
            OptimizedQuery(
                query=expanded,
                method="rule_expansion",
                reason="Added deterministic synonyms and use-case retrieval terms.",
            )
        )
    optimized.append(
        OptimizedQuery(
            query=f"{cleaned} source section citation",
            method="citation_focus",
            reason="Added source and citation terms to favor attributable chunks.",
        )
    )
    return QueryOptimizeResponse(original_query=cleaned, optimized_queries=optimized)


def _domain_terms(use_case: str | None) -> list[str]:
    if not use_case:
        return []
    return DOMAIN_TERMS.get(use_case.lower().strip(), [])


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        normalized = value.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    return output
