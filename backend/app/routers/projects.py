import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.common import WorkspaceRole
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services.audit_service import write_audit_log
from app.services.auth_service import get_current_user
from app.services.project_service import create_project, list_projects_for_user, update_project
from app.services.rbac_service import get_accessible_project, require_workspace_role

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def get_projects(
    workspace_id: uuid.UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Project]:
    return list_projects_for_user(db, user=current_user, workspace_id=workspace_id)


@router.post("", response_model=ProjectRead, status_code=201)
def post_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return create_project(db, user=current_user, payload=payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return get_accessible_project(db, project_id=project_id, user_id=current_user.id)


@router.patch("/{project_id}", response_model=ProjectRead)
def patch_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    return update_project(db, user=current_user, project_id=project_id, payload=payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    project = get_accessible_project(db, project_id=project_id, user_id=current_user.id)
    require_workspace_role(
        db, workspace_id=project.workspace_id, user_id=current_user.id, minimum_role=WorkspaceRole.admin
    )
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=current_user.id,
        action="project.delete",
        entity_type="project",
        entity_id=str(project.id),
    )
    db.delete(project)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

