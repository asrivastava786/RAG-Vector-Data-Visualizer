import json
import uuid

from sqlalchemy.orm import Session

from app.core.errors import bad_request
from app.models.user import User
from app.schemas.report import ExportConfigResponse
from app.services.experiment_service import recommendation_for_project


def export_project_config(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    export_format: str,
) -> ExportConfigResponse:
    recommendation = recommendation_for_project(db, project_id=project_id, user=user)
    config = recommendation.recommended_config
    if config is None:
        config = _fallback_config()
    content = _render_config(config, export_format)
    content_types = {
        "json": "application/json",
        "yaml": "application/x-yaml",
        "langchain": "text/x-python",
        "llamaindex": "text/x-python",
        "fastapi": "text/x-python",
    }
    return ExportConfigResponse(
        format=export_format,
        content=content,
        content_type=content_types[export_format],
        recommended_config=config,
    )


def _render_config(config: dict, export_format: str) -> str:
    if export_format == "json":
        return json.dumps(config, indent=2)
    if export_format == "yaml":
        return _to_yaml(config)
    if export_format == "langchain":
        return _langchain_snippet(config)
    if export_format == "llamaindex":
        return _llamaindex_snippet(config)
    if export_format == "fastapi":
        return _fastapi_snippet(config)
    raise bad_request("Unsupported export format.")


def _fallback_config() -> dict:
    return {
        "recommended_strategy": {
            "splitter_type": "recursive",
            "chunk_size": 600,
            "overlap": 100,
            "preserve_headings": True,
            "preserve_tables": True,
        },
        "retrieval": {
            "type": "hybrid",
            "dense_weight": 0.7,
            "sparse_weight": 0.3,
            "top_k": 10,
            "reranker": "disabled",
        },
        "rbac": {
            "filter_fields": ["workspace_id", "project_id", "allowed_roles", "allowed_users"],
        },
        "metrics": {
            "context_precision": 0.0,
            "context_recall": 0.0,
            "overall_score": 0.0,
        },
    }


def _to_yaml(value: object, *, indent: int = 0) -> str:
    prefix = " " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, dict | list):
                lines.append(f"{prefix}{key}:")
                lines.append(_to_yaml(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}{key}: {json.dumps(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{prefix}-")
                lines.append(_to_yaml(item, indent=indent + 2))
            else:
                lines.append(f"{prefix}- {json.dumps(item)}")
        return "\n".join(lines)
    return f"{prefix}{json.dumps(value)}"


def _langchain_snippet(config: dict) -> str:
    return f"""# LangChain-style pseudocode
splitter = RecursiveCharacterTextSplitter(
    chunk_size={config['recommended_strategy']['chunk_size']},
    chunk_overlap={config['recommended_strategy']['overlap']},
)
retriever = HybridRetriever(
    dense_weight={config['retrieval']['dense_weight']},
    sparse_weight={config['retrieval']['sparse_weight']},
    top_k={config['retrieval']['top_k']},
    metadata_filters={config['rbac']['filter_fields']},
)
"""


def _llamaindex_snippet(config: dict) -> str:
    return f"""# LlamaIndex-style pseudocode
node_parser = SentenceSplitter(
    chunk_size={config['recommended_strategy']['chunk_size']},
    chunk_overlap={config['recommended_strategy']['overlap']},
)
query_engine = HybridQueryEngine(
    similarity_top_k={config['retrieval']['top_k']},
    dense_weight={config['retrieval']['dense_weight']},
    sparse_weight={config['retrieval']['sparse_weight']},
    required_filters={config['rbac']['filter_fields']},
)
"""


def _fastapi_snippet(config: dict) -> str:
    return f"""# FastAPI integration sketch
@router.post("/retrieve")
def retrieve(payload: RetrieveRequest, user: CurrentUser):
    filters = {{
        "workspace_id": user.workspace_id,
        "project_id": payload.project_id,
        "allowed_roles": [user.role],
        "allowed_users": [str(user.id)],
    }}
    return hybrid_retrieve(
        query=payload.query,
        filters=filters,
        dense_weight={config['retrieval']['dense_weight']},
        sparse_weight={config['retrieval']['sparse_weight']},
        top_k={config['retrieval']['top_k']},
    )
"""
