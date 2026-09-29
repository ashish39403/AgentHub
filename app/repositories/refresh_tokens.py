from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def create_refresh_token(
    session: AsyncSession,
    *,
    user_id,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    refresh_token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
    session.add(refresh_token)
    await session.flush()
    return refresh_token


async def get_active_refresh_token(session: AsyncSession, token_hash: str) -> RefreshToken | None:
    now = datetime.now(UTC)
    result = await session.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(session: AsyncSession, refresh_token: RefreshToken) -> None:
    refresh_token.revoked_at = datetime.now(UTC)
    await session.flush()
