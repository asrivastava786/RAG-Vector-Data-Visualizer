from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import bad_request, not_found
from app.models.common import WorkspaceRole
from app.models.experiment import Experiment
from app.models.query_run import QueryRun
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentRead,
    ExperimentReport,
    ExperimentRunResponse,
    ProjectRecommendation,
    StrategyLeaderboardRow,
)
from app.schemas.query import QueryAnalyzeRequest
from app.services.audit_service import write_audit_log
from app.services.rbac_service import (
    ROLE_ORDER,
    get_accessible_project,
    get_workspace_membership,
    require_workspace_role,
)
from app.services.retrieval_service import analyze_query


def create_experiment(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
    payload: ExperimentCreate,
) -> Experiment:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    require_workspace_role(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        minimum_role=WorkspaceRole.developer,
    )
    _validate_strategy_ids(db, project_id=project.id, strategy_ids=payload.strategy_ids)
    experiment = Experiment(
        workspace_id=project.workspace_id,
        project_id=project.id,
        name=payload.name.strip(),
        description=payload.description,
        status="draft",
        strategy_ids_json=[str(strategy_id) for strategy_id in payload.strategy_ids],
        query_set_json=[
            {
                "query": item.query,
                "expected_chunk_ids": [str(chunk_id) for chunk_id in item.expected_chunk_ids],
            }
            for item in payload.query_set
        ],
        created_by=user.id,
    )
    db.add(experiment)
    write_audit_log(
        db,
        workspace_id=project.workspace_id,
        user_id=user.id,
        action="experiment.create",
        entity_type="experiment",
        entity_id=str(experiment.id),
        metadata={"strategies": experiment.strategy_ids_json, "queries": len(payload.query_set)},
    )
    db.commit()
    db.refresh(experiment)
    return experiment


def list_project_experiments(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
) -> list[Experiment]:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    return list(
        db.scalars(
            select(Experiment)
            .where(
                Experiment.workspace_id == project.workspace_id,
                Experiment.project_id == project.id,
            )
            .order_by(Experiment.created_at.desc())
        ).all()
    )


def get_experiment_for_user(
    db: Session,
    *,
    experiment_id: uuid.UUID,
    user: User,
) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise not_found("Experiment not found.")
    get_workspace_membership(db, workspace_id=experiment.workspace_id, user_id=user.id)
    return experiment


def run_experiment(
    db: Session,
    *,
    experiment_id: uuid.UUID,
    user: User,
    top_k: int = 5,
) -> ExperimentRunResponse:
    experiment = get_experiment_for_user(db, experiment_id=experiment_id, user=user)
    membership = get_workspace_membership(db, workspace_id=experiment.workspace_id, user_id=user.id)
    if ROLE_ORDER[membership.role] < ROLE_ORDER[WorkspaceRole.analyst]:
        raise bad_request("Viewer role cannot run experiments.")
    experiment.status = "running"
    db.commit()

    query_run_ids: list[uuid.UUID] = []
    for strategy_id in [uuid.UUID(value) for value in experiment.strategy_ids_json]:
        for query_item in experiment.query_set_json:
            analysis = analyze_query(
                db,
                project_id=experiment.project_id,
                user=user,
                payload=QueryAnalyzeRequest(
                    query=str(query_item["query"]),
                    strategy_id=strategy_id,
                    top_k=top_k,
                    role_simulation=membership.role,
                ),
                experiment_id=experiment.id,
            )
            query_run_ids.append(analysis.query_run_id)

    experiment.status = "completed"
    experiment.completed_at = datetime.now(UTC)
    write_audit_log(
        db,
        workspace_id=experiment.workspace_id,
        user_id=user.id,
        action="experiment.run",
        entity_type="experiment",
        entity_id=str(experiment.id),
        metadata={"query_runs": len(query_run_ids)},
    )
    db.commit()
    db.refresh(experiment)
    leaderboard = leaderboard_for_experiment(db, experiment=experiment)
    best = leaderboard[0].strategy_id if leaderboard else None
    return ExperimentRunResponse(
        experiment=ExperimentRead.model_validate(experiment),
        leaderboard=leaderboard,
        best_strategy_id=best,
        query_run_ids=query_run_ids,
    )


def report_for_experiment(
    db: Session,
    *,
    experiment_id: uuid.UUID,
    user: User,
) -> ExperimentReport:
    experiment = get_experiment_for_user(db, experiment_id=experiment_id, user=user)
    leaderboard = leaderboard_for_experiment(db, experiment=experiment)
    best = leaderboard[0].strategy_id if leaderboard else None
    return ExperimentReport(
        experiment=ExperimentRead.model_validate(experiment),
        leaderboard=leaderboard,
        best_strategy_id=best,
        summary={
            "strategies_compared": len(experiment.strategy_ids_json),
            "queries": len(experiment.query_set_json),
            "known_risks": _known_risks(leaderboard),
            "next_actions": _next_actions(leaderboard),
        },
    )


