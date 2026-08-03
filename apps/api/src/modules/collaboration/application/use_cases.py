from uuid import UUID

from src.modules.collaboration.application.ports import AttachmentRepository, CommentRepository
from src.modules.collaboration.domain.entities import Attachment, Comment, EntityType
from src.shared_kernel.errors import ValidationError


class AddCommentUseCase:
    def __init__(self, comment_repo: CommentRepository):
        self._comments = comment_repo

    async def execute(
        self, *, entity_type: EntityType, entity_id: UUID, author_id: UUID, body: str
    ) -> Comment:
        if not body.strip():
            raise ValidationError("Comment body cannot be empty")
        return await self._comments.create(
            entity_type=entity_type, entity_id=entity_id, author_id=author_id, body=body
        )


class AddAttachmentUseCase:
    def __init__(self, attachment_repo: AttachmentRepository):
        self._attachments = attachment_repo

    async def execute(
        self,
        *,
        entity_type: EntityType,
        entity_id: UUID,
        uploaded_by: UUID,
        file_name: str,
        file_url: str,
        file_size_bytes: int,
        mime_type: str,
    ) -> Attachment:
        return await self._attachments.create(
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=uploaded_by,
            file_name=file_name,
            file_url=file_url,
            file_size_bytes=file_size_bytes,
            mime_type=mime_type,
        )
