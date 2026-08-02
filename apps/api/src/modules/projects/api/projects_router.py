from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.dependencies import require_workspace_role
from src.modules.identity.domain.entities import User, WorkspaceRole
from src.modules.projects.api.dependencies import require_project_role
from src.modules.projects.api.schemas import CreateProjectRequest, ProjectOut, UpdateProjectRequest
from src.modules.projects.application.use_cases import (
    ArchiveProjectUseCase,
    CreateProjectUseCase,
    UpdateProjectUseCase,
)
from src.modules.projects.infrastructure.repositories import SqlAlchemyProjectRepository
from src.platform.db import get_db
from src.shared_kernel.errors import NotFoundError
from src.shared_kernel.schemas import ItemResponse, ListResponse, PageMeta

router = APIRouter(tags=["projects"])


@router.get("/api/v1/workspaces/{workspace_id}/projects", response_model=ListResponse[ProjectOut])
async def list_projects(
    workspace_id: UUID,
    current_user: User = Depends(require_workspace_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[ProjectOut]:
    projects = await SqlAlchemyProjectRepository(db).list_for_workspace(workspace_id)
    data = [ProjectOut(**p.__dict__) for p in projects]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/workspaces/{workspace_id}/projects",
    response_model=ItemResponse[ProjectOut],
    status_code=201,
)
async def create_project(
    workspace_id: UUID,
    body: CreateProjectRequest,
    current_user: User = Depends(require_workspace_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[ProjectOut]:
    use_case = CreateProjectUseCase(SqlAlchemyProjectRepository(db))
    project = await use_case.execute(
        workspace_id=workspace_id,
        key=body.key.upper(),
        name=body.name,
        description=body.description,
    )
    await db.commit()
    return ItemResponse(data=ProjectOut(**project.__dict__))


@router.get("/api/v1/projects/{project_id}", response_model=ItemResponse[ProjectOut])
async def get_project(
    project_id: UUID,
    current_user: User = Depends(require_project_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[ProjectOut]:
    project = await SqlAlchemyProjectRepository(db).get_by_id(project_id)
    if project is None:
        raise NotFoundError("Project not found")
    return ItemResponse(data=ProjectOut(**project.__dict__))


@router.patch("/api/v1/projects/{project_id}", response_model=ItemResponse[ProjectOut])
async def update_project(
    project_id: UUID,
    body: UpdateProjectRequest,
    current_user: User = Depends(
        require_project_role(WorkspaceRole.ADMIN, WorkspaceRole.PRODUCT_OWNER)
    ),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[ProjectOut]:
    fields = body.model_dump(exclude_unset=True)
    if "status" in fields and fields["status"] is not None:
        fields["status"] = fields["status"].value
    use_case = UpdateProjectUseCase(SqlAlchemyProjectRepository(db))
    project = await use_case.execute(project_id, fields)
    await db.commit()
    return ItemResponse(data=ProjectOut(**project.__dict__))


@router.delete("/api/v1/projects/{project_id}", response_model=ItemResponse[ProjectOut])
async def archive_project(
    project_id: UUID,
    current_user: User = Depends(
        require_project_role(WorkspaceRole.ADMIN, WorkspaceRole.PRODUCT_OWNER)
    ),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[ProjectOut]:
    use_case = ArchiveProjectUseCase(SqlAlchemyProjectRepository(db))
    project = await use_case.execute(project_id)
    await db.commit()
    return ItemResponse(data=ProjectOut(**project.__dict__))
