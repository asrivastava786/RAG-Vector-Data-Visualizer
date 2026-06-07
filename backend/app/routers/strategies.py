import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chunk import Chunk
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.chunk import ChunkRead
from app.schemas.strategy import StrategyCreate, StrategyIndexResponse, StrategyRead
from app.services.auth_service import get_current_user
from app.services.strategy_service import (
    create_strategy,
    get_strategy_for_user,
    index_strategy,
    list_project_strategies,
    list_strategy_chunks,
)

router = APIRouter(tags=["strategies"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/projects/{project_id}/strategies", response_model=StrategyRead, status_code=201)
def post_strategy(
    project_id: uuid.UUID,
    payload: StrategyCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ChunkingStrategy:
    return create_strategy(db, project_id=project_id, user=current_user, payload=payload)


@router.get("/projects/{project_id}/strategies", response_model=list[StrategyRead])
def get_project_strategies(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> list[ChunkingStrategy]:
    return list_project_strategies(db, project_id=project_id, user=current_user)


@router.get("/strategies/{strategy_id}", response_model=StrategyRead)
def get_strategy(
    strategy_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ChunkingStrategy:
    return get_strategy_for_user(db, strategy_id=strategy_id, user=current_user)


@router.post("/strategies/{strategy_id}/index", response_model=StrategyIndexResponse)
def post_index_strategy(
    strategy_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> StrategyIndexResponse:
    result = index_strategy(db, strategy_id=strategy_id, user=current_user)
    return StrategyIndexResponse(**result.__dict__)


@router.get("/strategies/{strategy_id}/chunks", response_model=list[ChunkRead])
def get_strategy_chunks(
    strategy_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[Chunk]:
    return list_strategy_chunks(db, strategy_id=strategy_id, user=current_user, limit=limit)
