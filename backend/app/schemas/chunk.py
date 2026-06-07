import uuid
from datetime import datetime

from pydantic import BaseModel


class ChunkRead(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    strategy_id: uuid.UUID
    chunk_index: int
    text: str
    token_count: int
    page_number: int | None
    section_heading: str | None
    start_offset: int
    end_offset: int
    allowed_roles_json: list[str]
    allowed_users_json: list[str]
    tags_json: list[str]
    metadata_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
