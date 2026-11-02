from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Schema for system health check response."""

    status: str = Field(
        ...,
        description="Overall operational status of the service",
        examples=["healthy"],
    )
    application_name: str = Field(
        ...,
        description="Application name",
        examples=["Advanced Multi-Agent AI Orchestrator"],
    )
    application_version: str = Field(
        ...,
        description="Semantic version of the application",
        examples=["0.1.0"],
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Returns the operational status, application name, and version.",
)
async def get_health() -> HealthResponse:
    """Health check endpoint returning system status and application metadata."""
    return HealthResponse(
        status="healthy",
        application_name=settings.PROJECT_NAME,
        application_version=settings.APP_VERSION,
    )
