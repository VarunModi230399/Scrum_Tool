from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class EntityType(StrEnum):
    """Owning modules register the entity types they attach comments/files to."""

    WORK_ITEM = "work_item"
    REQUIREMENT = "requirement"


@dataclass
class Comment:
    id: UUID
    entity_type: EntityType
    entity_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Attachment:
    id: UUID
    entity_type: EntityType
    entity_id: UUID
    uploaded_by: UUID
    file_name: str
    file_url: str
    file_size_bytes: int
    mime_type: str
    created_at: datetime
