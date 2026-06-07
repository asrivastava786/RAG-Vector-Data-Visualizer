import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.common import WorkspaceRole
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.audit_service import write_audit_log
from app.services.rbac_service import get_accessible_project, require_workspace_role


def list_projects_for_user(db: Session, *, user: User, workspace_id: uuid.UUID | None = None) -> list[Project]:
    workspace_ids = [membership.workspace_id for membership in user.memberships]
    stmt = select(Project).where(Project.workspace_id.in_(workspace_ids)).order_by(Project.created_at.desc())
    if workspace_id:
        stmt = stmt.where(Project.workspace_id == workspace_id)
    return list(db.scalars(stmt).all())


def create_project(db: Session, *, user: User, payload: ProjectCreate) -> Project:
    require_workspace_role(
        db,
        workspace_id=payload.workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.developer,
    )
    project = Project(
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description,
        use_case=payload.use_case,
        created_by=user.id,
    )
    db.add(project)
    db.flush()
    write_audit_log(
        db,
        workspace_id=payload.workspace_id,
        user_id=user.id,
        action="project.create",
        entity_type="project",
        entity_id=str(project.id),
    )
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, *, user: User, project_id: uuid.UUID, payload: ProjectUpdate) -> Project:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    require_workspace_role(
        db, workspace_id=project.workspace_id, user_id=user.id, minimum_role=WorkspaceRole.admin
    )
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(project, field, value)
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        action="project.update",
        entity_type="project",
        entity_id=str(project.id),
        metadata=changes,
    )
    db.commit()
    db.refresh(project)
    return project

