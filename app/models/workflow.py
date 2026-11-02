from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


class Workflow(Base):
    """Workflow blueprint definition capturing multi-agent orchestration topologies."""

    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    is_latest: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
    )
    definition: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
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
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workflows",
    )
    runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="workflow",
        overlaps="workflow_runs,user",
    )

    __table_args__ = (
        UniqueConstraint("user_id", "slug", "version", name="uq_workflows_user_slug_version"),
        UniqueConstraint("id", "user_id", name="uq_workflows_id_user"),
        CheckConstraint(
            "status IN ('draft', 'active', 'paused', 'archived')",
            name="chk_workflows_status",
        ),
        CheckConstraint(
            "version >= 1",
            name="chk_workflows_version",
        ),
        Index(
            "uq_workflows_single_latest_version",
            "user_id",
            "slug",
            unique=True,
            postgresql_where=(is_latest == True),  # noqa: E712
        ),
    )


class WorkflowRun(Base):
    """Workflow execution instance capturing runtime inputs, frozen definition, and outputs."""

    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    output_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    definition_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0.000000"),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
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
    workflow: Mapped["Workflow"] = relationship(
        "Workflow",
        back_populates="runs",
        primaryjoin="and_(WorkflowRun.workflow_id == Workflow.id, WorkflowRun.user_id == Workflow.user_id)",
        overlaps="workflow_runs,user,runs",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="workflow_runs",
        foreign_keys=[user_id],
        overlaps="runs,workflow",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="workflow_run",
        overlaps="parent_task,subtasks,tasks,user",
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["workflow_id", "user_id"],
            ["workflows.id", "workflows.user_id"],
            ondelete="RESTRICT",
            name="fk_workflow_runs_workflow_user",
        ),
        UniqueConstraint("id", "user_id", name="uq_workflow_runs_id_user"),
        CheckConstraint(
            "status IN ('pending', 'running', 'paused', 'completed', 'failed', 'cancelled')",
            name="chk_workflow_runs_status",
        ),
        CheckConstraint(
            "total_tokens >= 0",
            name="chk_workflow_runs_total_tokens",
        ),
        CheckConstraint(
            "total_cost_usd >= 0.000000",
            name="chk_workflow_runs_total_cost",
        ),
        Index("idx_workflow_runs_dispatch", "user_id", "status", "created_at"),
    )
