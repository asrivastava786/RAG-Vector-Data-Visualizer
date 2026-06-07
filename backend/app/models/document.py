import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.common import TimestampMixin, jsonb_default_dict, jsonb_default_list, uuid_pk


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = uuid_pk()
    workspace_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="uploaded", nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=jsonb_default_dict, nullable=False)
    allowed_roles_json: Mapped[list[str]] = mapped_column(JSONB, default=jsonb_default_list, nullable=False)
    allowed_users_json: Mapped[list[str]] = mapped_column(JSONB, default=jsonb_default_list, nullable=False)
    tags_json: Mapped[list[str]] = mapped_column(JSONB, default=jsonb_default_list, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer)

    project = relationship("Project", back_populates="documents")
    uploader = relationship("User")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

