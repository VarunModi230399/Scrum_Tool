from datetime import date
from typing import Any, Protocol
from uuid import UUID

from src.modules.projects.domain.entities import (
    DependencyType,
    Priority,
    Project,
    Risk,
    WorkItem,
    WorkItemDependency,
    WorkItemStatus,
    WorkItemType,
)


class ProjectRepository(Protocol):
    async def get_by_id(self, project_id: UUID) -> Project | None: ...
    async def get_by_key(self, workspace_id: UUID, key: str) -> Project | None: ...
    async def list_for_workspace(self, workspace_id: UUID) -> list[Project]: ...
    async def create(
        self, *, workspace_id: UUID, key: str, name: str, description: str | None
    ) -> Project: ...
    async def update(self, project_id: UUID, fields: dict[str, Any]) -> Project: ...
    async def set_progress(self, project_id: UUID, progress: float) -> Project: ...
    async def set_progress_override(
        self, project_id: UUID, progress_override: float | None
    ) -> Project: ...


class WorkItemRepository(Protocol):
    async def get_by_id(self, work_item_id: UUID) -> WorkItem | None: ...
    async def list_for_project(
        self,
        project_id: UUID,
        *,
        type: WorkItemType | None = None,
        status: WorkItemStatus | None = None,
        owner_id: UUID | None = None,
        parent_id: UUID | None = None,
    ) -> list[WorkItem]: ...
    async def list_children(self, parent_id: UUID) -> list[WorkItem]: ...
    async def list_ancestors(self, work_item: WorkItem) -> list[WorkItem]: ...
    async def create(
        self,
        *,
        project_id: UUID,
        parent_id: UUID | None,
        type: WorkItemType,
        title: str,
        description: str | None,
        acceptance_criteria: str | None,
        priority: Priority,
        risk: Risk | None,
        story_points: float | None,
        estimated_hours: float | None,
        start_date: date | None,
        due_date: date | None,
        owner_id: UUID | None,
        reviewer_id: UUID | None,
        created_by: UUID,
    ) -> WorkItem: ...
    async def update(self, work_item_id: UUID, fields: dict[str, Any]) -> WorkItem: ...
    async def delete(self, work_item_id: UUID) -> None: ...
    async def move(self, work_item: WorkItem, new_parent_id: UUID | None) -> WorkItem: ...
    async def set_progress(self, work_item_id: UUID, progress: float) -> WorkItem: ...
    async def set_progress_override(
        self, work_item_id: UUID, progress_override: float | None
    ) -> WorkItem: ...


class WorkItemDependencyRepository(Protocol):
    async def list_for_work_item(self, work_item_id: UUID) -> list[WorkItemDependency]: ...
    async def get(self, work_item_id: UUID, depends_on_id: UUID) -> WorkItemDependency | None: ...
    async def create(
        self, *, work_item_id: UUID, depends_on_id: UUID, type: DependencyType
    ) -> WorkItemDependency: ...
    async def delete(self, dependency_id: UUID) -> None: ...
