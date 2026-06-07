import uuid

from pydantic import BaseModel, Field

from app.models.common import WorkspaceRole
from app.schemas.query import QueryMetrics


class RBACSimulationRequest(BaseModel):
    strategy_id: uuid.UUID
    query: str = Field(min_length=2, max_length=2000)
    role_simulation: WorkspaceRole
    top_k: int = Field(default=5, ge=1, le=50)


class RBACChunkAccess(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    section_heading: str | None
    token_count: int
    allowed_roles: list[str]
    tags: list[str]
    access: str
    text_preview: str | None = None
    warnings: list[str] = Field(default_factory=list)


class RBACSimulationResponse(BaseModel):
    project_id: uuid.UUID
    strategy_id: uuid.UUID
    role_simulation: WorkspaceRole
    allowed_chunks: list[RBACChunkAccess]
    blocked_chunks: list[RBACChunkAccess]
    retrieved_chunk_ids: list[uuid.UUID]
    leakage_count: int
    mixed_permission_warnings: list[str]
    metrics: QueryMetrics


class RBACMatrixRow(BaseModel):
    entity_id: uuid.UUID
    entity_type: str
    label: str
    allowed_roles: list[str]
    tags: list[str]
    role_access: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)


class RBACMatrixResponse(BaseModel):
    project_id: uuid.UUID
    rows: list[RBACMatrixRow]
