from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_user_id,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.user import User
from app.repositories import refresh_tokens as refresh_token_repository
from app.repositories import users as user_repository
from app.schemas.auth import AuthResponse, TokenPair, UserCreate, UserLogin


class AuthError(ValueError):
    pass


async def register_user(session: AsyncSession, payload: UserCreate) -> AuthResponse:
    existing_user = await user_repository.get_user_by_email(session, payload.email)
    if existing_user:
        raise AuthError("A user with this email already exists.")

    user = await user_repository.create_user(
        session,
        name=payload.name.strip(),
        email=str(payload.email),
        hashed_password=hash_password(payload.password),
    )
    tokens = await issue_tokens(session, user)
    await session.commit()
    await session.refresh(user)

    return AuthResponse(user=user, tokens=tokens)


async def login_user(session: AsyncSession, payload: UserLogin) -> AuthResponse:
    user = await user_repository.get_user_by_email(session, str(payload.email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise AuthError("Invalid email or password.")

    tokens = await issue_tokens(session, user)
    await session.commit()
    await session.refresh(user)

    return AuthResponse(user=user, tokens=tokens)


async def refresh_user_tokens(session: AsyncSession, refresh_token: str) -> AuthResponse:
    try:
        user_id = decode_user_id(refresh_token, expected_type="refresh")
    except TokenError as exc:
        raise AuthError("Invalid refresh token.") from exc

    stored_token = await refresh_token_repository.get_active_refresh_token(session, hash_token(refresh_token))
    user = await user_repository.get_user_by_id(session, user_id)
    if stored_token is None or user is None or stored_token.user_id != user.id:
        raise AuthError("Invalid refresh token.")

    await refresh_token_repository.revoke_refresh_token(session, stored_token)
    tokens = await issue_tokens(session, user)
    await session.commit()
    await session.refresh(user)

    return AuthResponse(user=user, tokens=tokens)


async def logout_user(session: AsyncSession, refresh_token: str) -> None:
    stored_token = await refresh_token_repository.get_active_refresh_token(session, hash_token(refresh_token))
    if stored_token is not None:
        await refresh_token_repository.revoke_refresh_token(session, stored_token)
        await session.commit()


async def issue_tokens(session: AsyncSession, user: User) -> TokenPair:
    access_token = create_access_token(user.id)
    refresh_token, refresh_token_hash, expires_at = create_refresh_token(user.id)
    await refresh_token_repository.create_refresh_token(
        session,
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=expires_at,
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
