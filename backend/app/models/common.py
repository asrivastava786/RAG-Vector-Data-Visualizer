import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class WorkspaceRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    developer = "developer"
    analyst = "analyst"
    viewer = "viewer"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def fk(target: str, *, nullable: bool = False) -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey(target, ondelete="CASCADE"), nullable=nullable)


jsonb_default_list = lambda: []  # noqa: E731
jsonb_default_dict = lambda: {}  # noqa: E731

WorkspaceRoleEnum = Enum(WorkspaceRole, name="workspace_role")
JsonDict = JSONB

