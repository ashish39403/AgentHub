from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppHTTPException
from app.core.security import TokenError, decode_user_id
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.users import get_user_by_id

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    session: DbSession,
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization:
        raise AppHTTPException(status_code=401, code="not_authenticated", message="Authentication required.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise AppHTTPException(status_code=401, code="invalid_auth_header", message="Invalid authorization header.")

    try:
        user_id = decode_user_id(token, expected_type="access")
    except TokenError as exc:
        raise AppHTTPException(status_code=401, code="invalid_token", message="Invalid or expired token.") from exc

    user = await get_user_by_id(session, user_id)
    if user is None:
        raise AppHTTPException(status_code=401, code="invalid_token", message="Invalid or expired token.")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
