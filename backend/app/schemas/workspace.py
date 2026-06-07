import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import WorkspaceRole


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=180)
    slug: str | None = Field(default=None, max_length=120)


class WorkspaceRead(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    owner_user_id: uuid.UUID
    created_at: datetime
    current_user_role: WorkspaceRole

    model_config = {"from_attributes": True}


class WorkspaceMemberRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    role: WorkspaceRole
    created_at: datetime

    model_config = {"from_attributes": True}

