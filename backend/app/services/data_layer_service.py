from __future__ import annotations

import uuid
from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.models.query_run import QueryRun
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.data_layer import (
    DataLayerProjectFacts,
    DataLayerRecommendationResponse,
    DataLayerRoutingRule,
    DataLayerStoreRecommendation,
)
from app.services.rbac_service import get_accessible_project


def data_layer_recommendation_for_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
) -> DataLayerRecommendationResponse:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    documents = db.scalars(
        select(Document).where(Document.workspace_id == project.workspace_id, Document.project_id == project.id)
    ).all()
    chunk_rows = db.scalars(
        select(Chunk).where(Chunk.workspace_id == project.workspace_id, Chunk.project_id == project.id)
    ).all()
    strategy_count = db.scalar(
        select(func.count())
        .select_from(ChunkingStrategy)
        .where(ChunkingStrategy.workspace_id == project.workspace_id, ChunkingStrategy.project_id == project.id)
    ) or 0
    query_run_count = db.scalar(
        select(func.count())
        .select_from(QueryRun)
        .where(QueryRun.workspace_id == project.workspace_id, QueryRun.project_id == project.id)
    ) or 0

    facts = _facts(
        documents=documents,
        chunks=chunk_rows,
        strategy_count=int(strategy_count),
        query_run_count=int(query_run_count),
    )
    stores = _store_recommendations(facts)
    warnings = _warnings(facts)
    return DataLayerRecommendationResponse(
        project_id=str(project.id),
        facts=facts,
        recommended_architecture=_architecture_label(facts),
        stores=stores,
        routing_rules=_routing_rules(facts),
        efficiency_recommendations=_efficiency_recommendations(facts),
        governance_rules=[
            "Keep workspace_id and project_id as mandatory relational partition keys for every entity.",
            "Apply allowed_roles and allowed_users before vector, graph, report, or prompt payloads are emitted.",
            "Store raw documents and extracted text lineage in relational/object storage; never duplicate full source text in graph nodes.",
            "Treat graph and vector indexes as derived projections that can be rebuilt from relational source-of-truth records.",
        ],
        warnings=warnings,
    )


def _facts(
    *,
    documents: list[Document],
    chunks: list[Chunk],
    strategy_count: int,
    query_run_count: int,
) -> DataLayerProjectFacts:
    content_types = Counter(document.content_type for document in documents)
    token_total = sum(chunk.token_count for chunk in chunks)
    access_profiles = {
        (
            tuple(sorted(chunk.allowed_roles_json or [])),
            tuple(sorted(chunk.allowed_users_json or [])),
        )
        for chunk in chunks
    }
    mixed_access_count = sum(1 for chunk in chunks if len(chunk.allowed_roles_json or []) > 1 or chunk.allowed_users_json)
    return DataLayerProjectFacts(
        document_count=len(documents),
        processed_document_count=sum(1 for document in documents if document.status == "processed"),
        chunk_count=len(chunks),
        strategy_count=strategy_count,
        query_run_count=query_run_count,
        content_types=dict(content_types),
        average_chunk_tokens=round(token_total / len(chunks), 2) if chunks else 0.0,
        chunks_with_embeddings=sum(1 for chunk in chunks if chunk.embedding is not None),
        chunks_with_section_headings=sum(1 for chunk in chunks if chunk.section_heading),
        chunks_with_tags=sum(1 for chunk in chunks if chunk.tags_json),
        distinct_access_profiles=len(access_profiles),
        mixed_access_chunk_count=mixed_access_count,
    )


def _store_recommendations(facts: DataLayerProjectFacts) -> list[DataLayerStoreRecommendation]:
    vector_fit = 0.35
    if facts.chunks_with_embeddings:
        vector_fit += 0.3
    if facts.query_run_count:
        vector_fit += 0.15
    if facts.chunk_count >= 50:
        vector_fit += 0.15

    graph_fit = 0.25
    if facts.chunks_with_section_headings:
        graph_fit += 0.2
    if facts.chunks_with_tags:
        graph_fit += 0.15
    if facts.distinct_access_profiles > 1:
        graph_fit += 0.15
    if facts.query_run_count:
        graph_fit += 0.1

    relational_fit = 0.8
    if facts.distinct_access_profiles:
        relational_fit += 0.1
    if facts.query_run_count:
        relational_fit += 0.05

    return [
        DataLayerStoreRecommendation(
            store="relational",
            role="System of record and policy enforcement plane",
            fit_score=round(min(relational_fit, 1.0), 2),
            primary_entities=[
                "workspaces",
                "users",
                "projects",
                "documents",
                "chunk metadata",
                "strategies",
                "query runs",
                "audit logs",
            ],
            indexing_strategy=[
                "Composite indexes on workspace_id, project_id, strategy_id, and document_id.",
                "JSONB GIN indexes for tags, allowed_roles, and metadata facets when volume grows.",
                "Foreign-key lineage from document to chunk to query result for reproducible reports.",
            ],
            rationale=[
                "RBAC and multi-tenant isolation are deterministic joins and filters.",
                "Experiment metrics, audit logs, and exports need transactional consistency.",
            ],
            risks=["Avoid placing authorization state only inside vector metadata."],
        ),
        DataLayerStoreRecommendation(
            store="vector",
            role="Semantic retrieval and similarity optimization plane",
            fit_score=round(min(vector_fit, 1.0), 2),
            primary_entities=["chunk embeddings", "query embeddings", "strategy-specific vector indexes"],
            indexing_strategy=[
                "Maintain one vector namespace per workspace/project/strategy.",
                "Filter by workspace_id, project_id, strategy_id, allowed_roles, and allowed_users before returning candidates.",
                "Track embedding provider, dimensions, model version, and chunking strategy in relational metadata.",
            ],
            rationale=[
                "Dense search is the right fit for query-to-chunk semantic similarity.",
                "Strategy comparison depends on repeatable embedding projections per chunking strategy.",
            ],
            risks=["Embedding drift requires reindex jobs and versioned indexes."],
        ),
        DataLayerStoreRecommendation(
            store="graph",
            role="Lineage, citation, section, entity, and permission relationship plane",
            fit_score=round(min(graph_fit, 1.0), 2),
            primary_entities=[
                "document-section-chunk edges",
                "query-to-result edges",
                "citation paths",
                "role-to-document access edges",
                "tag/topic clusters",
            ],
            indexing_strategy=[
                "Represent graph nodes with stable relational IDs, not duplicated source text.",
                "Materialize edges from document structure, chunk metadata, query runs, citations, and RBAC profiles.",
                "Use graph traversal for impact analysis, leakage risk paths, and citation explainability.",
            ],
            rationale=[
                "Visual debugging benefits from explicit relationships beyond vector distance.",
                "RBAC safety analysis can show blocked paths and mixed-permission boundaries.",
            ],
            risks=["Graph should be a derived projection; keep relational records authoritative."],
        ),
    ]


