from typing import Protocol
from uuid import UUID

from src.modules.collaboration.domain.entities import Attachment, Comment, EntityType


class CommentRepository(Protocol):
    async def list_for_entity(self, entity_type: EntityType, entity_id: UUID) -> list[Comment]: ...
    async def create(
        self, *, entity_type: EntityType, entity_id: UUID, author_id: UUID, body: str
    ) -> Comment: ...


class AttachmentRepository(Protocol):
    async def list_for_entity(
        self, entity_type: EntityType, entity_id: UUID
    ) -> list[Attachment]: ...
    async def create(
        self,
        *,
        entity_type: EntityType,
        entity_id: UUID,
        uploaded_by: UUID,
        file_name: str,
        file_url: str,
        file_size_bytes: int,
        mime_type: str,
    ) -> Attachment: ...
