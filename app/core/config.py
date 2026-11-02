from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = Field(
        default="Advanced Multi-Agent AI Orchestrator",
        description="Application display name",
    )
    APP_VERSION: str = Field(
        default="0.1.0",
        description="Application semantic version",
    )
    API_V1_PREFIX: str = Field(
        default="/api/v1",
        description="Prefix path for version 1 API routes",
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment (development, staging, production)",
    )
    HOST: str = Field(
        default="127.0.0.1",
        description="Host interface for server binding",
    )
    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="TCP port for server binding",
    )
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://agent_orchestrator_user:change_me@localhost:5433/agent_orchestrator",
        description="Async PostgreSQL connection string",
    )
    DB_POOL_SIZE: int = Field(
        default=5,
        ge=1,
        le=50,
        description="SQLAlchemy connection pool size",
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        le=50,
        description="SQLAlchemy connection pool max overflow",
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="Connection pool timeout in seconds",
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )


settings = Settings()
