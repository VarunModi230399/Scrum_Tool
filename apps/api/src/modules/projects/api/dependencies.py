from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.dependencies import get_current_user
from src.modules.identity.domain.entities import User, WorkspaceRole
from src.modules.identity.infrastructure.repositories import SqlAlchemyWorkspaceMembershipRepository
from src.modules.projects.infrastructure.repositories import (
    SqlAlchemyProjectRepository,
    SqlAlchemyWorkItemRepository,
)
from src.platform.db import get_db
from src.shared_kernel.errors import ForbiddenError, NotFoundError


def require_project_role(*allowed_roles: WorkspaceRole):
    """Dependency factory: resolves the project's workspace and 403s unless the
    current user holds one of `allowed_roles` there.

    Cross-module by necessity: workspace membership is owned by the identity
    module. This imports identity's repository directly at the API layer
    (composition edge, not domain/application coupling) — see ARCHITECTURE.md
    §3 for the accepted-coupling note. If a third module needs the same
    check, extract a shared AuthorizationService port instead of a third copy.
    """

    async def _check(
        project_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        project = await SqlAlchemyProjectRepository(db).get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project not found")

        membership_repo = SqlAlchemyWorkspaceMembershipRepository(db)
        membership = await membership_repo.get(project.workspace_id, current_user.id)
        if membership is None or membership.role not in allowed_roles:
            raise ForbiddenError("You do not have access to this project")
        return current_user

    return _check


def require_work_item_role(*allowed_roles: WorkspaceRole):
    """Same as `require_project_role`, but resolves the project from a `work_item_id` path param."""

    async def _check(
        work_item_id: UUID,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        work_item = await SqlAlchemyWorkItemRepository(db).get_by_id(work_item_id)
        if work_item is None:
            raise NotFoundError("Work item not found")
        project = await SqlAlchemyProjectRepository(db).get_by_id(work_item.project_id)
        if project is None:
            raise NotFoundError("Project not found")

        membership_repo = SqlAlchemyWorkspaceMembershipRepository(db)
        membership = await membership_repo.get(project.workspace_id, current_user.id)
        if membership is None or membership.role not in allowed_roles:
            raise ForbiddenError("You do not have access to this work item")
        return current_user

    return _check
