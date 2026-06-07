import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.experiment import ExperimentReport, ProjectRecommendation
from app.schemas.report import ExportConfigRequest, ExportConfigResponse
from app.services.auth_service import get_current_user
from app.services.experiment_service import (
    recommendation_for_project,
    report_for_experiment,
)
from app.services.report_service import export_project_config

router = APIRouter(tags=["reports"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/experiments/{experiment_id}/report", response_model=ExperimentReport)
def get_experiment_report(
    experiment_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ExperimentReport:
    return report_for_experiment(db, experiment_id=experiment_id, user=current_user)


@router.get("/projects/{project_id}/recommendation", response_model=ProjectRecommendation)
def get_project_recommendation(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectRecommendation:
    return recommendation_for_project(db, project_id=project_id, user=current_user)


@router.post("/projects/{project_id}/export-config", response_model=ExportConfigResponse)
def post_project_export_config(
    project_id: uuid.UUID,
    payload: ExportConfigRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> ExportConfigResponse:
    return export_project_config(
        db,
        project_id=project_id,
        user=current_user,
        export_format=payload.format,
    )
