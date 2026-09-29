from app.integrations.gmail import get_gmail_connection_status
from app.models.user import User
from app.schemas.integration import IntegrationStatusResponse


async def get_user_gmail_status(*, user: User) -> IntegrationStatusResponse:
    status = await get_gmail_connection_status(user_id=user.id)
    return IntegrationStatusResponse(**status)
