import re
import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import bad_request, forbidden
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.common import WorkspaceRole
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember
from app.schemas.auth import RegisterRequest, TokenPair
from app.services.audit_service import write_audit_log

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or f"workspace-{uuid.uuid4().hex[:8]}"


def register_user(db: Session, payload: RegisterRequest) -> tuple[User, Workspace, TokenPair]:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise bad_request("A user with that email already exists.")

    user = User(
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()

    base_slug = slugify(payload.workspace_name)
    slug = base_slug
    suffix = 2
    while db.scalar(select(Workspace).where(Workspace.slug == slug)) is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    workspace = Workspace(name=payload.workspace_name, slug=slug, owner_user_id=user.id)
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.owner))
    write_audit_log(
        db,
        workspace_id=workspace.id,
        user_id=user.id,
        action="auth.register",
        entity_type="workspace",
        entity_id=str(workspace.id),
    )
    db.commit()
    db.refresh(user)
    db.refresh(workspace)
    return user, workspace, issue_tokens(user)


def authenticate_user(db: Session, *, email: str, password: str) -> tuple[User, TokenPair]:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.hashed_password):
        raise forbidden("Invalid email or password.")
    if not user.is_active:
        raise forbidden("User account is inactive.")
    write_audit_log(
        db,
        workspace_id=None,
        user_id=user.id,
        action="auth.login",
        entity_type="user",
        entity_id=str(user.id),
    )
    db.commit()
    return user, issue_tokens(user)


def issue_tokens(user: User) -> TokenPair:
    subject = str(user.id)
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


def refresh_tokens(db: Session, *, refresh_token: str) -> TokenPair:
    try:
        payload = decode_token(refresh_token)
    except InvalidTokenError as exc:
        raise forbidden("Invalid refresh token.") from exc
    if payload.get("type") != "refresh":
        raise forbidden("Invalid refresh token.")
    user_id = payload.get("sub")
    if not user_id:
        raise forbidden("Invalid refresh token.")
    user = db.get(User, uuid.UUID(str(user_id)))
    if user is None or not user.is_active:
        raise forbidden("Invalid refresh token.")
    return issue_tokens(user)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except InvalidTokenError as exc:
        raise forbidden("Invalid authentication token.") from exc
    if payload.get("type") != "access":
        raise forbidden("Invalid authentication token.")
    user_id = payload.get("sub")
    if not user_id:
        raise forbidden("Invalid authentication token.")
    user = db.scalar(
        select(User)
        .options(selectinload(User.memberships).selectinload(WorkspaceMember.workspace))
        .where(User.id == uuid.UUID(str(user_id)))
    )
    if user is None or not user.is_active:
        raise forbidden("Invalid authentication token.")
    return user
