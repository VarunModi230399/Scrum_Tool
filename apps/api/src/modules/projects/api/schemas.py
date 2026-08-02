from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.modules.projects.domain.entities import (
    DependencyType,
    Priority,
    ProjectStatus,
    Risk,
    WorkItemStatus,
    WorkItemType,
)

# --- Projects ---


class CreateProjectRequest(BaseModel):
    key: str = Field(min_length=1, max_length=10, pattern=r"^[A-Za-z][A-Za-z0-9]*$")
    name: str = Field(min_length=1)
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(BaseModel):
    id: UUID
    workspace_id: UUID
    key: str
    name: str
    description: str | None
    status: ProjectStatus
    progress: float
    progress_override: float | None
    created_at: datetime
    updated_at: datetime


# --- Work items ---


class CreateWorkItemRequest(BaseModel):
    parent_id: UUID | None = None
    type: WorkItemType
    title: str = Field(min_length=1)
    description: str | None = None
    acceptance_criteria: str | None = None
    priority: Priority = Priority.MEDIUM
    risk: Risk | None = None
    story_points: float | None = None
    estimated_hours: float | None = None
    start_date: date | None = None
    due_date: date | None = None
    owner_id: UUID | None = None
    reviewer_id: UUID | None = None


class UpdateWorkItemRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    acceptance_criteria: str | None = None
    status: WorkItemStatus | None = None
    priority: Priority | None = None
    risk: Risk | None = None
    story_points: float | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None
    start_date: date | None = None
    due_date: date | None = None
    owner_id: UUID | None = None
    reviewer_id: UUID | None = None


class MoveWorkItemRequest(BaseModel):
    new_parent_id: UUID | None = None


class SetProgressOverrideRequest(BaseModel):
    value: float | None = Field(default=None, ge=0, le=100)


class WorkItemOut(BaseModel):
    id: UUID
    project_id: UUID
    parent_id: UUID | None
    type: WorkItemType
    path: str
    depth: int
    title: str
    description: str | None
    acceptance_criteria: str | None
    status: WorkItemStatus
    priority: Priority
    risk: Risk | None
    story_points: float | None
    estimated_hours: float | None
    actual_hours: float | None
    start_date: date | None
    due_date: date | None
    owner_id: UUID | None
    reviewer_id: UUID | None
    progress: float
    progress_override: float | None
    position: int
    created_by: UUID
    created_at: datetime
    updated_at: datetime


class AddDependencyRequest(BaseModel):
    depends_on_id: UUID
    type: DependencyType = DependencyType.BLOCKS


class WorkItemDependencyOut(BaseModel):
    id: UUID
    work_item_id: UUID
    depends_on_id: UUID
    type: DependencyType
    created_at: datetime
