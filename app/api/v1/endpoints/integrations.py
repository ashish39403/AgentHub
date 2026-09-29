from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.integration import IntegrationStatusResponse
from app.services.integration_service import get_user_gmail_status

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/gmail/status", response_model=IntegrationStatusResponse)
async def gmail_status(current_user: CurrentUser) -> IntegrationStatusResponse:
    return await get_user_gmail_status(user=current_user)
