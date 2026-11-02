from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.agent import Agent
    from app.models.task import Task
    from app.models.workflow import Workflow, WorkflowRun


class User(Base):
    """User account entity representing platform operators, developers, and administrators."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True,
    )
    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="user",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
    agents: Mapped[list["Agent"]] = relationship(
        "Agent",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workflows: Mapped[list["Workflow"]] = relationship(
        "Workflow",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    workflow_runs: Mapped[list["WorkflowRun"]] = relationship(
        "WorkflowRun",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
        overlaps="parent_task,subtasks,workflow_run",
    )

    __table_args__ = (
        CheckConstraint(
            "role IN ('admin', 'developer', 'user', 'service')",
            name="chk_users_role",
        ),
        Index("idx_users_active", "id", postgresql_where=(is_active == True)),  # noqa: E712
    )
