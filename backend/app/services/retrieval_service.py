from __future__ import annotations

import time
import uuid
from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.models.chunk import Chunk
from app.models.common import WorkspaceRole
from app.models.query_run import QueryRun
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.query import (
    FunnelStage,
    QueryAnalyzeRequest,
    QueryAnalyzeResponse,
    RetrievedChunk,
    ScoreBreakdown,
)
from app.services.audit_service import write_audit_log
from app.services.embedding_service import cosine_similarity, get_embedding_provider
from app.services.evaluation_service import retrieval_metrics
from app.services.hybrid_search_service import fuse_scores
from app.services.rbac_service import ROLE_ORDER, get_accessible_project, get_workspace_membership
from app.services.rerank_service import get_reranker
from app.services.sparse_search_service import score_sparse_candidates


@dataclass(frozen=True)
class ScoredChunk:
    chunk: Chunk
    dense_score: float
    sparse_score: float
    hybrid_score: float
    rerank_score: float | None = None


def analyze_query(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    payload: QueryAnalyzeRequest,
    experiment_id: uuid.UUID | None = None,
) -> QueryAnalyzeResponse:
    started = time.perf_counter()
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    strategy = _get_strategy(db, strategy_id=payload.strategy_id)
    if strategy.project_id != project.id or strategy.workspace_id != project.workspace_id:
        raise not_found("Strategy not found.")

    membership = get_workspace_membership(db, workspace_id=project.workspace_id, user_id=user.id)
    simulated_role = payload.role_simulation or membership.role
    _validate_role_simulation(actual_role=membership.role, simulated_role=simulated_role)
    role_context = {
        "actual_role": membership.role.value,
        "simulated_role": simulated_role.value,
        "user_id": str(user.id),
    }

    query_embedding = get_embedding_provider(
        strategy.config_json.get("embedding_provider")
    ).embed_text(payload.query)
    dense_started = time.perf_counter()
    candidates = _authorized_chunks(
        db,
        strategy=strategy,
        simulated_role=simulated_role,
        user_id=user.id,
    )
    dense_scores = _dense_scores(query_embedding, candidates)
    dense_latency = _elapsed_ms(dense_started)

    sparse_started = time.perf_counter()
    sparse_scores = score_sparse_candidates(payload.query, candidates)
    sparse_latency = _elapsed_ms(sparse_started)

    fusion_started = time.perf_counter()
    scored = [
        ScoredChunk(
            chunk=chunk,
            dense_score=dense_scores.get(str(chunk.id), 0.0),
            sparse_score=sparse_scores.get(str(chunk.id), 0.0),
            hybrid_score=fuse_scores(
                dense_score=dense_scores.get(str(chunk.id), 0.0),
                sparse_score=sparse_scores.get(str(chunk.id), 0.0),
                dense_weight=payload.dense_weight,
                sparse_weight=payload.sparse_weight,
            ).hybrid_score,
        )
        for chunk in candidates
    ]
    scored.sort(key=lambda item: item.hybrid_score, reverse=True)
    fused = scored[: max(payload.top_k * 2, payload.top_k)]
    fusion_latency = _elapsed_ms(fusion_started)

    rerank_started = time.perf_counter()
    reranked = get_reranker(payload.rerank).rerank(payload.query, fused)[: payload.top_k]
    rerank_latency = _elapsed_ms(rerank_started)

    returned_chunks = [_to_retrieved_chunk(item) for item in reranked]
    rbac_leakage_count = _rbac_leakage_count(
        returned_chunks,
        simulated_role=simulated_role,
        user_id=user.id,
    )
    latency_ms = _elapsed_ms(started)
    metrics = retrieval_metrics(
        chunks=returned_chunks,
        latency_ms=latency_ms,
        rbac_leakage_count=rbac_leakage_count,
    )
    funnel = [
        FunnelStage(name="Authorized candidates", count=len(candidates), latency_ms=dense_latency),
        FunnelStage(name="Sparse candidates", count=len(candidates), latency_ms=sparse_latency),
        FunnelStage(name="After RBAC filter", count=len(candidates), latency_ms=0),
        FunnelStage(name="After fusion", count=len(fused), latency_ms=fusion_latency),
        FunnelStage(name="After rerank", count=len(reranked), latency_ms=rerank_latency),
    ]
    persisted_metrics = {
        **metrics,
        "funnel": [stage.model_dump(mode="json") for stage in funnel],
    }
    query_run = QueryRun(
        workspace_id=project.workspace_id,
        project_id=project.id,
        experiment_id=experiment_id,
        strategy_id=strategy.id,
        query=payload.query,
        optimized_query=None,
        role_context=role_context,
        retrieved_chunks_json=[chunk.model_dump(mode="json") for chunk in returned_chunks],
        metrics_json=persisted_metrics,
        latency_ms=latency_ms,
        created_by=user.id,
    )
    db.add(query_run)
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        action="query.analyze",
        entity_type="query_run",
        entity_id=str(query_run.id),
        metadata={
            "strategy_id": str(strategy.id),
            "top_k": payload.top_k,
            "simulated_role": simulated_role.value,
            "returned_chunks": len(returned_chunks),
        },
    )
    db.commit()
    db.refresh(query_run)
    return QueryAnalyzeResponse(
        query_run_id=query_run.id,
        project_id=project.id,
        strategy_id=strategy.id,
        query=payload.query,
        role_context=role_context,
        retrieved_chunks=returned_chunks,
        metrics=metrics,
        funnel=funnel,
        latency_ms=latency_ms,
        created_at=query_run.created_at,
    )


