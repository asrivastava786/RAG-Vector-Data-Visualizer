import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import WorkspaceRole


class DocumentMetadata(BaseModel):
    source: str | None = None
    department: str | None = None
    sensitivity: str | None = None


class DocumentUploadForm(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    allowed_roles: list[WorkspaceRole] = Field(default_factory=list)
    allowed_user_ids: list[uuid.UUID] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)


class DocumentRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    filename: str
    content_type: str
    status: str
    metadata_json: dict
    allowed_roles_json: list[str]
    allowed_users_json: list[str]
    tags_json: list[str]
    page_count: int | None
    updated_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentDetail(DocumentRead):
    extracted_text: str | None
    preview: dict


class DocumentProcessResponse(BaseModel):
    id: uuid.UUID
    status: str
    extracted_characters: int
    page_count: int | None
    warnings: list[str] = Field(default_factory=list)
