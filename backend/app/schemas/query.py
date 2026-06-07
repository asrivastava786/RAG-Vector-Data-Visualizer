import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.common import WorkspaceRole


class QueryAnalyzeRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    strategy_id: uuid.UUID
    top_k: int = Field(default=5, ge=1, le=50)
    dense_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    sparse_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    role_simulation: WorkspaceRole | None = None
    rerank: bool = False


class ScoreBreakdown(BaseModel):
    dense_score: float
    sparse_score: float
    hybrid_score: float
    rerank_score: float | None = None


class RetrievedChunk(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    strategy_id: uuid.UUID
    chunk_index: int
    text: str
    token_count: int
    page_number: int | None
    section_heading: str | None
    allowed_roles: list[str]
    tags: list[str]
    metadata: dict
    scores: ScoreBreakdown


class FunnelStage(BaseModel):
    name: str
    count: int
    latency_ms: int


class QueryMetrics(BaseModel):
    context_precision: float
    context_recall: float
    average_similarity: float
    irrelevant_chunk_rate: float
    citation_coverage: float
    rbac_leakage_count: int
    latency_ms: int
    estimated_cost: float
    overall_score: float
    warnings: list[str] = Field(default_factory=list)


class QueryAnalyzeResponse(BaseModel):
    query_run_id: uuid.UUID
    project_id: uuid.UUID
    strategy_id: uuid.UUID
    query: str
    role_context: dict
    retrieved_chunks: list[RetrievedChunk]
    metrics: QueryMetrics
    funnel: list[FunnelStage]
    latency_ms: int
    created_at: datetime


class QueryCompareRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    strategy_ids: list[uuid.UUID] = Field(min_length=1, max_length=6)
    top_k: int = Field(default=5, ge=1, le=50)
    role_simulation: WorkspaceRole | None = None


class QueryCompareResult(BaseModel):
    strategy_id: uuid.UUID
    query_run_id: uuid.UUID
    metrics: QueryMetrics
    top_chunk_count: int
    latency_ms: int


class QueryCompareResponse(BaseModel):
    query: str
    results: list[QueryCompareResult]


class ScatterPoint(BaseModel):
    id: str
    type: str
    label: str
    x: float
    y: float
    score: float
    cluster: str
    metadata: dict


class ScatterResponse(BaseModel):
    points: list[ScatterPoint]


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    metadata: dict = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    label: str


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class FunnelResponse(BaseModel):
    stages: list[FunnelStage]


class QueryOptimizeRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2000)
    use_case: str | None = None


class OptimizedQuery(BaseModel):
    query: str
    method: str
    reason: str


class QueryOptimizeResponse(BaseModel):
    original_query: str
    optimized_queries: list[OptimizedQuery]
