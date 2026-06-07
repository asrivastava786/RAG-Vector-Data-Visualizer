import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceRead
from app.services.auth_service import get_current_user
from app.services.rbac_service import get_accessible_workspace, get_workspace_membership
from app.services.workspace_service import create_workspace, list_workspaces, workspace_to_read

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.get("", response_model=list[WorkspaceRead])
def get_workspaces(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[WorkspaceRead]:
    return list_workspaces(db, user=current_user)


@router.post("", response_model=WorkspaceRead, status_code=201)
def post_workspace(
    payload: WorkspaceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceRead:
    return create_workspace(db, user=current_user, payload=payload)


@router.get("/{workspace_id}", response_model=WorkspaceRead)
def get_workspace(
    workspace_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> WorkspaceRead:
    workspace = get_accessible_workspace(db, workspace_id=workspace_id, user_id=current_user.id)
    membership = get_workspace_membership(db, workspace_id=workspace.id, user_id=current_user.id)
    return workspace_to_read(workspace, membership.role)

