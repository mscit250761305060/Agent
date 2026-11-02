from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Optional
import uuid

from sqlalchemy import (
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
    from app.models.agent import Agent
    from app.models.user import User
    from app.models.workflow import WorkflowRun


class Task(Base):
    """Task unit representing discrete execution goals, standalone prompts, or workflow graph steps."""

    __tablename__ = "tasks"

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
    workflow_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    assigned_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    parent_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    input_data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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
        back_populates="tasks",
        foreign_keys=[user_id],
        overlaps="parent_task,subtasks,workflow_run",
    )
    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="tasks",
        primaryjoin="and_(Task.workflow_run_id == WorkflowRun.id, Task.user_id == WorkflowRun.user_id)",
        overlaps="user,tasks,parent_task,subtasks",
    )
    assigned_agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="tasks",
    )
    parent_task: Mapped[Optional["Task"]] = relationship(
        "Task",
        back_populates="subtasks",
        primaryjoin="and_(Task.parent_task_id == Task.id, Task.user_id == Task.user_id)",
        remote_side="[Task.id, Task.user_id]",
        overlaps="user,workflow_run,tasks,subtasks",
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="parent_task",
        primaryjoin="and_(Task.parent_task_id == Task.id, Task.user_id == Task.user_id)",
        cascade="all, delete-orphan",
        overlaps="user,workflow_run,tasks,parent_task",
    )
    executions: Mapped[list["TaskExecution"]] = relationship(
        "TaskExecution",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("id", "user_id", name="uq_tasks_id_user"),
        ForeignKeyConstraint(
            ["workflow_run_id", "user_id"],
            ["workflow_runs.id", "workflow_runs.user_id"],
            ondelete="CASCADE",
            name="fk_tasks_workflow_run_user",
        ),
        ForeignKeyConstraint(
            ["parent_task_id", "user_id"],
            ["tasks.id", "tasks.user_id"],
            ondelete="CASCADE",
            name="fk_tasks_parent_task_user",
        ),
        CheckConstraint(
            "status IN ('pending', 'queued', 'assigned', 'running', 'completed', 'failed', 'cancelled', 'retrying')",
            name="chk_tasks_status",
        ),
        CheckConstraint(
            "priority >= 0 AND priority <= 1000",
            name="chk_tasks_priority",
        ),
        Index("idx_tasks_queue_dispatch", "status", "priority", "created_at"),
        Index("idx_tasks_agent", "assigned_agent_id"),
    )


class TaskExecution(Base):
    """Detailed record of an individual execution attempt with micro-cent cost and token tracking."""

    __tablename__ = "task_executions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="started",
    )
    model_used: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    result_data: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    cached_prompt_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    completion_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    reasoning_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    total_tokens: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 6),
        nullable=False,
        default=Decimal("0.000000"),
    )
    latency_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    task: Mapped["Task"] = relationship(
        "Task",
        back_populates="executions",
    )
    agent: Mapped[Optional["Agent"]] = relationship(
        "Agent",
        back_populates="task_executions",
    )

    __table_args__ = (
        UniqueConstraint("task_id", "attempt_number", name="uq_task_executions_task_attempt"),
        CheckConstraint("attempt_number >= 1", name="chk_task_executions_attempt"),
        CheckConstraint(
            "status IN ('started', 'streaming', 'completed', 'failed', 'timed_out', 'cancelled')",
            name="chk_task_executions_status",
        ),
        CheckConstraint("prompt_tokens >= 0", name="chk_task_executions_prompt_tokens"),
        CheckConstraint(
            "cached_prompt_tokens >= 0 AND cached_prompt_tokens <= prompt_tokens",
            name="chk_task_executions_cached_tokens",
        ),
        CheckConstraint("completion_tokens >= 0", name="chk_task_executions_completion_tokens"),
        CheckConstraint(
            "reasoning_tokens >= 0 AND reasoning_tokens <= completion_tokens",
            name="chk_task_executions_reasoning_tokens",
        ),
        CheckConstraint(
            "total_tokens = prompt_tokens + completion_tokens",
            name="chk_task_executions_total_tokens",
        ),
        CheckConstraint("cost_usd >= 0.000000", name="chk_task_executions_cost"),
        CheckConstraint("latency_ms IS NULL OR latency_ms >= 0", name="chk_task_executions_latency"),
        Index("idx_task_executions_task", "task_id"),
        Index("idx_task_executions_cost", "model_used", "cost_usd"),
    )
