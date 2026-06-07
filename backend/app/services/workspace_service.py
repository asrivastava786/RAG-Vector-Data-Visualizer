from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.common import WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services.audit_service import write_audit_log
from app.services.auth_service import slugify


def workspace_to_read(workspace: Workspace, role: WorkspaceRole) -> WorkspaceRead:
    return WorkspaceRead(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        owner_user_id=workspace.owner_user_id,
        created_at=workspace.created_at,
        current_user_role=role,
    )


def list_workspaces(db: Session, *, user: User) -> list[WorkspaceRead]:
    memberships = db.scalars(
        select(WorkspaceMember).where(WorkspaceMember.user_id == user.id).order_by(WorkspaceMember.created_at)
    ).all()
    return [workspace_to_read(member.workspace, member.role) for member in memberships]


def create_workspace(db: Session, *, user: User, payload: WorkspaceCreate) -> WorkspaceRead:
    base_slug = payload.slug or slugify(payload.name)
    slug = base_slug
    suffix = 2
    while db.scalar(select(Workspace).where(Workspace.slug == slug)) is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    workspace = Workspace(name=payload.name, slug=slug, owner_user_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.owner))
    write_audit_log(
        db,
        workspace_id=workspace.id,
        user_id=user.id,
        action="workspace.create",
        entity_type="workspace",
        entity_id=str(workspace.id),
    )
    db.commit()
    db.refresh(workspace)
    return workspace_to_read(workspace, WorkspaceRole.owner)

