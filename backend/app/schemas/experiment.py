import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import WorkspaceRole


class ExperimentQuery(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    expected_chunk_ids: list[uuid.UUID] = Field(default_factory=list)


class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    description: str | None = None
    strategy_ids: list[uuid.UUID] = Field(min_length=1, max_length=8)
    query_set: list[ExperimentQuery] = Field(min_length=1, max_length=50)
    role_simulation: WorkspaceRole | None = None


class ExperimentRead(BaseModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None
    status: str
    strategy_ids_json: list[str]
    query_set_json: list[dict]
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class StrategyLeaderboardRow(BaseModel):
    strategy_id: uuid.UUID
    strategy_name: str
    query_runs: int
    context_precision: float
    context_recall: float
    average_similarity: float
    irrelevant_chunk_rate: float
    citation_coverage: float
    latency_ms: float
    estimated_cost: float
    rbac_leakage_count: int
    overall_score: float
    recommendation: str


class ExperimentRunResponse(BaseModel):
    experiment: ExperimentRead
    leaderboard: list[StrategyLeaderboardRow]
    best_strategy_id: uuid.UUID | None
    query_run_ids: list[uuid.UUID]


class ExperimentReport(BaseModel):
    experiment: ExperimentRead
    leaderboard: list[StrategyLeaderboardRow]
    best_strategy_id: uuid.UUID | None
    summary: dict


class ProjectRecommendation(BaseModel):
    project_id: uuid.UUID
    recommended_strategy_id: uuid.UUID | None
    recommended_strategy_name: str | None
    leaderboard: list[StrategyLeaderboardRow]
    recommended_config: dict | None
