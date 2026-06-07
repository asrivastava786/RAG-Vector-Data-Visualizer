import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.rbac import RBACMatrixResponse, RBACSimulationRequest, RBACSimulationResponse
from app.services.auth_service import get_current_user
from app.services.rbac_analysis_service import rbac_matrix, simulate_rbac

router = APIRouter(tags=["rbac"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/projects/{project_id}/rbac/simulate", response_model=RBACSimulationResponse)
def post_rbac_simulation(
    project_id: uuid.UUID,
    payload: RBACSimulationRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> RBACSimulationResponse:
    return simulate_rbac(db, project_id=project_id, user=current_user, payload=payload)


@router.get("/projects/{project_id}/rbac/matrix", response_model=RBACMatrixResponse)
def get_rbac_matrix(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> RBACMatrixResponse:
    return rbac_matrix(db, project_id=project_id, user=current_user)
