import uuid
from dataclasses import dataclass, field

from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session

from app.core.errors import bad_request, not_found
from app.models.chunk import Chunk
from app.models.common import WorkspaceRole
from app.models.document import Document
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.strategy import StrategyCreate
from app.services.audit_service import write_audit_log
from app.services.chunking_service import ChunkerConfig, chunk_text
from app.services.document_service import user_can_access_document
from app.services.embedding_service import get_embedding_provider, sparse_terms, tokenize
from app.services.rbac_service import (
    ROLE_ORDER,
    get_accessible_project,
    get_workspace_membership,
    require_workspace_role,
)


@dataclass(frozen=True)
class IndexingResult:
    strategy_id: uuid.UUID
    documents_indexed: int
    chunks_created: int
    chunks_deleted: int
    warnings: list[str] = field(default_factory=list)


def create_strategy(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    payload: StrategyCreate,
) -> ChunkingStrategy:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    require_workspace_role(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.developer,
    )
    _validate_strategy_payload(payload)
    strategy = ChunkingStrategy(
        workspace_id=project.workspace_id,
        project_id=project.id,
        name=payload.name.strip(),
        splitter_type=payload.splitter_type,
        chunk_size=payload.chunk_size,
        overlap=payload.overlap,
        preserve_headings=payload.preserve_headings,
        preserve_tables=payload.preserve_tables,
        semantic_threshold=payload.semantic_threshold,
        config_json=payload.config_json,
        created_by=user.id,
    )
    db.add(strategy)
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        action="strategy.create",
        entity_type="chunking_strategy",
        entity_id=str(strategy.id),
        metadata={"splitter_type": strategy.splitter_type, "chunk_size": strategy.chunk_size},
    )
    db.commit()
    db.refresh(strategy)
    return strategy


def list_project_strategies(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
) -> list[ChunkingStrategy]:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    return list(
        db.scalars(
            select(ChunkingStrategy)
            .where(
                ChunkingStrategy.workspace_id == project.workspace_id,
                ChunkingStrategy.project_id == project.id,
            )
            .order_by(ChunkingStrategy.created_at.desc())
        ).all()
    )


def get_strategy_for_user(
    db: Session,
    *,
    strategy_id: uuid.UUID,
    user: User,
) -> ChunkingStrategy:
    strategy = db.get(ChunkingStrategy, strategy_id)
    if strategy is None:
        raise not_found("Strategy not found.")
    get_accessible_project(db, project_id=strategy.project_id, user_id=user.id)
    return strategy


def list_strategy_chunks(
    db: Session,
    *,
    strategy_id: uuid.UUID,
    user: User,
    limit: int = 100,
) -> list[Chunk]:
    strategy = get_strategy_for_user(db, strategy_id=strategy_id, user=user)
    membership = get_workspace_membership(db, workspace_id=strategy.workspace_id, user_id=user.id)
    stmt = (
        select(Chunk)
        .where(
            Chunk.workspace_id == strategy.workspace_id,
            Chunk.project_id == strategy.project_id,
            Chunk.strategy_id == strategy.id,
        )
        .order_by(Chunk.document_id, Chunk.chunk_index)
        .limit(min(max(limit, 1), 500))
    )
    if ROLE_ORDER[membership.role] < ROLE_ORDER[WorkspaceRole.admin]:
        stmt = stmt.where(
            or_(
                Chunk.allowed_roles_json.contains([membership.role.value]),
                Chunk.allowed_users_json.contains([str(user.id)]),
            )
        )
    return list(db.scalars(stmt).all())


