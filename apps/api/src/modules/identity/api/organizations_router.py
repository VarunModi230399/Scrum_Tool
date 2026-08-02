from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.dependencies import get_current_user
from src.modules.identity.api.schemas import CreateOrganizationRequest, OrganizationOut
from src.modules.identity.application.use_cases import CreateOrganizationUseCase
from src.modules.identity.domain.entities import User
from src.modules.identity.infrastructure.repositories import (
    SqlAlchemyOrganizationRepository,
    SqlAlchemyWorkspaceMembershipRepository,
    SqlAlchemyWorkspaceRepository,
)
from src.platform.db import get_db
from src.shared_kernel.errors import ForbiddenError, NotFoundError
from src.shared_kernel.schemas import ItemResponse

router = APIRouter(prefix="/api/v1/organizations", tags=["organizations"])


@router.post("", response_model=ItemResponse[OrganizationOut], status_code=201)
async def create_organization(
    body: CreateOrganizationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[OrganizationOut]:
    use_case = CreateOrganizationUseCase(SqlAlchemyOrganizationRepository(db))
    organization = await use_case.execute(name=body.name)
    await db.commit()
    return ItemResponse(data=OrganizationOut(**organization.__dict__))


@router.get("/{organization_id}", response_model=ItemResponse[OrganizationOut])
async def get_organization(
    organization_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[OrganizationOut]:
    organization = await SqlAlchemyOrganizationRepository(db).get_by_id(organization_id)
    if organization is None:
        raise NotFoundError("Organization not found")

    workspace_repo = SqlAlchemyWorkspaceRepository(db)
    membership_repo = SqlAlchemyWorkspaceMembershipRepository(db)
    workspaces = await workspace_repo.list_for_organization(organization_id)
    is_member = False
    for workspace in workspaces:
        if await membership_repo.get(workspace.id, current_user.id) is not None:
            is_member = True
            break
    if not is_member:
        raise ForbiddenError("You do not have access to this organization")

    return ItemResponse(data=OrganizationOut(**organization.__dict__))
