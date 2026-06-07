from pydantic import BaseModel, Field


class DataLayerProjectFacts(BaseModel):
    document_count: int
    processed_document_count: int
    chunk_count: int
    strategy_count: int
    query_run_count: int
    content_types: dict[str, int]
    average_chunk_tokens: float
    chunks_with_embeddings: int
    chunks_with_section_headings: int
    chunks_with_tags: int
    distinct_access_profiles: int
    mixed_access_chunk_count: int


class DataLayerStoreRecommendation(BaseModel):
    store: str
    role: str
    fit_score: float = Field(ge=0.0, le=1.0)
    primary_entities: list[str]
    indexing_strategy: list[str]
    rationale: list[str]
    risks: list[str]


class DataLayerRoutingRule(BaseModel):
    data_domain: str
    primary_store: str
    secondary_stores: list[str]
    reason: str
    sync_pattern: str


class DataLayerRecommendationResponse(BaseModel):
    project_id: str
    facts: DataLayerProjectFacts
    recommended_architecture: str
    stores: list[DataLayerStoreRecommendation]
    routing_rules: list[DataLayerRoutingRule]
    efficiency_recommendations: list[str]
    governance_rules: list[str]
    warnings: list[str]