def _routing_rules(facts: DataLayerProjectFacts) -> list[DataLayerRoutingRule]:
    rules = [
        DataLayerRoutingRule(
            data_domain="tenant, user, role, project, strategy, and audit records",
            primary_store="relational",
            secondary_stores=[],
            reason="Requires strong consistency, access control, and workspace isolation.",
            sync_pattern="transactional write",
        ),
        DataLayerRoutingRule(
            data_domain="document binaries",
            primary_store="object storage",
            secondary_stores=["relational"],
            reason="Large immutable files belong in object storage with relational lineage and access policy metadata.",
            sync_pattern="write object first, then commit storage_key and metadata",
        ),
        DataLayerRoutingRule(
            data_domain="chunk text, offsets, source pages, headings, tags, and RBAC metadata",
            primary_store="relational",
            secondary_stores=["vector", "graph"],
            reason="Chunks need deterministic filtering plus derived semantic and relationship projections.",
            sync_pattern="relational commit followed by async projection jobs",
        ),
        DataLayerRoutingRule(
            data_domain="chunk and query embeddings",
            primary_store="vector",
            secondary_stores=["relational"],
            reason="High-dimensional similarity search is optimized in the vector plane.",
            sync_pattern="async index/update with relational embedding_version marker",
        ),
        DataLayerRoutingRule(
            data_domain="document-section-chunk, query-result, citation, and access relationships",
            primary_store="graph",
            secondary_stores=["relational"],
            reason="Traversals and visual explainability are more efficient as explicit relationships.",
            sync_pattern="event/materialized projection from relational records",
        ),
    ]
    if facts.query_run_count:
        rules.append(
            DataLayerRoutingRule(
                data_domain="retrieval experiments and result leaderboards",
                primary_store="relational",
                secondary_stores=["graph"],
                reason="Metrics are tabular, while result paths and citation chains benefit from graph projection.",
                sync_pattern="transactional metric write with graph edge projection",
            )
        )
    return rules


def _efficiency_recommendations(facts: DataLayerProjectFacts) -> list[str]:
    recommendations = [
        "Use relational storage as the source of truth; rebuild vector and graph projections from project-scoped records.",
        "Partition every derived index by workspace_id, project_id, and strategy_id to prevent cross-tenant candidate bleed.",
    ]
    if facts.chunk_count == 0:
        recommendations.append("Upload, process, and index documents before making vector or graph stores authoritative.")
    if facts.chunks_with_embeddings < facts.chunk_count:
        recommendations.append("Backfill missing embeddings before relying on dense retrieval comparisons.")
    if facts.distinct_access_profiles > 1:
        recommendations.append("Keep RBAC metadata in relational records and duplicate only filterable policy facets into vector metadata.")
    if facts.chunks_with_section_headings or facts.chunks_with_tags:
        recommendations.append("Project section headings and tags into graph edges for faster visual traversal and cluster explainability.")
    if facts.query_run_count:
        recommendations.append("Persist query-to-chunk result edges in graph storage to power before/after retrieval debugging views.")
    return recommendations


def _warnings(facts: DataLayerProjectFacts) -> list[str]:
    warnings: list[str] = []
    if facts.document_count == 0:
        warnings.append("No documents are available, so recommendations are based on the target architecture only.")
    if facts.processed_document_count < facts.document_count:
        warnings.append("Some documents are not processed; chunk and relationship recommendations may change after extraction.")
    if facts.chunk_count and facts.chunks_with_embeddings == 0:
        warnings.append("Chunks exist without embeddings; vector storage is not ready for semantic retrieval.")
    if facts.mixed_access_chunk_count:
        warnings.append("Mixed-access chunks exist; graph and vector projections must preserve RBAC facets exactly.")
    return warnings


def _architecture_label(facts: DataLayerProjectFacts) -> str:
    if facts.chunk_count == 0:
        return "Relational-first foundation with vector and graph projections pending indexing"
    if facts.distinct_access_profiles > 1 or facts.chunks_with_section_headings:
        return "Relational source of truth with filtered vector retrieval and graph explainability overlay"
    return "Relational source of truth with vector retrieval projection"
