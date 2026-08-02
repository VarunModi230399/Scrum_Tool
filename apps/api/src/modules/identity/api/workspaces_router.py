from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.dependencies import get_current_user, require_workspace_role
from src.modules.identity.api.schemas import (
    AddMemberRequest,
    CreateWorkspaceRequest,
    UpdateMemberRoleRequest,
    UpdateWorkspaceRequest,
    WorkspaceMembershipOut,
    WorkspaceOut,
)
from src.modules.identity.application.use_cases import (
    AddWorkspaceMemberUseCase,
    CreateWorkspaceUseCase,
    RemoveWorkspaceMemberUseCase,
    UpdateWorkspaceMemberRoleUseCase,
    UpdateWorkspaceUseCase,
)
from src.modules.identity.domain.entities import User, WorkspaceRole
from src.modules.identity.infrastructure.repositories import (
    SqlAlchemyUserRepository,
    SqlAlchemyWorkspaceMembershipRepository,
    SqlAlchemyWorkspaceRepository,
)
from src.platform.db import get_db
from src.shared_kernel.errors import ForbiddenError, NotFoundError
from src.shared_kernel.schemas import ItemResponse, ListResponse, PageMeta

router = APIRouter(tags=["workspaces"])


@router.get(
    "/api/v1/organizations/{organization_id}/workspaces", response_model=ListResponse[WorkspaceOut]
)
async def list_workspaces(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkspaceOut]:
    workspace_repo = SqlAlchemyWorkspaceRepository(db)
    membership_repo = SqlAlchemyWorkspaceMembershipRepository(db)
    all_workspaces = await workspace_repo.list_for_organization(organization_id)

    visible = [
        w for w in all_workspaces if await membership_repo.get(w.id, current_user.id) is not None
    ]
    data = [WorkspaceOut(**w.__dict__) for w in visible]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/organizations/{organization_id}/workspaces",
    response_model=ItemResponse[WorkspaceOut],
    status_code=201,
)
async def create_workspace(
    organization_id: UUID,
    body: CreateWorkspaceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkspaceOut]:
    use_case = CreateWorkspaceUseCase(
        SqlAlchemyWorkspaceRepository(db), SqlAlchemyWorkspaceMembershipRepository(db)
    )
    workspace = await use_case.execute(
        organization_id=organization_id, name=body.name, creator_user_id=current_user.id
    )
    await db.commit()
    return ItemResponse(data=WorkspaceOut(**workspace.__dict__))


@router.get("/api/v1/workspaces/{workspace_id}", response_model=ItemResponse[WorkspaceOut])
async def get_workspace(
    workspace_id: UUID,
    current_user: User = Depends(require_workspace_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkspaceOut]:
    workspace = await SqlAlchemyWorkspaceRepository(db).get_by_id(workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")
    return ItemResponse(data=WorkspaceOut(**workspace.__dict__))


@router.patch("/api/v1/workspaces/{workspace_id}", response_model=ItemResponse[WorkspaceOut])
async def update_workspace(
    workspace_id: UUID,
    body: UpdateWorkspaceRequest,
    current_user: User = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkspaceOut]:
    use_case = UpdateWorkspaceUseCase(SqlAlchemyWorkspaceRepository(db))
    workspace = await use_case.execute(workspace_id=workspace_id, name=body.name)
    await db.commit()
    return ItemResponse(data=WorkspaceOut(**workspace.__dict__))


@router.get(
    "/api/v1/workspaces/{workspace_id}/members",
    response_model=ListResponse[WorkspaceMembershipOut],
)
async def list_members(
    workspace_id: UUID,
    current_user: User = Depends(require_workspace_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkspaceMembershipOut]:
    memberships = await SqlAlchemyWorkspaceMembershipRepository(db).list_for_workspace(workspace_id)
    data = [WorkspaceMembershipOut(**m.__dict__) for m in memberships]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/workspaces/{workspace_id}/members",
    response_model=ItemResponse[WorkspaceMembershipOut],
    status_code=201,
)
async def add_member(
    workspace_id: UUID,
    body: AddMemberRequest,
    current_user: User = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkspaceMembershipOut]:
    use_case = AddWorkspaceMemberUseCase(
        SqlAlchemyWorkspaceMembershipRepository(db), SqlAlchemyUserRepository(db)
    )
    membership = await use_case.execute(
        workspace_id=workspace_id, user_id=body.user_id, role=body.role
    )
    await db.commit()
    return ItemResponse(data=WorkspaceMembershipOut(**membership.__dict__))


@router.patch(
    "/api/v1/workspaces/{workspace_id}/members/{user_id}",
    response_model=ItemResponse[WorkspaceMembershipOut],
)
async def update_member_role(
    workspace_id: UUID,
    user_id: UUID,
    body: UpdateMemberRoleRequest,
    current_user: User = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkspaceMembershipOut]:
    use_case = UpdateWorkspaceMemberRoleUseCase(SqlAlchemyWorkspaceMembershipRepository(db))
    membership = await use_case.execute(workspace_id=workspace_id, user_id=user_id, role=body.role)
    await db.commit()
    return ItemResponse(data=WorkspaceMembershipOut(**membership.__dict__))


@router.delete("/api/v1/workspaces/{workspace_id}/members/{user_id}", status_code=204)
async def remove_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: User = Depends(require_workspace_role(WorkspaceRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    if current_user.id == user_id:
        raise ForbiddenError("Admins cannot remove themselves from a workspace")
    use_case = RemoveWorkspaceMemberUseCase(SqlAlchemyWorkspaceMembershipRepository(db))
    await use_case.execute(workspace_id=workspace_id, user_id=user_id)
    await db.commit()
