from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class WorkspaceRole(StrEnum):
    ADMIN = "admin"
    PRODUCT_OWNER = "product_owner"
    SCRUM_MASTER = "scrum_master"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class OAuthProviderName(StrEnum):
    GOOGLE = "google"
    MICROSOFT = "microsoft"


@dataclass
class User:
    id: UUID
    email: str
    full_name: str
    password_hash: str | None
    avatar_url: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Organization:
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime


@dataclass
class Workspace:
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    created_at: datetime


@dataclass
class WorkspaceMembership:
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime
