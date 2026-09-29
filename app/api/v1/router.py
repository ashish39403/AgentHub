from fastapi import APIRouter

from app.api.v1.endpoints import agents, auth, conversations, dashboard, health, integrations, routines, tools

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(agents.router)
api_router.include_router(conversations.router)
api_router.include_router(tools.router)
api_router.include_router(routines.router)
api_router.include_router(integrations.router)
api_router.include_router(dashboard.router)
api_router.include_router(health.router, tags=["health"])
