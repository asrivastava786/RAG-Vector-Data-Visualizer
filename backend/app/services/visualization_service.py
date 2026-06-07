from __future__ import annotations

import math
import uuid

from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.query_run import QueryRun
from app.models.user import User
from app.schemas.query import (
    FunnelResponse,
    FunnelStage,
    GraphEdge,
    GraphNode,
    GraphResponse,
    ScatterPoint,
    ScatterResponse,
)
from app.services.rbac_service import get_workspace_membership


def scatter_for_query_run(
    db: Session,
    *,
    query_run_id: uuid.UUID,
    user: User,
) -> ScatterResponse:
    query_run = _get_accessible_query_run(db, query_run_id=query_run_id, user=user)
    chunks = _retrieved_chunks(query_run)
    points = [
        ScatterPoint(
            id="query",
            type="query",
            label=_label(query_run.query, 40),
            x=0.0,
            y=0.0,
            score=1.0,
            cluster="query",
            metadata={"query_run_id": str(query_run.id)},
        )
    ]
    for index, chunk in enumerate(chunks):
        scores = chunk.get("scores", {})
        dense = float(scores.get("dense_score", 0.0) or 0.0)
        sparse = float(scores.get("sparse_score", 0.0) or 0.0)
        hybrid = float(scores.get("hybrid_score", 0.0) or 0.0)
        angle = (index + 1) * 0.85
        radius = max(0.15, 1.0 - hybrid)
        cluster = _cluster_for_chunk(chunk)
        points.append(
            ScatterPoint(
                id=f"chunk_{chunk.get('id')}",
                type="chunk",
                label=_label(chunk.get("section_heading") or chunk.get("text") or "Chunk", 42),
                x=round(dense + math.cos(angle) * radius, 6),
                y=round(sparse + math.sin(angle) * radius, 6),
                score=round(hybrid, 6),
                cluster=cluster,
                metadata={
                    "chunk_id": chunk.get("id"),
                    "document_id": chunk.get("document_id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "token_count": chunk.get("token_count"),
                    "allowed_roles": chunk.get("allowed_roles", []),
                    "tags": chunk.get("tags", []),
                },
            )
        )
    return ScatterResponse(points=points)


def graph_for_query_run(
    db: Session,
    *,
    query_run_id: uuid.UUID,
    user: User,
) -> GraphResponse:
    query_run = _get_accessible_query_run(db, query_run_id=query_run_id, user=user)
    chunks = _retrieved_chunks(query_run)
    nodes = [
        GraphNode(
            id="query",
            type="query",
            label=_label(query_run.query, 60),
            metadata={"query_run_id": str(query_run.id)},
        )
    ]
    edges: list[GraphEdge] = []
    document_nodes: set[str] = set()
    for chunk in chunks:
        chunk_id = f"chunk_{chunk.get('id')}"
        document_id = f"document_{chunk.get('document_id')}"
        if document_id not in document_nodes:
            document_nodes.add(document_id)
            nodes.append(
                GraphNode(
                    id=document_id,
                    type="document",
                    label=_label(
                        str(chunk.get("metadata", {}).get("source_document_title", "Document")),
                        48,
                    ),
                    metadata={"document_id": chunk.get("document_id")},
                )
            )
        scores = chunk.get("scores", {})
        weight = round(float(scores.get("hybrid_score", 0.0) or 0.0), 6)
        nodes.append(
            GraphNode(
                id=chunk_id,
                type="chunk",
                label=_label(chunk.get("section_heading") or chunk.get("text") or "Chunk", 52),
                metadata={
                    "chunk_id": chunk.get("id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "allowed_roles": chunk.get("allowed_roles", []),
                },
            )
        )
        edges.append(
            GraphEdge(
                source="query",
                target=chunk_id,
                weight=weight,
                label=f"hybrid {weight:.2f}",
            )
        )
        edges.append(
            GraphEdge(
                source=document_id,
                target=chunk_id,
                weight=0.4,
                label="contains",
            )
        )
    return GraphResponse(nodes=nodes, edges=edges)


def funnel_for_query_run(
    db: Session,
    *,
    query_run_id: uuid.UUID,
    user: User,
) -> FunnelResponse:
    query_run = _get_accessible_query_run(db, query_run_id=query_run_id, user=user)
    raw_stages = query_run.metrics_json.get("funnel") or _fallback_funnel(query_run)
    return FunnelResponse(stages=[FunnelStage(**stage) for stage in raw_stages])


def _get_accessible_query_run(
    db: Session,
    *,
    query_run_id: uuid.UUID,
    user: User,
) -> QueryRun:
    query_run = db.get(QueryRun, query_run_id)
    if query_run is None:
        raise not_found("Query run not found.")
    get_workspace_membership(db, workspace_id=query_run.workspace_id, user_id=user.id)
    return query_run


def _retrieved_chunks(query_run: QueryRun) -> list[dict]:
    return list(query_run.retrieved_chunks_json or [])


def _cluster_for_chunk(chunk: dict) -> str:
    tags = chunk.get("tags") or []
    if isinstance(tags, list) and tags:
        return str(tags[0])
    heading = chunk.get("section_heading")
    return str(heading or "unclustered")


def _fallback_funnel(query_run: QueryRun) -> list[dict]:
    count = len(_retrieved_chunks(query_run))
    return [
        {"name": "Authorized candidates", "count": count, "latency_ms": query_run.latency_ms},
        {"name": "After RBAC filter", "count": count, "latency_ms": 0},
        {"name": "After fusion", "count": count, "latency_ms": 0},
        {"name": "After rerank", "count": count, "latency_ms": 0},
    ]


def _label(value: object, max_length: int) -> str:
    text = " ".join(str(value).split())
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 3]}..."
