from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

# Shared response shapes for comments/attachments, owned by the collaboration
# module and imported by whichever module mounts the routes (projects,
# requirements, ...) — see ARCHITECTURE.md for why collaboration has no
# routes of its own.


class AddCommentRequest(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    updated_at: datetime


class AttachmentOut(BaseModel):
    id: UUID
    entity_type: str
    entity_id: UUID
    uploaded_by: UUID
    file_name: str
    file_url: str
    file_size_bytes: int
    mime_type: str
    created_at: datetime
