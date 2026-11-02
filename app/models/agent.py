from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.task import Task, TaskExecution
    from app.models.user import User

# Standardized 8 Fixed Manager Agent Roles & Slugs
SYSTEM_MANAGER_ROLES: dict[str, str] = {
    "manager-planning": "Planning Manager",
    "manager-development": "Development Manager",
    "manager-research": "Research Manager",
    "manager-quality": "Quality Manager",
    "manager-resource-cost": "Resource & Cost Manager",
    "manager-security": "Security Manager",
    "manager-communication": "Communication Manager",
    "manager-deployment": "Deployment Manager",
}


class Agent(Base):
    """Agent entity representing both 8 fixed system managers and dynamic user specialists."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="specialist",
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    lifecycle_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    model_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    temperature: Mapped[Decimal] = mapped_column(
        Numeric(3, 2),
        nullable=False,
        default=Decimal("0.70"),
    )
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    max_concurrency: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    total_runs: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="agents",
    )
    agent_capabilities: Mapped[list["AgentCapability"]] = relationship(
        "AgentCapability",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    capabilities: Mapped[list["Capability"]] = relationship(
        "Capability",
        secondary="agent_capabilities",
        back_populates="agents",
        viewonly=True,
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="assigned_agent",
    )
    task_executions: Mapped[list["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="agent",
    )

    __table_args__ = (
        CheckConstraint(
            "agent_type IN ('manager', 'specialist')",
            name="chk_agents_agent_type",
        ),
        CheckConstraint(
            "lifecycle_status IN ('draft', 'initializing', 'active', 'busy', 'paused', 'deprecated', 'terminated')",
            name="chk_agents_lifecycle_status",
        ),
        CheckConstraint(
            "temperature >= 0.00 AND temperature <= 2.00",
            name="chk_agents_temperature",
        ),
        CheckConstraint(
            "max_tokens IS NULL OR max_tokens > 0",
            name="chk_agents_max_tokens",
        ),
        CheckConstraint(
            "max_concurrency >= 1 AND max_concurrency <= 100",
            name="chk_agents_max_concurrency",
        ),
        CheckConstraint(
            "total_runs >= 0",
            name="chk_agents_total_runs",
        ),
        CheckConstraint(
            "((is_system = TRUE AND user_id IS NULL AND agent_type = 'manager') OR "
            "(is_system = FALSE AND user_id IS NOT NULL AND agent_type = 'specialist'))",
            name="chk_agent_tier_ownership",
        ),
        Index(
            "uq_agents_system_slug",
            "slug",
            unique=True,
            postgresql_where=(user_id.is_(None)),
        ),
        Index(
            "uq_agents_user_slug",
            "user_id",
            "slug",
            unique=True,
            postgresql_where=(user_id.is_not(None)),
        ),
        Index(
            "idx_agents_lookup",
            "agent_type",
            "lifecycle_status",
        ),
    )


class Capability(Base):
    """Tool or skill integration available to agents."""

    __tablename__ = "capabilities"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    display_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    parameters_schema: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    agent_capabilities: Mapped[list["AgentCapability"]] = relationship(
        "AgentCapability",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        secondary="agent_capabilities",
        back_populates="capabilities",
        viewonly=True,
    )


class AgentCapability(Base):
    """Junction entity mapping agents to granted capabilities with agent-specific configuration."""

    __tablename__ = "agent_capabilities"

    agent_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    capability_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("capabilities.id", ondelete="CASCADE"),
        primary_key=True,
    )
    config: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Relationships
    agent: Mapped["Agent"] = relationship(
        "Agent",
        back_populates="agent_capabilities",
    )
    capability: Mapped["Capability"] = relationship(
        "Capability",
        back_populates="agent_capabilities",
    )

    __table_args__ = (
        Index("idx_agent_capabilities_cap", "capability_id"),
    )

