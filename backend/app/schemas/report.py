from pydantic import BaseModel, Field


class RecommendationConfig(BaseModel):
    recommended_strategy: dict
    retrieval: dict
    rbac: dict
    metrics: dict


class ExportConfigRequest(BaseModel):
    format: str = Field(default="json", pattern="^(json|yaml|langchain|llamaindex|fastapi)$")


class ExportConfigResponse(BaseModel):
    format: str
    content: str
    content_type: str
    recommended_config: dict
