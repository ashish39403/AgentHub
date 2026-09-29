from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: UUID) -> User | None:
    return await session.get(User, user_id)


async def create_user(session: AsyncSession, *, name: str, email: str, hashed_password: str) -> User:
    user = User(name=name, email=email.lower(), hashed_password=hashed_password)
    session.add(user)
    await session.flush()
    return user
