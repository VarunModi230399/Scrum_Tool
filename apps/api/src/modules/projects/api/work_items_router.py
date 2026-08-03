from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.collaboration.api.schemas import AddCommentRequest, AttachmentOut, CommentOut
from src.modules.collaboration.application.use_cases import AddAttachmentUseCase, AddCommentUseCase
from src.modules.collaboration.domain.entities import EntityType
from src.modules.collaboration.infrastructure.repositories import (
    SqlAlchemyAttachmentRepository,
    SqlAlchemyCommentRepository,
)
from src.modules.collaboration.infrastructure.storage import save_upload
from src.modules.identity.domain.entities import User, WorkspaceRole
from src.modules.projects.api.dependencies import require_project_role, require_work_item_role
from src.modules.projects.api.schemas import (
    AddDependencyRequest,
    CreateWorkItemRequest,
    MoveWorkItemRequest,
    SetProgressOverrideRequest,
    UpdateWorkItemRequest,
    WorkItemDependencyOut,
    WorkItemOut,
)
from src.modules.projects.application.progress import ProgressRollupService
from src.modules.projects.application.use_cases import (
    AddDependencyUseCase,
    CreateWorkItemUseCase,
    DeleteWorkItemUseCase,
    MoveWorkItemUseCase,
    RemoveDependencyUseCase,
    SetProgressOverrideUseCase,
    UpdateWorkItemUseCase,
)
from src.modules.projects.domain.entities import WorkItemStatus, WorkItemType
from src.modules.projects.infrastructure.repositories import (
    SqlAlchemyProjectRepository,
    SqlAlchemyWorkItemDependencyRepository,
    SqlAlchemyWorkItemRepository,
)
from src.platform.db import get_db
from src.shared_kernel.errors import NotFoundError
from src.shared_kernel.schemas import ItemResponse, ListResponse, PageMeta

router = APIRouter(tags=["work-items"])


