import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import bad_request
from app.models.chunk import Chunk
from app.models.common import WorkspaceRole
from app.models.document import Document
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.query import QueryAnalyzeRequest
from app.schemas.rbac import (
    RBACChunkAccess,
    RBACMatrixResponse,
    RBACMatrixRow,
    RBACSimulationRequest,
    RBACSimulationResponse,
)
from app.services.rbac_service import ROLE_ORDER, get_accessible_project, get_workspace_membership
from app.services.retrieval_service import analyze_query


def simulate_rbac(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    payload: RBACSimulationRequest,
) -> RBACSimulationResponse:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    membership = get_workspace_membership(db, workspace_id=project.workspace_id, user_id=user.id)
    if ROLE_ORDER[membership.role] < ROLE_ORDER[WorkspaceRole.analyst]:
        raise bad_request("Viewer role cannot run RBAC simulations.")
    strategy = db.get(ChunkingStrategy, payload.strategy_id)
    if strategy is None or strategy.project_id != project.id:
        raise bad_request("Strategy does not belong to this project.")
    chunks = list(
        db.scalars(
            select(Chunk)
            .where(
                Chunk.workspace_id == project.workspace_id,
                Chunk.project_id == project.id,
                Chunk.strategy_id == strategy.id,
            )
            .order_by(Chunk.document_id, Chunk.chunk_index)
        ).all()
    )
    allowed = [chunk for chunk in chunks if _role_can_access(chunk, payload.role_simulation)]
    blocked = [chunk for chunk in chunks if not _role_can_access(chunk, payload.role_simulation)]
    analysis = analyze_query(
        db,
        project_id=project.id,
        user=user,
        payload=QueryAnalyzeRequest(
            query=payload.query,
            strategy_id=strategy.id,
            top_k=payload.top_k,
            role_simulation=payload.role_simulation,
        ),
    )
    retrieved_ids = [chunk.id for chunk in analysis.retrieved_chunks]
    blocked_ids = {chunk.id for chunk in blocked}
    leakage = len([chunk_id for chunk_id in retrieved_ids if chunk_id in blocked_ids])
    mixed = [
        f"Chunk {chunk.chunk_index + 1} mixes role and explicit-user permissions."
        for chunk in chunks
        if chunk.allowed_roles_json and chunk.allowed_users_json
    ]
    return RBACSimulationResponse(
        project_id=project.id,
        strategy_id=strategy.id,
        role_simulation=payload.role_simulation,
        allowed_chunks=[
            _chunk_access(chunk, access="allowed", include_preview=True) for chunk in allowed
        ],
        blocked_chunks=[
            _chunk_access(chunk, access="blocked", include_preview=False) for chunk in blocked
        ],
        retrieved_chunk_ids=retrieved_ids,
        leakage_count=leakage,
        mixed_permission_warnings=mixed,
        metrics=analysis.metrics,
    )


def rbac_matrix(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
) -> RBACMatrixResponse:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    get_workspace_membership(db, workspace_id=project.workspace_id, user_id=user.id)
    documents = list(
        db.scalars(
            select(Document)
            .where(Document.workspace_id == project.workspace_id, Document.project_id == project.id)
            .order_by(Document.created_at.desc())
        ).all()
    )
    def warnings_for(document: Document) -> list[str]:
        if document.allowed_roles_json and document.allowed_users_json:
            return ["mixed_access"]
        return []

    rows = [
        RBACMatrixRow(
            entity_id=document.id,
            entity_type="document",
            label=document.title,
            allowed_roles=document.allowed_roles_json,
            tags=document.tags_json,
            role_access={
                role.value: role.value in document.allowed_roles_json for role in WorkspaceRole
            },
            warnings=warnings_for(document),
        )
        for document in documents
    ]
    return RBACMatrixResponse(project_id=project.id, rows=rows)


def _role_can_access(chunk: Chunk, role: WorkspaceRole) -> bool:
    return role.value in chunk.allowed_roles_json


def _chunk_access(chunk: Chunk, *, access: str, include_preview: bool) -> RBACChunkAccess:
    warnings = chunk.metadata_json.get("warnings", [])
    return RBACChunkAccess(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        chunk_index=chunk.chunk_index,
        section_heading=chunk.section_heading,
        token_count=chunk.token_count,
        allowed_roles=chunk.allowed_roles_json,
        tags=chunk.tags_json,
        access=access,
        text_preview=chunk.text[:320] if include_preview else None,
        warnings=warnings if isinstance(warnings, list) else [],
    )
