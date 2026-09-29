from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppHTTPException
from app.schemas.auth import AuthResponse, RefreshTokenRequest, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthError, login_user, logout_user, refresh_user_tokens, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, session: DbSession) -> AuthResponse:
    try:
        return await register_user(session, payload)
    except AuthError as exc:
        raise AppHTTPException(status_code=409, code="auth_error", message=str(exc)) from exc


@router.post("/login", response_model=AuthResponse)
async def login(payload: UserLogin, session: DbSession) -> AuthResponse:
    try:
        return await login_user(session, payload)
    except AuthError as exc:
        raise AppHTTPException(status_code=401, code="invalid_credentials", message=str(exc)) from exc


@router.post("/refresh", response_model=AuthResponse)
async def refresh(payload: RefreshTokenRequest, session: DbSession) -> AuthResponse:
    try:
        return await refresh_user_tokens(session, payload.refresh_token)
    except AuthError as exc:
        raise AppHTTPException(status_code=401, code="invalid_refresh_token", message=str(exc)) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(payload: RefreshTokenRequest, session: DbSession) -> None:
    await logout_user(session, payload.refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)
