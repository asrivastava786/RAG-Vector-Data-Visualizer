import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.admin import (
    AdminSettingsResponse,
    AdminUserRead,
    AdminUserUpdate,
    AuditLogRead,
)
from app.services.admin_service import (
    admin_settings,
    list_admin_users,
    list_audit_logs,
    update_admin_user,
)
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/users", response_model=list[AdminUserRead])
def get_admin_users(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[AdminUserRead]:
    return list_admin_users(db, workspace_id=workspace_id, user=current_user)


@router.patch("/users/{user_id}", response_model=AdminUserRead)
def patch_admin_user(
    user_id: uuid.UUID,
    workspace_id: uuid.UUID,
    payload: AdminUserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> AdminUserRead:
    return update_admin_user(
        db,
        workspace_id=workspace_id,
        target_user_id=user_id,
        actor=current_user,
        payload=payload,
    )


@router.get("/audit-logs", response_model=list[AuditLogRead])
def get_admin_audit_logs(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLog]:
    return list_audit_logs(db, workspace_id=workspace_id, user=current_user, limit=limit)


@router.get("/settings", response_model=AdminSettingsResponse)
def get_admin_settings(
    workspace_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> AdminSettingsResponse:
    return admin_settings(db, workspace_id=workspace_id, user=current_user)
