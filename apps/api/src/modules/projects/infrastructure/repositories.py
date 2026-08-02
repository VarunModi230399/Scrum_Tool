import uuid
from datetime import date
from typing import Any

from sqlalchemy import delete as sa_delete
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.projects.domain.entities import (
    DependencyType,
    Priority,
    Project,
    ProjectStatus,
    Risk,
    WorkItem,
    WorkItemDependency,
    WorkItemStatus,
    WorkItemType,
)
from src.modules.projects.infrastructure.models import (
    ProjectModel,
    WorkItemDependencyModel,
    WorkItemModel,
)


def _project_to_entity(model: ProjectModel) -> Project:
    return Project(
        id=model.id,
        workspace_id=model.workspace_id,
        key=model.key,
        name=model.name,
        description=model.description,
        status=ProjectStatus(model.status),
        progress=float(model.progress),
        progress_override=float(model.progress_override)
        if model.progress_override is not None
        else None,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _work_item_to_entity(model: WorkItemModel) -> WorkItem:
    return WorkItem(
        id=model.id,
        project_id=model.project_id,
        parent_id=model.parent_id,
        type=WorkItemType(model.type),
        path=model.path,
        depth=model.depth,
        title=model.title,
        description=model.description,
        acceptance_criteria=model.acceptance_criteria,
        status=WorkItemStatus(model.status),
        priority=Priority(model.priority),
        risk=Risk(model.risk) if model.risk else None,
        story_points=float(model.story_points) if model.story_points is not None else None,
        estimated_hours=float(model.estimated_hours) if model.estimated_hours is not None else None,
        actual_hours=float(model.actual_hours) if model.actual_hours is not None else None,
        start_date=model.start_date,
        due_date=model.due_date,
        owner_id=model.owner_id,
        reviewer_id=model.reviewer_id,
        progress=float(model.progress),
        progress_override=float(model.progress_override)
        if model.progress_override is not None
        else None,
        position=model.position,
        created_by=model.created_by,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _dependency_to_entity(model: WorkItemDependencyModel) -> WorkItemDependency:
    return WorkItemDependency(
        id=model.id,
        work_item_id=model.work_item_id,
        depends_on_id=model.depends_on_id,
        type=DependencyType(model.type),
        created_at=model.created_at,
    )


class SqlAlchemyProjectRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, project_id: uuid.UUID) -> Project | None:
        model = await self._session.get(ProjectModel, project_id)
        return _project_to_entity(model) if model else None

    async def get_by_key(self, workspace_id: uuid.UUID, key: str) -> Project | None:
        result = await self._session.execute(
            select(ProjectModel).where(
                ProjectModel.workspace_id == workspace_id, ProjectModel.key == key
            )
        )
        model = result.scalar_one_or_none()
        return _project_to_entity(model) if model else None

    async def list_for_workspace(self, workspace_id: uuid.UUID) -> list[Project]:
        result = await self._session.execute(
            select(ProjectModel).where(ProjectModel.workspace_id == workspace_id)
        )
        return [_project_to_entity(m) for m in result.scalars().all()]

    async def create(
        self, *, workspace_id: uuid.UUID, key: str, name: str, description: str | None
    ) -> Project:
        model = ProjectModel(workspace_id=workspace_id, key=key, name=name, description=description)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _project_to_entity(model)

    async def update(self, project_id: uuid.UUID, fields: dict[str, Any]) -> Project:
        model = await self._session.get(ProjectModel, project_id)
        if model is None:
            raise ValueError(f"Project {project_id} not found")
        for key, value in fields.items():
            setattr(model, key, value.value if isinstance(value, ProjectStatus) else value)
        await self._session.flush()
        await self._session.refresh(model)
        return _project_to_entity(model)

    async def set_progress(self, project_id: uuid.UUID, progress: float) -> Project:
        model = await self._session.get(ProjectModel, project_id)
        if model is None:
            raise ValueError(f"Project {project_id} not found")
        model.progress = progress
        await self._session.flush()
        await self._session.refresh(model)
        return _project_to_entity(model)

    async def set_progress_override(
        self, project_id: uuid.UUID, progress_override: float | None
    ) -> Project:
        model = await self._session.get(ProjectModel, project_id)
        if model is None:
            raise ValueError(f"Project {project_id} not found")
        model.progress_override = progress_override
        await self._session.flush()
        await self._session.refresh(model)
        return _project_to_entity(model)


class SqlAlchemyWorkItemRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, work_item_id: uuid.UUID) -> WorkItem | None:
        model = await self._session.get(WorkItemModel, work_item_id)
        return _work_item_to_entity(model) if model else None

    async def list_for_project(
        self,
        project_id: uuid.UUID,
        *,
        type: WorkItemType | None = None,
        status: WorkItemStatus | None = None,
        owner_id: uuid.UUID | None = None,
        parent_id: uuid.UUID | None = None,
    ) -> list[WorkItem]:
        query = select(WorkItemModel).where(WorkItemModel.project_id == project_id)
        if type is not None:
            query = query.where(WorkItemModel.type == type.value)
        if status is not None:
            query = query.where(WorkItemModel.status == status.value)
        if owner_id is not None:
            query = query.where(WorkItemModel.owner_id == owner_id)
        if parent_id is not None:
            query = query.where(WorkItemModel.parent_id == parent_id)
        result = await self._session.execute(query)
        return [_work_item_to_entity(m) for m in result.scalars().all()]

    async def list_children(self, parent_id: uuid.UUID) -> list[WorkItem]:
        result = await self._session.execute(
            select(WorkItemModel).where(WorkItemModel.parent_id == parent_id)
        )
        return [_work_item_to_entity(m) for m in result.scalars().all()]

    async def list_ancestors(self, work_item: WorkItem) -> list[WorkItem]:
        ancestor_ids = [uuid.UUID(part) for part in work_item.path.split(".")[:-1]]
        if not ancestor_ids:
            return []
        result = await self._session.execute(
            select(WorkItemModel).where(WorkItemModel.id.in_(ancestor_ids))
        )
        by_id = {m.id: m for m in result.scalars().all()}
        return [_work_item_to_entity(by_id[aid]) for aid in ancestor_ids if aid in by_id]

    async def create(
        self,
        *,
        project_id: uuid.UUID,
        parent_id: uuid.UUID | None,
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
        owner_id: uuid.UUID | None,
        reviewer_id: uuid.UUID | None,
        created_by: uuid.UUID,
    ) -> WorkItem:
        new_id = uuid.uuid4()
        if parent_id is not None:
            parent = await self._session.get(WorkItemModel, parent_id)
            if parent is None:
                raise ValueError(f"Parent work item {parent_id} not found")
            path = f"{parent.path}.{new_id}"
            depth = parent.depth + 1
        else:
            path = str(new_id)
            depth = 0

        model = WorkItemModel(
            id=new_id,
            project_id=project_id,
            parent_id=parent_id,
            type=type.value,
            path=path,
            depth=depth,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            priority=priority.value,
            risk=risk.value if risk else None,
            story_points=story_points,
            estimated_hours=estimated_hours,
            start_date=start_date,
            due_date=due_date,
            owner_id=owner_id,
            reviewer_id=reviewer_id,
            created_by=created_by,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _work_item_to_entity(model)

    async def update(self, work_item_id: uuid.UUID, fields: dict[str, Any]) -> WorkItem:
        model = await self._session.get(WorkItemModel, work_item_id)
        if model is None:
            raise ValueError(f"Work item {work_item_id} not found")
        for key, value in fields.items():
            if hasattr(value, "value") and isinstance(
                value, WorkItemStatus | Priority | Risk | WorkItemType
            ):
                value = value.value
            setattr(model, key, value)
        await self._session.flush()
        await self._session.refresh(model)
        return _work_item_to_entity(model)

    async def delete(self, work_item_id: uuid.UUID) -> None:
        """Deletes the work item and its subtree (deleting an Epic deletes its Stories/Tasks)."""
        model = await self._session.get(WorkItemModel, work_item_id)
        if model is None:
            return
        await self._session.execute(
            sa_delete(WorkItemModel).where(
                or_(WorkItemModel.path.like(f"{model.path}.%"), WorkItemModel.id == work_item_id)
            )
        )
        await self._session.flush()

    async def move(self, work_item: WorkItem, new_parent_id: uuid.UUID | None) -> WorkItem:
        model = await self._session.get(WorkItemModel, work_item.id)
        if model is None:
            raise ValueError(f"Work item {work_item.id} not found")

        old_prefix = work_item.path
        if new_parent_id is not None:
            new_parent = await self._session.get(WorkItemModel, new_parent_id)
            if new_parent is None:
                raise ValueError(f"Parent work item {new_parent_id} not found")
            new_prefix = f"{new_parent.path}.{model.id}"
            new_depth = new_parent.depth + 1
        else:
            new_prefix = str(model.id)
            new_depth = 0
        depth_delta = new_depth - model.depth

        result = await self._session.execute(
            select(WorkItemModel).where(WorkItemModel.path.like(f"{old_prefix}.%"))
        )
        for descendant in result.scalars().all():
            descendant.path = new_prefix + descendant.path[len(old_prefix) :]
            descendant.depth += depth_delta

        model.parent_id = new_parent_id
        model.path = new_prefix
        model.depth = new_depth
        await self._session.flush()
        await self._session.refresh(model)
        return _work_item_to_entity(model)

    async def set_progress(self, work_item_id: uuid.UUID, progress: float) -> WorkItem:
        model = await self._session.get(WorkItemModel, work_item_id)
        if model is None:
            raise ValueError(f"Work item {work_item_id} not found")
        model.progress = progress
        await self._session.flush()
        await self._session.refresh(model)
        return _work_item_to_entity(model)

    async def set_progress_override(
        self, work_item_id: uuid.UUID, progress_override: float | None
    ) -> WorkItem:
        model = await self._session.get(WorkItemModel, work_item_id)
        if model is None:
            raise ValueError(f"Work item {work_item_id} not found")
        model.progress_override = progress_override
        await self._session.flush()
        await self._session.refresh(model)
        return _work_item_to_entity(model)


class SqlAlchemyWorkItemDependencyRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_work_item(self, work_item_id: uuid.UUID) -> list[WorkItemDependency]:
        result = await self._session.execute(
            select(WorkItemDependencyModel).where(
                WorkItemDependencyModel.work_item_id == work_item_id
            )
        )
        return [_dependency_to_entity(m) for m in result.scalars().all()]

    async def get(
        self, work_item_id: uuid.UUID, depends_on_id: uuid.UUID
    ) -> WorkItemDependency | None:
        result = await self._session.execute(
            select(WorkItemDependencyModel).where(
                WorkItemDependencyModel.work_item_id == work_item_id,
                WorkItemDependencyModel.depends_on_id == depends_on_id,
            )
        )
        model = result.scalar_one_or_none()
        return _dependency_to_entity(model) if model else None

    async def create(
        self, *, work_item_id: uuid.UUID, depends_on_id: uuid.UUID, type: DependencyType
    ) -> WorkItemDependency:
        model = WorkItemDependencyModel(
            work_item_id=work_item_id, depends_on_id=depends_on_id, type=type.value
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _dependency_to_entity(model)

    async def delete(self, dependency_id: uuid.UUID) -> None:
        model = await self._session.get(WorkItemDependencyModel, dependency_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()
