from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, MeResponse, RefreshRequest, RegisterRequest, TokenPair
from app.services.auth_service import authenticate_user, get_current_user, refresh_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenPair, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenPair:
    _, _, tokens = register_user(db, payload)
    return tokens


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    _, tokens = authenticate_user(db, email=payload.email, password=payload.password)
    return tokens


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    return refresh_tokens(db, refresh_token=payload.refresh_token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    memberships = [
        {
            "workspace_id": membership.workspace_id,
            "workspace_name": membership.workspace.name,
            "workspace_slug": membership.workspace.slug,
            "role": membership.role,
        }
        for membership in current_user.memberships
    ]
    return MeResponse(user=current_user, memberships=memberships)
