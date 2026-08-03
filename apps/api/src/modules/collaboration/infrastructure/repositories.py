import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.collaboration.domain.entities import Attachment, Comment, EntityType
from src.modules.collaboration.infrastructure.models import AttachmentModel, CommentModel


def _comment_to_entity(model: CommentModel) -> Comment:
    return Comment(
        id=model.id,
        entity_type=EntityType(model.entity_type),
        entity_id=model.entity_id,
        author_id=model.author_id,
        body=model.body,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _attachment_to_entity(model: AttachmentModel) -> Attachment:
    return Attachment(
        id=model.id,
        entity_type=EntityType(model.entity_type),
        entity_id=model.entity_id,
        uploaded_by=model.uploaded_by,
        file_name=model.file_name,
        file_url=model.file_url,
        file_size_bytes=model.file_size_bytes,
        mime_type=model.mime_type,
        created_at=model.created_at,
    )


class SqlAlchemyCommentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_entity(self, entity_type: EntityType, entity_id: uuid.UUID) -> list[Comment]:
        result = await self._session.execute(
            select(CommentModel)
            .where(
                CommentModel.entity_type == entity_type.value, CommentModel.entity_id == entity_id
            )
            .order_by(CommentModel.created_at)
        )
        return [_comment_to_entity(m) for m in result.scalars().all()]

    async def create(
        self, *, entity_type: EntityType, entity_id: uuid.UUID, author_id: uuid.UUID, body: str
    ) -> Comment:
        model = CommentModel(
            entity_type=entity_type.value, entity_id=entity_id, author_id=author_id, body=body
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _comment_to_entity(model)


class SqlAlchemyAttachmentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_for_entity(
        self, entity_type: EntityType, entity_id: uuid.UUID
    ) -> list[Attachment]:
        result = await self._session.execute(
            select(AttachmentModel)
            .where(
                AttachmentModel.entity_type == entity_type.value,
                AttachmentModel.entity_id == entity_id,
            )
            .order_by(AttachmentModel.created_at)
        )
        return [_attachment_to_entity(m) for m in result.scalars().all()]

    async def create(
        self,
        *,
        entity_type: EntityType,
        entity_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        file_name: str,
        file_url: str,
        file_size_bytes: int,
        mime_type: str,
    ) -> Attachment:
        model = AttachmentModel(
            entity_type=entity_type.value,
            entity_id=entity_id,
            uploaded_by=uploaded_by,
            file_name=file_name,
            file_url=file_url,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _attachment_to_entity(model)
