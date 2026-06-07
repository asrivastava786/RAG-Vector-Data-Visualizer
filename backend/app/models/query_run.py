import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import jsonb_default_dict, jsonb_default_list, uuid_pk


class QueryRun(Base):
    __tablename__ = "query_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    experiment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("experiments.id", ondelete="SET NULL")
    )
    strategy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chunking_strategies.id", ondelete="RESTRICT"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    optimized_query: Mapped[str | None] = mapped_column(Text)
    role_context: Mapped[dict] = mapped_column(JSONB, default=jsonb_default_dict, nullable=False)
    retrieved_chunks_json: Mapped[list[dict]] = mapped_column(JSONB, default=jsonb_default_list, nullable=False)
    metrics_json: Mapped[dict] = mapped_column(JSONB, default=jsonb_default_dict, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment = relationship("Experiment")
    strategy = relationship("ChunkingStrategy")
    creator = relationship("User")