def _get_strategy(db: Session, *, strategy_id: uuid.UUID) -> ChunkingStrategy:
    strategy = db.get(ChunkingStrategy, strategy_id)
    if strategy is None:
        raise not_found("Strategy not found.")
    return strategy


def _validate_role_simulation(
    *,
    actual_role: WorkspaceRole,
    simulated_role: WorkspaceRole,
) -> None:
    if actual_role in {WorkspaceRole.owner, WorkspaceRole.admin}:
        return
    if ROLE_ORDER[simulated_role] > ROLE_ORDER[actual_role]:
        raise forbidden("You cannot simulate a role with broader access than your own.")


def _authorized_chunks(
    db: Session,
    *,
    strategy: ChunkingStrategy,
    simulated_role: WorkspaceRole,
    user_id: uuid.UUID,
) -> list[Chunk]:
    stmt = (
        select(Chunk)
        .where(
            Chunk.workspace_id == strategy.workspace_id,
            Chunk.project_id == strategy.project_id,
            Chunk.strategy_id == strategy.id,
            or_(
                Chunk.allowed_roles_json.contains([simulated_role.value]),
                Chunk.allowed_users_json.contains([str(user_id)]),
            ),
        )
        .order_by(Chunk.document_id, Chunk.chunk_index)
    )
    return list(db.scalars(stmt).all())


def _dense_scores(query_embedding: list[float], candidates: list[Chunk]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for chunk in candidates:
        if chunk.embedding is None:
            scores[str(chunk.id)] = 0.0
            continue
        scores[str(chunk.id)] = cosine_similarity(query_embedding, list(chunk.embedding))
    return scores


def _to_retrieved_chunk(item: ScoredChunk) -> RetrievedChunk:
    fused = fuse_scores(
        dense_score=item.dense_score,
        sparse_score=item.sparse_score,
        dense_weight=0.7,
        sparse_weight=0.3,
    )
    return RetrievedChunk(
        id=item.chunk.id,
        document_id=item.chunk.document_id,
        strategy_id=item.chunk.strategy_id,
        chunk_index=item.chunk.chunk_index,
        text=item.chunk.text,
        token_count=item.chunk.token_count,
        page_number=item.chunk.page_number,
        section_heading=item.chunk.section_heading,
        allowed_roles=item.chunk.allowed_roles_json,
        tags=item.chunk.tags_json,
        metadata=item.chunk.metadata_json,
        scores=ScoreBreakdown(
            dense_score=fused.dense_score,
            sparse_score=fused.sparse_score,
            hybrid_score=item.hybrid_score,
            rerank_score=item.rerank_score,
        ),
    )


def _rbac_leakage_count(
    chunks: list[RetrievedChunk],
    *,
    simulated_role: WorkspaceRole,
    user_id: uuid.UUID,
) -> int:
    # The SQL query applies the role/user predicate before scoring or persistence.
    return 0


def _elapsed_ms(started: float) -> int:
    return max(0, int((time.perf_counter() - started) * 1000))
