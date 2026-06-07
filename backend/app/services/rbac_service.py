import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import forbidden, not_found
from app.models.common import WorkspaceRole
from app.models.project import Project
from app.models.workspace import Workspace, WorkspaceMember

ROLE_ORDER = {
    WorkspaceRole.owner: 5,
    WorkspaceRole.admin: 4,
    WorkspaceRole.developer: 3,
    WorkspaceRole.analyst: 2,
    WorkspaceRole.viewer: 1,
}


def get_workspace_membership(
    db: Session, *, workspace_id: uuid.UUID, user_id: uuid.UUID
) -> WorkspaceMember:
    membership = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    )
    if membership is None:
        raise forbidden()
    return membership


def require_workspace_role(
    db: Session,
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    minimum_role: WorkspaceRole,
) -> WorkspaceMember:
    membership = get_workspace_membership(db, workspace_id=workspace_id, user_id=user_id)
    if ROLE_ORDER[membership.role] < ROLE_ORDER[minimum_role]:
        raise forbidden()
    return membership


def get_accessible_workspace(db: Session, *, workspace_id: uuid.UUID, user_id: uuid.UUID) -> Workspace:
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise not_found("Workspace not found.")
    get_workspace_membership(db, workspace_id=workspace_id, user_id=user_id)
    return workspace


def get_accessible_project(db: Session, *, project_id: uuid.UUID, user_id: uuid.UUID) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise not_found("Project not found.")
    get_workspace_membership(db, workspace_id=project.workspace_id, user_id=user_id)
    return project


def can_manage_users(actor_role: WorkspaceRole, target_role: WorkspaceRole) -> bool:
    if actor_role == WorkspaceRole.owner:
        return True
    if actor_role == WorkspaceRole.admin and target_role != WorkspaceRole.owner:
        return True
    return False