@router.get("/api/v1/projects/{project_id}/work-items", response_model=ListResponse[WorkItemOut])
async def list_work_items(
    project_id: UUID,
    type: WorkItemType | None = Query(default=None),
    status: WorkItemStatus | None = Query(default=None),
    owner_id: UUID | None = Query(default=None),
    parent_id: UUID | None = Query(default=None),
    current_user: User = Depends(require_project_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkItemOut]:
    work_items = await SqlAlchemyWorkItemRepository(db).list_for_project(
        project_id, type=type, status=status, owner_id=owner_id, parent_id=parent_id
    )
    data = [WorkItemOut(**w.__dict__) for w in work_items]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/projects/{project_id}/work-items",
    response_model=ItemResponse[WorkItemOut],
    status_code=201,
)
async def create_work_item(
    project_id: UUID,
    body: CreateWorkItemRequest,
    current_user: User = Depends(require_project_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemOut]:
    work_item_repo = SqlAlchemyWorkItemRepository(db)
    use_case = CreateWorkItemUseCase(
        work_item_repo, ProgressRollupService(work_item_repo, SqlAlchemyProjectRepository(db))
    )
    work_item = await use_case.execute(
        project_id=project_id,
        parent_id=body.parent_id,
        type=body.type,
        title=body.title,
        description=body.description,
        acceptance_criteria=body.acceptance_criteria,
        priority=body.priority,
        risk=body.risk,
        story_points=body.story_points,
        estimated_hours=body.estimated_hours,
        start_date=body.start_date,
        due_date=body.due_date,
        owner_id=body.owner_id,
        reviewer_id=body.reviewer_id,
        created_by=current_user.id,
    )
    await db.commit()
    return ItemResponse(data=WorkItemOut(**work_item.__dict__))


@router.get("/api/v1/work-items/{work_item_id}", response_model=ItemResponse[WorkItemOut])
async def get_work_item(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemOut]:
    work_item = await SqlAlchemyWorkItemRepository(db).get_by_id(work_item_id)
    if work_item is None:
        raise NotFoundError("Work item not found")
    return ItemResponse(data=WorkItemOut(**work_item.__dict__))


@router.patch("/api/v1/work-items/{work_item_id}", response_model=ItemResponse[WorkItemOut])
async def update_work_item(
    work_item_id: UUID,
    body: UpdateWorkItemRequest,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemOut]:
    fields = body.model_dump(exclude_unset=True)
    for key in ("status", "priority", "risk"):
        if key in fields and fields[key] is not None:
            fields[key] = fields[key].value

    work_item_repo = SqlAlchemyWorkItemRepository(db)
    use_case = UpdateWorkItemUseCase(
        work_item_repo, ProgressRollupService(work_item_repo, SqlAlchemyProjectRepository(db))
    )
    work_item = await use_case.execute(work_item_id, fields)
    await db.commit()
    return ItemResponse(data=WorkItemOut(**work_item.__dict__))


@router.delete("/api/v1/work-items/{work_item_id}", status_code=204)
async def delete_work_item(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> None:
    work_item_repo = SqlAlchemyWorkItemRepository(db)
    use_case = DeleteWorkItemUseCase(
        work_item_repo, ProgressRollupService(work_item_repo, SqlAlchemyProjectRepository(db))
    )
    await use_case.execute(work_item_id)
    await db.commit()


@router.get("/api/v1/work-items/{work_item_id}/children", response_model=ListResponse[WorkItemOut])
async def list_children(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkItemOut]:
    children = await SqlAlchemyWorkItemRepository(db).list_children(work_item_id)
    data = [WorkItemOut(**w.__dict__) for w in children]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.get("/api/v1/work-items/{work_item_id}/ancestors", response_model=ListResponse[WorkItemOut])
async def list_ancestors(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkItemOut]:
    repo = SqlAlchemyWorkItemRepository(db)
    work_item = await repo.get_by_id(work_item_id)
    if work_item is None:
        raise NotFoundError("Work item not found")
    ancestors = await repo.list_ancestors(work_item)
    data = [WorkItemOut(**w.__dict__) for w in ancestors]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.patch("/api/v1/work-items/{work_item_id}/move", response_model=ItemResponse[WorkItemOut])
async def move_work_item(
    work_item_id: UUID,
    body: MoveWorkItemRequest,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemOut]:
    work_item_repo = SqlAlchemyWorkItemRepository(db)
    use_case = MoveWorkItemUseCase(
        work_item_repo, ProgressRollupService(work_item_repo, SqlAlchemyProjectRepository(db))
    )
    work_item = await use_case.execute(work_item_id, body.new_parent_id)
    await db.commit()
    return ItemResponse(data=WorkItemOut(**work_item.__dict__))


@router.patch(
    "/api/v1/work-items/{work_item_id}/progress-override",
    response_model=ItemResponse[WorkItemOut],
)
async def set_progress_override(
    work_item_id: UUID,
    body: SetProgressOverrideRequest,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemOut]:
    work_item_repo = SqlAlchemyWorkItemRepository(db)
    use_case = SetProgressOverrideUseCase(
        work_item_repo, ProgressRollupService(work_item_repo, SqlAlchemyProjectRepository(db))
    )
    work_item = await use_case.execute(work_item_id, body.value)
    await db.commit()
    return ItemResponse(data=WorkItemOut(**work_item.__dict__))


@router.get(
    "/api/v1/work-items/{work_item_id}/dependencies",
    response_model=ListResponse[WorkItemDependencyOut],
)
async def list_dependencies(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[WorkItemDependencyOut]:
    dependencies = await SqlAlchemyWorkItemDependencyRepository(db).list_for_work_item(work_item_id)
    data = [WorkItemDependencyOut(**d.__dict__) for d in dependencies]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/work-items/{work_item_id}/dependencies",
    response_model=ItemResponse[WorkItemDependencyOut],
    status_code=201,
)
async def add_dependency(
    work_item_id: UUID,
    body: AddDependencyRequest,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[WorkItemDependencyOut]:
    use_case = AddDependencyUseCase(
        SqlAlchemyWorkItemDependencyRepository(db), SqlAlchemyWorkItemRepository(db)
    )
    dependency = await use_case.execute(
        work_item_id=work_item_id, depends_on_id=body.depends_on_id, type=body.type
    )
    await db.commit()
    return ItemResponse(data=WorkItemDependencyOut(**dependency.__dict__))


@router.delete("/api/v1/work-items/{work_item_id}/dependencies/{dependency_id}", status_code=204)
async def remove_dependency(
    work_item_id: UUID,
    dependency_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> None:
    use_case = RemoveDependencyUseCase(SqlAlchemyWorkItemDependencyRepository(db))
    await use_case.execute(dependency_id)
    await db.commit()


@router.get("/api/v1/work-items/{work_item_id}/comments", response_model=ListResponse[CommentOut])
async def list_work_item_comments(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[CommentOut]:
    comments = await SqlAlchemyCommentRepository(db).list_for_entity(
        EntityType.WORK_ITEM, work_item_id
    )
    data = [CommentOut(**c.__dict__) for c in comments]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/work-items/{work_item_id}/comments",
    response_model=ItemResponse[CommentOut],
    status_code=201,
)
async def add_work_item_comment(
    work_item_id: UUID,
    body: AddCommentRequest,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[CommentOut]:
    use_case = AddCommentUseCase(SqlAlchemyCommentRepository(db))
    comment = await use_case.execute(
        entity_type=EntityType.WORK_ITEM,
        entity_id=work_item_id,
        author_id=current_user.id,
        body=body.body,
    )
    await db.commit()
    return ItemResponse(data=CommentOut(**comment.__dict__))


@router.get(
    "/api/v1/work-items/{work_item_id}/attachments", response_model=ListResponse[AttachmentOut]
)
async def list_work_item_attachments(
    work_item_id: UUID,
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ListResponse[AttachmentOut]:
    attachments = await SqlAlchemyAttachmentRepository(db).list_for_entity(
        EntityType.WORK_ITEM, work_item_id
    )
    data = [AttachmentOut(**a.__dict__) for a in attachments]
    return ListResponse(data=data, meta=PageMeta(page=1, page_size=len(data), total=len(data)))


@router.post(
    "/api/v1/work-items/{work_item_id}/attachments",
    response_model=ItemResponse[AttachmentOut],
    status_code=201,
)
async def add_work_item_attachment(
    work_item_id: UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_work_item_role(*WorkspaceRole)),
    db: AsyncSession = Depends(get_db),
) -> ItemResponse[AttachmentOut]:
    file_url, file_name, file_size_bytes = await save_upload(file)
    use_case = AddAttachmentUseCase(SqlAlchemyAttachmentRepository(db))
    attachment = await use_case.execute(
        entity_type=EntityType.WORK_ITEM,
        entity_id=work_item_id,
        uploaded_by=current_user.id,
        file_name=file_name,
        file_url=file_url,
        file_size_bytes=file_size_bytes,
        mime_type=file.content_type or "application/octet-stream",
    )
    await db.commit()
    return ItemResponse(data=AttachmentOut(**attachment.__dict__))