def index_strategy(
    db: Session,
    *,
    strategy_id: uuid.UUID,
    user: User,
) -> IndexingResult:
    strategy = get_strategy_for_user(db, strategy_id=strategy_id, user=user)
    require_workspace_role(
        db,
        workspace_id=strategy.workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.developer,
    )
    config = _chunker_config(strategy)
    provider = get_embedding_provider(strategy.config_json.get("embedding_provider"))
    documents = list(
        db.scalars(
            select(Document)
            .where(
                Document.workspace_id == strategy.workspace_id,
                Document.project_id == strategy.project_id,
                Document.status == "processed",
                Document.extracted_text.is_not(None),
            )
            .order_by(Document.created_at.asc())
        ).all()
    )
    if not documents:
        raise bad_request("No processed documents are available for indexing.")

    delete_result = db.execute(
        delete(Chunk).where(
            Chunk.workspace_id == strategy.workspace_id,
            Chunk.project_id == strategy.project_id,
            Chunk.strategy_id == strategy.id,
        )
    )
    chunks_deleted = int(delete_result.rowcount or 0)
    warnings: list[str] = []
    chunks_created = 0
    documents_indexed = 0
    membership = get_workspace_membership(db, workspace_id=strategy.workspace_id, user_id=user.id)

    for document in documents:
        if not user_can_access_document(
            document,
            role=membership.role,
            user_id=user.id,
        ) and ROLE_ORDER[membership.role] < ROLE_ORDER[WorkspaceRole.admin]:
            continue
        candidates = chunk_text(document.extracted_text or "", config)
        if not candidates:
            warnings.append(f"Document '{document.title}' produced no chunks.")
            continue
        embeddings = provider.embed_batch([candidate.text for candidate in candidates])
        documents_indexed += 1
        for index, (candidate, embedding) in enumerate(zip(candidates, embeddings, strict=True)):
            chunk_warnings = list(candidate.warnings)
            if _has_mixed_access(document):
                chunk_warnings.append("mixed_access")
            terms = sparse_terms(candidate.text)
            db.add(
                Chunk(
                    workspace_id=strategy.workspace_id,
                    project_id=strategy.project_id,
                    document_id=document.id,
                    strategy_id=strategy.id,
                    chunk_index=index,
                    text=candidate.text,
                    embedding=embedding,
                    sparse_terms_json=terms,
                    token_count=max(1, len(tokenize(candidate.text))),
                    page_number=candidate.page_number,
                    section_heading=candidate.section_heading,
                    start_offset=candidate.start_offset,
                    end_offset=candidate.end_offset,
                    allowed_roles_json=document.allowed_roles_json,
                    allowed_users_json=document.allowed_users_json,
                    tags_json=document.tags_json,
                    metadata_json={
                        **candidate.metadata,
                        "warnings": chunk_warnings,
                        "source_document_title": document.title,
                    },
                )
            )
            chunks_created += 1
    write_audit_log(
        db,
        workspace_id=strategy.workspace_id,
        user_id=user.id,
        action="strategy.index",
        entity_type="chunking_strategy",
        entity_id=str(strategy.id),
        metadata={
            "documents_indexed": documents_indexed,
            "chunks_created": chunks_created,
            "chunks_deleted": chunks_deleted,
        },
    )
    db.commit()
    return IndexingResult(
        strategy_id=strategy.id,
        documents_indexed=documents_indexed,
        chunks_created=chunks_created,
        chunks_deleted=chunks_deleted,
        warnings=warnings,
    )


def _validate_strategy_payload(payload: StrategyCreate) -> None:
    if payload.overlap >= payload.chunk_size:
        raise bad_request("Chunk overlap must be smaller than chunk size.")
    if not payload.name.strip():
        raise bad_request("Strategy name is required.")


def _chunker_config(strategy: ChunkingStrategy) -> ChunkerConfig:
    return ChunkerConfig(
        splitter_type=strategy.splitter_type,
        chunk_size=strategy.chunk_size,
        overlap=strategy.overlap,
        preserve_headings=strategy.preserve_headings,
        preserve_tables=strategy.preserve_tables,
        semantic_threshold=strategy.semantic_threshold,
        config=strategy.config_json,
    )


def _has_mixed_access(document: Document) -> bool:
    return bool(document.allowed_roles_json and document.allowed_users_json)
