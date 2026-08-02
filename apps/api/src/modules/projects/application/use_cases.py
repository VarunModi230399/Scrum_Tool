from datetime import date
from typing import Any
from uuid import UUID

from src.modules.projects.application.ports import (
    ProjectRepository,
    WorkItemDependencyRepository,
    WorkItemRepository,
)
from src.modules.projects.application.progress import ProgressRollupService
from src.modules.projects.domain.entities import (
    DependencyType,
    Priority,
    Project,
    Risk,
    WorkItem,
    WorkItemDependency,
    WorkItemType,
)
from src.shared_kernel.errors import ConflictError, NotFoundError, ValidationError


class CreateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._projects = project_repo

    async def execute(
        self, *, workspace_id: UUID, key: str, name: str, description: str | None
    ) -> Project:
        if await self._projects.get_by_key(workspace_id, key) is not None:
            raise ConflictError(f"Project key '{key}' is already used in this workspace")
        return await self._projects.create(
            workspace_id=workspace_id, key=key, name=name, description=description
        )


class UpdateProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._projects = project_repo

    async def execute(self, project_id: UUID, fields: dict[str, Any]) -> Project:
        if await self._projects.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        return await self._projects.update(project_id, fields)


class ArchiveProjectUseCase:
    def __init__(self, project_repo: ProjectRepository):
        self._projects = project_repo

    async def execute(self, project_id: UUID) -> Project:
        if await self._projects.get_by_id(project_id) is None:
            raise NotFoundError("Project not found")
        return await self._projects.update(project_id, {"status": "archived"})


class CreateWorkItemUseCase:
    def __init__(self, work_item_repo: WorkItemRepository, rollup: ProgressRollupService):
        self._work_items = work_item_repo
        self._rollup = rollup

    async def execute(
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
    ) -> WorkItem:
        parent = None
        if parent_id is not None:
            parent = await self._work_items.get_by_id(parent_id)
            if parent is None:
                raise NotFoundError("Parent work item not found")
            if parent.project_id != project_id:
                raise ValidationError("Parent work item belongs to a different project")

        work_item = await self._work_items.create(
            project_id=project_id,
            parent_id=parent_id,
            type=type,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority,
            risk=risk,
            story_points=story_points,
            estimated_hours=estimated_hours,
            start_date=start_date,
            due_date=due_date,
            owner_id=owner_id,
            reviewer_id=reviewer_id,
            created_by=created_by,
        )
        if parent is not None:
            await self._rollup.recompute(parent)
        return work_item


class UpdateWorkItemUseCase:
    def __init__(self, work_item_repo: WorkItemRepository, rollup: ProgressRollupService):
        self._work_items = work_item_repo
        self._rollup = rollup

    async def execute(self, work_item_id: UUID, fields: dict[str, Any]) -> WorkItem:
        if await self._work_items.get_by_id(work_item_id) is None:
            raise NotFoundError("Work item not found")
        updated = await self._work_items.update(work_item_id, fields)
        await self._rollup.recompute(updated)
        # recompute() may have rewritten this item's own `progress` (e.g. a status
        # change on a leaf); re-fetch so the response reflects that, not the
        # pre-rollup snapshot.
        refreshed = await self._work_items.get_by_id(work_item_id)
        return refreshed if refreshed is not None else updated


class DeleteWorkItemUseCase:
    def __init__(self, work_item_repo: WorkItemRepository, rollup: ProgressRollupService):
        self._work_items = work_item_repo
        self._rollup = rollup

    async def execute(self, work_item_id: UUID) -> None:
        work_item = await self._work_items.get_by_id(work_item_id)
        if work_item is None:
            raise NotFoundError("Work item not found")
        await self._work_items.delete(work_item_id)
        if work_item.parent_id is not None:
            parent = await self._work_items.get_by_id(work_item.parent_id)
            if parent is not None:
                await self._rollup.recompute(parent)


class MoveWorkItemUseCase:
    def __init__(self, work_item_repo: WorkItemRepository, rollup: ProgressRollupService):
        self._work_items = work_item_repo
        self._rollup = rollup

    async def execute(self, work_item_id: UUID, new_parent_id: UUID | None) -> WorkItem:
        work_item = await self._work_items.get_by_id(work_item_id)
        if work_item is None:
            raise NotFoundError("Work item not found")

        if new_parent_id == work_item_id:
            raise ValidationError("A work item cannot be moved under itself")

        new_parent = None
        if new_parent_id is not None:
            new_parent = await self._work_items.get_by_id(new_parent_id)
            if new_parent is None:
                raise NotFoundError("Target parent work item not found")
            if new_parent.project_id != work_item.project_id:
                raise ValidationError("Cannot move a work item to a different project")
            if new_parent.path.startswith(f"{work_item.path}."):
                raise ValidationError("Cannot move a work item into one of its own descendants")

        old_parent_id = work_item.parent_id
        moved = await self._work_items.move(work_item, new_parent_id)

        if old_parent_id is not None:
            old_parent = await self._work_items.get_by_id(old_parent_id)
            if old_parent is not None:
                await self._rollup.recompute(old_parent)
        if new_parent is not None:
            await self._rollup.recompute(new_parent)
        return moved


class SetProgressOverrideUseCase:
    def __init__(self, work_item_repo: WorkItemRepository, rollup: ProgressRollupService):
        self._work_items = work_item_repo
        self._rollup = rollup

    async def execute(self, work_item_id: UUID, progress_override: float | None) -> WorkItem:
        if await self._work_items.get_by_id(work_item_id) is None:
            raise NotFoundError("Work item not found")
        updated = await self._work_items.set_progress_override(work_item_id, progress_override)
        await self._rollup.recompute(updated)
        return updated


class AddDependencyUseCase:
    def __init__(
        self, dependency_repo: WorkItemDependencyRepository, work_item_repo: WorkItemRepository
    ):
        self._dependencies = dependency_repo
        self._work_items = work_item_repo

    async def execute(
        self, *, work_item_id: UUID, depends_on_id: UUID, type: DependencyType
    ) -> WorkItemDependency:
        if work_item_id == depends_on_id:
            raise ValidationError("A work item cannot depend on itself")
        if await self._work_items.get_by_id(work_item_id) is None:
            raise NotFoundError("Work item not found")
        if await self._work_items.get_by_id(depends_on_id) is None:
            raise NotFoundError("Dependency target work item not found")
        if await self._dependencies.get(work_item_id, depends_on_id) is not None:
            raise ConflictError("This dependency already exists")
        # Direct reverse-edge check only; full transitive cycle detection across the
        # dependency graph is deferred until the Dependency Graph view (Phase 2) needs it.
        if await self._dependencies.get(depends_on_id, work_item_id) is not None:
            raise ValidationError("This would create a circular dependency")

        return await self._dependencies.create(
            work_item_id=work_item_id, depends_on_id=depends_on_id, type=type
        )


class RemoveDependencyUseCase:
    def __init__(self, dependency_repo: WorkItemDependencyRepository):
        self._dependencies = dependency_repo

    async def execute(self, dependency_id: UUID) -> None:
        await self._dependencies.delete(dependency_id)
