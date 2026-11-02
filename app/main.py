from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import close_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application lifecycle events (startup and shutdown)."""
    yield
    # Gracefully dispose database connection pool upon server shutdown
    await close_db_connection()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Intelligent orchestration platform for coordinated multi-agent workflows.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Mount API routers
app.include_router(api_v1_router)


class RootResponse(BaseModel):
    """Schema for root endpoint response with service navigation."""

    name: str = Field(
        ...,
        description="Service name",
        examples=["Advanced Multi-Agent AI Orchestrator"],
    )
    version: str = Field(
        ...,
        description="Current service version",
        examples=["0.1.0"],
    )
    description: str = Field(
        ...,
        description="Brief summary of service purpose",
        examples=["Advanced Multi-Agent AI Orchestrator API"],
    )
    docs_url: str = Field(
        ...,
        description="Interactive OpenAPI documentation URL",
        examples=["/docs"],
    )
    health_url: str = Field(
        ...,
        description="Service health check URL",
        examples=["/api/v1/health"],
    )


@app.get(
    "/",
    response_model=RootResponse,
    tags=["Root"],
    summary="API Root Information",
    description="Provides basic API metadata, documentation URL, and health check route.",
)
async def root() -> RootResponse:
    """Root endpoint providing basic API information and navigation links."""
    return RootResponse(
        name=settings.PROJECT_NAME,
        version=settings.APP_VERSION,
        description="Advanced Multi-Agent AI Orchestrator API",
        docs_url="/docs",
        health_url=f"{settings.API_V1_PREFIX}/health",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development"),
    )
