import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.common import WorkspaceRole


class AdminUserRead(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    workspace_id: uuid.UUID
    role: WorkspaceRole
    joined_at: datetime


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    role: WorkspaceRole | None = None


class AuditLogRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID | None
    user_id: uuid.UUID | None
    action: str
    entity_type: str
    entity_id: str | None
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSettingsResponse(BaseModel):
    embedding_providers: list[str]
    storage_provider: str
    api_keys_placeholder: str
    rate_limiting: str
