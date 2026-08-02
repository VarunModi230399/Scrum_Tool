from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"


class WorkItemType(StrEnum):
    EPIC = "epic"
    FEATURE = "feature"
    STORY = "story"
    TASK = "task"
    SUBTASK = "subtask"
    CHECKLIST_ITEM = "checklist_item"


class WorkItemStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    BLOCKED = "blocked"
    DONE = "done"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Risk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DependencyType(StrEnum):
    BLOCKS = "blocks"
    RELATES_TO = "relates_to"


@dataclass
class Project:
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


@dataclass
class WorkItem:
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

    @property
    def effective_progress(self) -> float:
        return self.progress_override if self.progress_override is not None else self.progress


@dataclass
class WorkItemDependency:
    id: UUID
    work_item_id: UUID
    depends_on_id: UUID
    type: DependencyType
    created_at: datetime
