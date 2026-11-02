from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.core.config import settings

api_v1_router = APIRouter(prefix=settings.API_V1_PREFIX)
api_v1_router.include_router(health_router)
