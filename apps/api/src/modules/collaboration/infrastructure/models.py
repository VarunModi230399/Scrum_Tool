import uuid
from datetime import datetime

from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column

from src.platform.db import Base


class CommentModel(Base):
    __tablename__ = "comments"
    __table_args__ = (Index("idx_comments_entity", "entity_type", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class AttachmentModel(Base):
    __tablename__ = "attachments"
    __table_args__ = (Index("idx_attachments_entity", "entity_type", "entity_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(nullable=False)
    file_name: Mapped[str] = mapped_column(nullable=False)
    file_url: Mapped[str] = mapped_column(nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(nullable=False)
    mime_type: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
