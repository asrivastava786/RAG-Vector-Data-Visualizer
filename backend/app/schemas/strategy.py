import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class StrategyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    splitter_type: str = Field(
        default="recursive",
        pattern="^(fixed|recursive|heading|semantic|table_aware)$",
    )
    chunk_size: int = Field(default=600, ge=50, le=4000)
    overlap: int = Field(default=100, ge=0, le=1000)
    preserve_headings: bool = True
    preserve_tables: bool = True
    semantic_threshold: float | None = Field(default=None, ge=0.0, le=1.0)
    config_json: dict = Field(default_factory=dict)


class StrategyRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    splitter_type: str
    chunk_size: int
    overlap: int
    preserve_headings: bool
    preserve_tables: bool
    semantic_threshold: float | None
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategyIndexResponse(BaseModel):
    strategy_id: uuid.UUID
    documents_indexed: int
    chunks_created: int
    chunks_deleted: int
    warnings: list[str] = Field(default_factory=list)
