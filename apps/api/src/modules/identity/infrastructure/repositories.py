from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.domain.entities import (
    Organization,
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from src.modules.identity.infrastructure.models import (
    OAuthIdentityModel,
    OrganizationModel,
    RefreshTokenModel,
    UserModel,
    WorkspaceMembershipModel,
    WorkspaceModel,
)


def _user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        full_name=model.full_name,
        password_hash=model.password_hash,
        avatar_url=model.avatar_url,
        timezone=model.timezone,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _organization_to_entity(model: OrganizationModel) -> Organization:
    return Organization(
        id=model.id,
        name=model.name,
        slug=model.slug,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _workspace_to_entity(model: WorkspaceModel) -> Workspace:
    return Workspace(
        id=model.id,
        organization_id=model.organization_id,
        name=model.name,
        slug=model.slug,
        created_at=model.created_at,
    )


def _membership_to_entity(model: WorkspaceMembershipModel) -> WorkspaceMembership:
    return WorkspaceMembership(
        id=model.id,
        workspace_id=model.workspace_id,
        user_id=model.user_id,
        role=WorkspaceRole(model.role),
        created_at=model.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        model = await self._session.get(UserModel, user_id)
        return _user_to_entity(model) if model else None

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(select(UserModel).where(UserModel.email == email))
        model = result.scalar_one_or_none()
        return _user_to_entity(model) if model else None

    async def create(self, *, email: str, full_name: str, password_hash: str | None) -> User:
        model = UserModel(email=email, full_name=full_name, password_hash=password_hash)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _user_to_entity(model)


class SqlAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, organization_id: UUID) -> Organization | None:
        model = await self._session.get(OrganizationModel, organization_id)
        return _organization_to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _organization_to_entity(model) if model else None

    async def create(self, *, name: str, slug: str) -> Organization:
        model = OrganizationModel(name=name, slug=slug)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _organization_to_entity(model)


class SqlAlchemyWorkspaceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, workspace_id: UUID) -> Workspace | None:
        model = await self._session.get(WorkspaceModel, workspace_id)
        return _workspace_to_entity(model) if model else None

    async def list_for_organization(self, organization_id: UUID) -> list[Workspace]:
        result = await self._session.execute(
            select(WorkspaceModel).where(WorkspaceModel.organization_id == organization_id)
        )
        return [_workspace_to_entity(m) for m in result.scalars().all()]

    async def create(self, *, organization_id: UUID, name: str, slug: str) -> Workspace:
        model = WorkspaceModel(organization_id=organization_id, name=name, slug=slug)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _workspace_to_entity(model)

    async def update_name(self, workspace_id: UUID, name: str) -> Workspace:
        model = await self._session.get(WorkspaceModel, workspace_id)
        if model is None:
            raise ValueError(f"Workspace {workspace_id} not found")
        model.name = name
        await self._session.flush()
        await self._session.refresh(model)
        return _workspace_to_entity(model)


class SqlAlchemyWorkspaceMembershipRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, workspace_id: UUID, user_id: UUID) -> WorkspaceMembership | None:
        result = await self._session.execute(
            select(WorkspaceMembershipModel).where(
                WorkspaceMembershipModel.workspace_id == workspace_id,
                WorkspaceMembershipModel.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return _membership_to_entity(model) if model else None

    async def list_for_workspace(self, workspace_id: UUID) -> list[WorkspaceMembership]:
        result = await self._session.execute(
            select(WorkspaceMembershipModel).where(
                WorkspaceMembershipModel.workspace_id == workspace_id
            )
        )
        return [_membership_to_entity(m) for m in result.scalars().all()]

    async def list_for_user(self, user_id: UUID) -> list[WorkspaceMembership]:
        result = await self._session.execute(
            select(WorkspaceMembershipModel).where(WorkspaceMembershipModel.user_id == user_id)
        )
        return [_membership_to_entity(m) for m in result.scalars().all()]

    async def create(
        self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMembership:
        model = WorkspaceMembershipModel(
            workspace_id=workspace_id, user_id=user_id, role=role.value
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _membership_to_entity(model)

    async def update_role(
        self, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMembership:
        result = await self._session.execute(
            select(WorkspaceMembershipModel).where(
                WorkspaceMembershipModel.workspace_id == workspace_id,
                WorkspaceMembershipModel.user_id == user_id,
            )
        )
        model = result.scalar_one()
        model.role = role.value
        await self._session.flush()
        await self._session.refresh(model)
        return _membership_to_entity(model)

    async def delete(self, workspace_id: UUID, user_id: UUID) -> None:
        result = await self._session.execute(
            select(WorkspaceMembershipModel).where(
                WorkspaceMembershipModel.workspace_id == workspace_id,
                WorkspaceMembershipModel.user_id == user_id,
            )
        )
        model = result.scalar_one()
        await self._session.delete(model)
        await self._session.flush()


class SqlAlchemyOAuthIdentityRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_user_id_by_provider(self, provider: str, provider_uid: str) -> UUID | None:
        result = await self._session.execute(
            select(OAuthIdentityModel).where(
                OAuthIdentityModel.provider == provider,
                OAuthIdentityModel.provider_uid == provider_uid,
            )
        )
        model = result.scalar_one_or_none()
        return model.user_id if model else None

    async def link(self, *, user_id: UUID, provider: str, provider_uid: str) -> None:
        self._session.add(
            OAuthIdentityModel(user_id=user_id, provider=provider, provider_uid=provider_uid)
        )
        await self._session.flush()


class SqlAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def store(self, *, user_id: UUID, token_hash: str, expires_at: datetime) -> None:
        self._session.add(
            RefreshTokenModel(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        )
        await self._session.flush()

    async def get_active_user_id(self, token_hash: str) -> UUID | None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.revoked_at.is_(None),
            )
        )
        model = result.scalar_one_or_none()
        if model is None or model.expires_at < datetime.now(UTC):
            return None
        return model.user_id

    async def revoke(self, token_hash: str) -> None:
        result = await self._session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == token_hash)
        )
        model = result.scalar_one_or_none()
        if model is not None:
            model.revoked_at = datetime.now(UTC)
            await self._session.flush()
