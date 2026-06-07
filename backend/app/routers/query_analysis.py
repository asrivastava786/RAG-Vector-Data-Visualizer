import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.query import (
    FunnelResponse,
    GraphResponse,
    QueryAnalyzeRequest,
    QueryAnalyzeResponse,
    QueryCompareRequest,
    QueryCompareResponse,
    QueryCompareResult,
    QueryOptimizeRequest,
    QueryOptimizeResponse,
    ScatterResponse,
)
from app.services.auth_service import get_current_user
from app.services.optimization_service import optimize_query
from app.services.retrieval_service import analyze_query
from app.services.visualization_service import (
    funnel_for_query_run,
    graph_for_query_run,
    scatter_for_query_run,
)

router = APIRouter(tags=["query-analysis"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/projects/{project_id}/query/analyze", response_model=QueryAnalyzeResponse)
def post_query_analysis(
    project_id: uuid.UUID,
    payload: QueryAnalyzeRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> QueryAnalyzeResponse:
    return analyze_query(db, project_id=project_id, user=current_user, payload=payload)


@router.post("/projects/{project_id}/query/optimize", response_model=QueryOptimizeResponse)
def post_query_optimize(
    project_id: uuid.UUID,
    payload: QueryOptimizeRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> QueryOptimizeResponse:
    # Project access is checked by a retrieval-shaped no-op lookup path in later phases.
    from app.services.rbac_service import get_accessible_project

    project = get_accessible_project(db, project_id=project_id, user_id=current_user.id)
    return optimize_query(payload.query, payload.use_case or project.use_case)


@router.post("/projects/{project_id}/query/compare", response_model=QueryCompareResponse)
def post_query_compare(
    project_id: uuid.UUID,
    payload: QueryCompareRequest,
    current_user: CurrentUser,
    db: DbSession,
) -> QueryCompareResponse:
    results: list[QueryCompareResult] = []
    for strategy_id in payload.strategy_ids:
        analysis = analyze_query(
            db,
            project_id=project_id,
            user=current_user,
            payload=QueryAnalyzeRequest(
                query=payload.query,
                strategy_id=strategy_id,
                top_k=payload.top_k,
                role_simulation=payload.role_simulation,
            ),
        )
        results.append(
            QueryCompareResult(
                strategy_id=strategy_id,
                query_run_id=analysis.query_run_id,
                metrics=analysis.metrics,
                top_chunk_count=len(analysis.retrieved_chunks),
                latency_ms=analysis.latency_ms,
            )
        )
    return QueryCompareResponse(query=payload.query, results=results)


@router.get("/query-runs/{query_run_id}/scatter", response_model=ScatterResponse)
def get_query_run_scatter(
    query_run_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> ScatterResponse:
    return scatter_for_query_run(db, query_run_id=query_run_id, user=current_user)


@router.get("/query-runs/{query_run_id}/graph", response_model=GraphResponse)
def get_query_run_graph(
    query_run_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> GraphResponse:
    return graph_for_query_run(db, query_run_id=query_run_id, user=current_user)


@router.get("/query-runs/{query_run_id}/funnel", response_model=FunnelResponse)
def get_query_run_funnel(
    query_run_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> FunnelResponse:
    return funnel_for_query_run(db, query_run_id=query_run_id, user=current_user)
