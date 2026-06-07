import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.experiment import Experiment
from app.models.user import User
from app.schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentRunResponse
from app.services.auth_service import get_current_user
from app.services.experiment_service import (
    create_experiment,
    get_experiment_for_user,
    list_project_experiments,
    run_experiment,
)

router = APIRouter(tags=["experiments"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/projects/{project_id}/experiments", response_model=ExperimentRead, status_code=201)
def post_experiment(
    project_id: uuid.UUID,
    payload: ExperimentCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> Experiment:
    return create_experiment(db, project_id=project_id, user=current_user, payload=payload)


@router.get("/projects/{project_id}/experiments", response_model=list[ExperimentRead])
def get_project_experiments(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[Experiment]:
    return list_project_experiments(db, project_id=project_id, user=current_user)


@router.get("/experiments/{experiment_id}", response_model=ExperimentRead)
def get_experiment(
    experiment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> Experiment:
    return get_experiment_for_user(db, experiment_id=experiment_id, user=current_user)


@router.post("/experiments/{experiment_id}/run", response_model=ExperimentRunResponse)
def post_run_experiment(
    experiment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ExperimentRunResponse:
    return run_experiment(db, experiment_id=experiment_id, user=current_user)
