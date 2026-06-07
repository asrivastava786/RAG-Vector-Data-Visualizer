import sys
from pathlib import Path

from sqlalchemy import select

sys.path.append(str(Path(__file__).resolve().parents[1]))

import app.db.base  # noqa: F401
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.common import WorkspaceRole
from app.models.document import Document
from app.models.project import Project
from app.models.strategy import ChunkingStrategy
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember


def get_or_create_user(db, *, email: str, full_name: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, full_name=full_name, hashed_password=hash_password("ChangeMeDemo123!"))
    db.add(user)
    db.flush()
    return user


def main() -> None:
    db = SessionLocal()
    try:
        owner = get_or_create_user(db, email="owner@demo.example.com", full_name="Demo Owner")
        admin = get_or_create_user(db, email="admin@demo.example.com", full_name="Demo Admin")
        developer = get_or_create_user(
            db, email="developer@demo.example.com", full_name="Demo Developer"
        )
        analyst = get_or_create_user(db, email="analyst@demo.example.com", full_name="Demo Analyst")
        viewer = get_or_create_user(db, email="viewer@demo.example.com", full_name="Demo Viewer")

        workspace = db.scalar(select(Workspace).where(Workspace.slug == "demo-workspace"))
        if workspace is None:
            workspace = Workspace(
                name="Demo Workspace",
                slug="demo-workspace",
                owner_user_id=owner.id,
            )
            db.add(workspace)
            db.flush()

        for user, role in [
            (owner, WorkspaceRole.owner),
            (admin, WorkspaceRole.admin),
            (developer, WorkspaceRole.developer),
            (analyst, WorkspaceRole.analyst),
            (viewer, WorkspaceRole.viewer),
        ]:
            exists = db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace.id,
                    WorkspaceMember.user_id == user.id,
                )
            )
            if exists is None:
                db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=role))

        project = db.scalar(select(Project).where(Project.workspace_id == workspace.id))
        if project is None:
            project = Project(
                workspace_id=workspace.id,
                name="HR Policy Assistant Optimization",
                description=(
                    "Demo RAG optimization project for policy retrieval, RBAC safety, and "
                    "strategy comparison."
                ),
                use_case="HR policy assistant",
                created_by=owner.id,
            )
            db.add(project)
            db.flush()

        project_strategies = list(
            db.scalars(
                select(ChunkingStrategy).where(ChunkingStrategy.project_id == project.id)
            ).all()
        )
        for strategy in project_strategies:
            if strategy.splitter_type == "heading_recursive":
                strategy.splitter_type = "heading"
                strategy.config_json = {
                    **strategy.config_json,
                    "migration_note": "Seed strategy normalized to Phase 3 splitter types.",
                }
        existing_strategy = project_strategies[0] if project_strategies else None
        if not existing_strategy:
            db.add_all(
                [
                    ChunkingStrategy(
                        workspace_id=workspace.id,
                        project_id=project.id,
                        name="Heading recursive 600/100",
                        splitter_type="heading",
                        chunk_size=600,
                        overlap=100,
                        preserve_headings=True,
                        preserve_tables=True,
                        semantic_threshold=None,
                        config_json={"phase": "seed"},
                        created_by=owner.id,
                    ),
                    ChunkingStrategy(
                        workspace_id=workspace.id,
                        project_id=project.id,
                        name="Semantic paragraph baseline",
                        splitter_type="semantic",
                        chunk_size=450,
                        overlap=60,
                        preserve_headings=True,
                        preserve_tables=False,
                        semantic_threshold=0.72,
                        config_json={"phase": "seed"},
                        created_by=developer.id,
                    ),
                ]
            )
        if not db.scalars(select(Document).where(Document.project_id == project.id)).first():
            db.add(
                Document(
                    workspace_id=workspace.id,
                    project_id=project.id,
                    uploaded_by=owner.id,
                    title="Employee Leave Policy",
                    filename="employee-leave-policy.md",
                    content_type="text/markdown",
                    storage_key=f"seed/{workspace.id}/{project.id}/employee-leave-policy.md",
                    status="processed",
                    extracted_text=(
                        "# Employee Leave Policy\n\n"
                        "Employees may request paid leave through the HR portal. Managers approve "
                        "leave based on eligibility, staffing, and policy constraints.\n\n"
                        "| Role | Visibility |\n| --- | --- |\n| employee | public policy |\n"
                    ),
                    metadata_json={
                        "source": "seed",
                        "structure": {
                            "kind": "markdown",
                            "paragraph_count": 3,
                            "headings": [{"line": 1, "text": "Employee Leave Policy"}],
                            "tables": [{"start_line": 5, "end_line": 7}],
                        },
                        "warnings": [],
                        "extracted_character_count": 216,
                    },
                    allowed_roles_json=["owner", "admin", "developer", "analyst", "viewer"],
                    allowed_users_json=[],
                    tags_json=["hr", "policy", "seed"],
                )
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