def recommendation_for_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    user: User,
) -> ProjectRecommendation:
    project = get_accessible_project(db, project_id=project_id, user_id=user.id)
    experiments = list(
        db.scalars(
            select(Experiment)
            .where(
                Experiment.workspace_id == project.workspace_id,
                Experiment.project_id == project.id,
                Experiment.status == "completed",
            )
            .order_by(Experiment.completed_at.desc())
        ).all()
    )
    rows: list[StrategyLeaderboardRow] = []
    for experiment in experiments:
        rows.extend(leaderboard_for_experiment(db, experiment=experiment))
    rows.sort(key=lambda row: row.overall_score, reverse=True)
    best = rows[0] if rows else None
    strategy = db.get(ChunkingStrategy, best.strategy_id) if best else None
    return ProjectRecommendation(
        project_id=project.id,
        recommended_strategy_id=best.strategy_id if best else None,
        recommended_strategy_name=best.strategy_name if best else None,
        leaderboard=rows[:8],
        recommended_config=_strategy_config(strategy, best) if strategy and best else None,
    )


def leaderboard_for_experiment(
    db: Session,
    *,
    experiment: Experiment,
) -> list[StrategyLeaderboardRow]:
    runs = list(
        db.scalars(
            select(QueryRun).where(
                QueryRun.workspace_id == experiment.workspace_id,
                QueryRun.project_id == experiment.project_id,
                QueryRun.experiment_id == experiment.id,
            )
        ).all()
    )
    by_strategy: dict[uuid.UUID, list[QueryRun]] = defaultdict(list)
    for run in runs:
        by_strategy[run.strategy_id].append(run)

    rows: list[StrategyLeaderboardRow] = []
    for strategy_id, strategy_runs in by_strategy.items():
        strategy = db.get(ChunkingStrategy, strategy_id)
        if strategy is None:
            continue
        rows.append(_row_for_strategy(strategy=strategy, runs=strategy_runs))
    rows.sort(key=lambda row: (row.rbac_leakage_count == 0, row.overall_score), reverse=True)
    return rows


def _row_for_strategy(
    *,
    strategy: ChunkingStrategy,
    runs: list[QueryRun],
) -> StrategyLeaderboardRow:
    metrics = [run.metrics_json for run in runs]
    leaks = sum(int(metric.get("rbac_leakage_count", 0) or 0) for metric in metrics)
    score = _average(metrics, "overall_score")
    return StrategyLeaderboardRow(
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        query_runs=len(runs),
        context_precision=_average(metrics, "context_precision"),
        context_recall=_average(metrics, "context_recall"),
        average_similarity=_average(metrics, "average_similarity"),
        irrelevant_chunk_rate=_average(metrics, "irrelevant_chunk_rate"),
        citation_coverage=_average(metrics, "citation_coverage"),
        latency_ms=_average(metrics, "latency_ms"),
        estimated_cost=_average(metrics, "estimated_cost"),
        rbac_leakage_count=leaks,
        overall_score=0.0 if leaks else score,
        recommendation=_recommendation_label(score=score, leaks=leaks),
    )


def _validate_strategy_ids(
    db: Session,
    *,
    project_id: uuid.UUID,
    strategy_ids: list[uuid.UUID],
) -> None:
    strategies = list(
        db.scalars(
            select(ChunkingStrategy).where(
                ChunkingStrategy.project_id == project_id,
                ChunkingStrategy.id.in_(strategy_ids),
            )
        ).all()
    )
    if len(strategies) != len(set(strategy_ids)):
        raise bad_request("All strategies must belong to the project.")


def _average(metrics: list[dict], key: str) -> float:
    if not metrics:
        return 0.0
    return round(sum(float(metric.get(key, 0) or 0) for metric in metrics) / len(metrics), 6)


def _recommendation_label(*, score: float, leaks: int) -> str:
    if leaks:
        return "Blocked: RBAC leakage detected"
    if score >= 0.75:
        return "Recommended"
    if score >= 0.5:
        return "Promising"
    return "Needs tuning"


def _strategy_config(
    strategy: ChunkingStrategy,
    row: StrategyLeaderboardRow,
) -> dict:
    return {
        "recommended_strategy": {
            "splitter_type": strategy.splitter_type,
            "chunk_size": strategy.chunk_size,
            "overlap": strategy.overlap,
            "preserve_headings": strategy.preserve_headings,
            "preserve_tables": strategy.preserve_tables,
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
            "context_precision": row.context_precision,
            "context_recall": row.context_recall,
            "overall_score": row.overall_score,
        },
    }


def _known_risks(rows: list[StrategyLeaderboardRow]) -> list[str]:
    risks: list[str] = []
    if any(row.rbac_leakage_count for row in rows):
        risks.append("At least one strategy returned RBAC leakage and must be blocked.")
    if rows and rows[0].citation_coverage < 0.5:
        risks.append("Best strategy has low citation coverage.")
    if rows and rows[0].irrelevant_chunk_rate > 0.5:
        risks.append("Best strategy still retrieves too many irrelevant chunks.")
    return risks or ["No critical risks detected in this MVP evaluation."]


def _next_actions(rows: list[StrategyLeaderboardRow]) -> list[str]:
    if not rows:
        return ["Run an experiment with at least one indexed strategy."]
    best = rows[0]
    actions = [f"Promote '{best.strategy_name}' as the current baseline."]
    if best.context_recall < 0.6:
        actions.append(
            "Test larger chunk sizes or lower sparse/dense thresholds to improve recall."
        )
    if best.latency_ms > 1000:
        actions.append("Profile candidate count and add vector indexes before production traffic.")
    return actions
