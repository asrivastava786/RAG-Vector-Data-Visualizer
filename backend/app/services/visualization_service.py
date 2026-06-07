from __future__ import annotations

import math
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.chunk import Chunk
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
from app.services.embedding_service import get_embedding_provider
from app.services.rbac_service import get_workspace_membership


def scatter_for_query_run(
    db: Session,
    *,
    query_run_id: uuid.UUID,
    user: User,
) -> ScatterResponse:
    query_run = _get_accessible_query_run(db, query_run_id=query_run_id, user=user)
    chunks = _retrieved_chunks(query_run)
    pca_response = _pca_scatter(db, query_run=query_run, chunks=chunks)
    if pca_response is not None:
        return pca_response
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
    return ScatterResponse(
        points=points,
        projection_method="score_space",
        x_axis_label="Dense score",
        y_axis_label="Sparse score",
    )


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


def _pca_scatter(db: Session, *, query_run: QueryRun, chunks: list[dict]) -> ScatterResponse | None:
    chunk_ids = [uuid.UUID(str(chunk["id"])) for chunk in chunks if chunk.get("id")]
    if not chunk_ids:
        return None
    chunk_records = db.scalars(
        select(Chunk).where(
            Chunk.workspace_id == query_run.workspace_id,
            Chunk.project_id == query_run.project_id,
            Chunk.id.in_(chunk_ids),
        )
    ).all()
    chunks_by_id = {str(chunk.id): chunk for chunk in chunk_records if chunk.embedding is not None}
    if len(chunks_by_id) < 2:
        return None

    provider = get_embedding_provider()
    vectors = [provider.embed_text(query_run.query)]
    labels = [
        {
            "id": "query",
            "type": "query",
            "label": _label(query_run.query, 40),
            "score": 1.0,
            "cluster": "query",
            "metadata": {"query_run_id": str(query_run.id)},
        }
    ]
    for chunk in chunks:
        record = chunks_by_id.get(str(chunk.get("id")))
        if record is None or record.embedding is None:
            continue
        vectors.append(list(record.embedding))
        scores = chunk.get("scores", {})
        labels.append(
            {
                "id": f"chunk_{chunk.get('id')}",
                "type": "chunk",
                "label": _label(chunk.get("section_heading") or chunk.get("text") or "Chunk", 42),
                "score": round(float(scores.get("hybrid_score", 0.0) or 0.0), 6),
                "cluster": _cluster_for_chunk(chunk),
                "metadata": {
                    "chunk_id": chunk.get("id"),
                    "document_id": chunk.get("document_id"),
                    "chunk_index": chunk.get("chunk_index"),
                    "token_count": chunk.get("token_count"),
                    "allowed_roles": chunk.get("allowed_roles", []),
                    "tags": chunk.get("tags", []),
                },
            }
        )
    if len(vectors) < 3:
        return None

    coordinates = _project_pca_2d(vectors)
    if coordinates is None:
        return None
    points = [
        ScatterPoint(
            id=str(label["id"]),
            type=str(label["type"]),
            label=str(label["label"]),
            x=x,
            y=y,
            score=float(label["score"]),
            cluster=str(label["cluster"]),
            metadata=dict(label["metadata"]),
        )
        for label, (x, y) in zip(labels, coordinates, strict=True)
    ]
    return ScatterResponse(
        points=points,
        projection_method="pca",
        x_axis_label="PC1",
        y_axis_label="PC2",
    )


def _project_pca_2d(vectors: list[list[float]]) -> list[tuple[float, float]] | None:
    dimensions = len(vectors[0])
    if dimensions == 0 or any(len(vector) != dimensions for vector in vectors):
        return None
    means = [sum(vector[index] for vector in vectors) / len(vectors) for index in range(dimensions)]
    centered = [[value - means[index] for index, value in enumerate(vector)] for vector in vectors]
    first = _principal_component(centered)
    if first is None:
        return None
    first_scores = [_dot(row, first) for row in centered]
    residual = [
        [value - first_scores[row_index] * first[col_index] for col_index, value in enumerate(row)]
        for row_index, row in enumerate(centered)
    ]
    second = _principal_component(residual)
    if second is None:
        return None
    raw_coordinates = [(_dot(row, first), _dot(row, second)) for row in centered]
    return _scale_coordinates(raw_coordinates)


def _principal_component(rows: list[list[float]]) -> list[float] | None:
    dimensions = len(rows[0])
    component = [1.0 / math.sqrt(dimensions)] * dimensions
    for _ in range(16):
        multiplied = _covariance_multiply(rows, component)
        norm = math.sqrt(sum(value * value for value in multiplied))
        if norm < 1e-12:
            return None
        component = [value / norm for value in multiplied]
    return component


def _covariance_multiply(rows: list[list[float]], vector: list[float]) -> list[float]:
    row_scores = [_dot(row, vector) for row in rows]
    return [
        sum(row[column] * score for row, score in zip(rows, row_scores, strict=True))
        for column in range(len(vector))
    ]


def _scale_coordinates(coordinates: list[tuple[float, float]]) -> list[tuple[float, float]]:
    max_abs = max((abs(value) for coordinate in coordinates for value in coordinate), default=0.0)
    if max_abs < 1e-12:
        return [(0.0, 0.0) for _ in coordinates]
    return [(round(x / max_abs, 6), round(y / max_abs, 6)) for x, y in coordinates]


def _dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


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
