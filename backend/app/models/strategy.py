import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import jsonb_default_dict, uuid_pk


class ChunkingStrategy(Base):
    __tablename__ = "chunking_strategies"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(180), nullable=False)
    splitter_type: Mapped[str] = mapped_column(String(80), nullable=False)
    chunk_size: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    overlap: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    preserve_headings: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    preserve_tables: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    semantic_threshold: Mapped[float | None] = mapped_column(Float)
    config_json: Mapped[dict] = mapped_column(JSONB, default=jsonb_default_dict, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    project = relationship("Project", back_populates="strategies")
    creator = relationship("User")

