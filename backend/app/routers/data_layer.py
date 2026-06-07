import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.data_layer import DataLayerRecommendationResponse
from app.services.auth_service import get_current_user
from app.services.data_layer_service import data_layer_recommendation_for_project

router = APIRouter(tags=["data-layer"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/projects/{project_id}/data-layer/recommendation", response_model=DataLayerRecommendationResponse)
def get_project_data_layer_recommendation(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> DataLayerRecommendationResponse:
    return data_layer_recommendation_for_project(db, project_id=project_id, user=current_user)
