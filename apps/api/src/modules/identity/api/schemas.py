from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from src.modules.identity.domain.entities import WorkspaceRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: UUID
    email: str
    full_name: str
    avatar_url: str | None
    timezone: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenPairOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OrganizationOut(BaseModel):
    id: UUID
    name: str
    slug: str
    created_at: datetime


class CreateOrganizationRequest(BaseModel):
    name: str = Field(min_length=1)


class WorkspaceOut(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    slug: str
    created_at: datetime


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1)


class UpdateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1)


class WorkspaceMembershipOut(BaseModel):
    id: UUID
    workspace_id: UUID
    user_id: UUID
    role: WorkspaceRole
    created_at: datetime


class AddMemberRequest(BaseModel):
    user_id: UUID
    role: WorkspaceRole


class UpdateMemberRoleRequest(BaseModel):
    role: WorkspaceRole
