import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.models.audit_log import AuditLog
from app.models.common import WorkspaceRole
from app.models.user import User
from app.models.workspace import WorkspaceMember
from app.schemas.admin import AdminSettingsResponse, AdminUserRead, AdminUserUpdate
from app.services.audit_service import write_audit_log
from app.services.rbac_service import (
    can_manage_users,
    get_workspace_membership,
    require_workspace_role,
)


def list_admin_users(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user: User,
) -> list[AdminUserRead]:
    require_workspace_role(
        db,
        workspace_id=workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.admin,
    )
    members = db.scalars(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at)
    ).all()
    return [
        AdminUserRead(
            user_id=member.user.id,
            email=member.user.email,
            full_name=member.user.full_name,
            is_active=member.user.is_active,
            workspace_id=member.workspace_id,
            role=member.role,
            joined_at=member.created_at,
        )
        for member in members
    ]


def update_admin_user(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    target_user_id: uuid.UUID,
    actor: User,
    payload: AdminUserUpdate,
) -> AdminUserRead:
    actor_membership = require_workspace_role(
        db,
        workspace_id=workspace_id,
        user_id=actor.id,
        minimum_role=WorkspaceRole.admin,
    )
    target_membership = get_workspace_membership(
        db,
        workspace_id=workspace_id,
        user_id=target_user_id,
    )
    if not can_manage_users(actor_membership.role, target_membership.role):
        raise forbidden("You cannot modify a user with that role.")
    target = db.get(User, target_user_id)
    if target is None:
        raise not_found("User not found.")
    if payload.role is not None:
        if not can_manage_users(actor_membership.role, payload.role):
            raise forbidden("You cannot assign that role.")
        target_membership.role = payload.role
    if payload.is_active is not None:
        target.is_active = payload.is_active
    write_audit_log(
        db,
        workspace_id=workspace_id,
        user_id=actor.id,
        action="admin.user.update",
        entity_type="user",
        entity_id=str(target.id),
        metadata={"role": target_membership.role.value, "is_active": target.is_active},
    )
    db.commit()
    db.refresh(target_membership)
    return AdminUserRead(
        user_id=target.id,
        email=target.email,
        full_name=target.full_name,
        is_active=target.is_active,
        workspace_id=workspace_id,
        role=target_membership.role,
        joined_at=target_membership.created_at,
    )


def list_audit_logs(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user: User,
    limit: int = 100,
) -> list[AuditLog]:
    require_workspace_role(
        db,
        workspace_id=workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.admin,
    )
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.workspace_id == workspace_id)
            .order_by(AuditLog.created_at.desc())
            .limit(min(max(limit, 1), 500))
        ).all()
    )


def admin_settings(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user: User,
) -> AdminSettingsResponse:
    require_workspace_role(
        db,
        workspace_id=workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.admin,
    )
    return AdminSettingsResponse(
        embedding_providers=["deterministic_local", "openai_compatible_ready", "bge_ready"],
        storage_provider="s3_compatible_minio",
        api_keys_placeholder=(
            "Workspace API key management is scaffolded for a later hardening pass."
        ),
        rate_limiting="Application-level rate limiting placeholder; deploy behind gateway limits.",
    )
