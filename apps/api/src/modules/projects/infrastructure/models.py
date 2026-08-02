import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.platform.db import Base


class ProjectModel(Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("workspace_id", "key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    key: Mapped[str] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="active")
    progress: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    progress_override: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class WorkItemModel(Base):
    __tablename__ = "work_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("work_items.id"), nullable=True)
    type: Mapped[str] = mapped_column(nullable=False)
    path: Mapped[str] = mapped_column(nullable=False)
    depth: Mapped[int] = mapped_column(nullable=False, default=0)
    title: Mapped[str] = mapped_column(nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    acceptance_criteria: Mapped[str | None] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False, default="todo")
    priority: Mapped[str] = mapped_column(nullable=False, default="medium")
    risk: Mapped[str | None] = mapped_column(nullable=True)
    story_points: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    estimated_hours: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    actual_hours: Mapped[float | None] = mapped_column(Numeric(7, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    progress: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    progress_override: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    position: Mapped[int] = mapped_column(nullable=False, default=0)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_work_items_path", "path", postgresql_ops={"path": "text_pattern_ops"}),
        Index("idx_work_items_parent", "parent_id"),
        Index("idx_work_items_project", "project_id"),
    )


class WorkItemDependencyModel(Base):
    __tablename__ = "work_item_dependencies"
    __table_args__ = (UniqueConstraint("work_item_id", "depends_on_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    work_item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id"), nullable=False)
    depends_on_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_items.id"), nullable=False)
    type: Mapped[str] = mapped_column(nullable=False, default="blocks")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
