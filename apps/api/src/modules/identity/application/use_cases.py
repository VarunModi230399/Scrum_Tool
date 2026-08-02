from dataclasses import dataclass
from uuid import UUID

from src.modules.identity.application.ports import (
    OAuthIdentityRepository,
    OrganizationRepository,
    RefreshTokenRepository,
    UserRepository,
    WorkspaceMembershipRepository,
    WorkspaceRepository,
)
from src.modules.identity.domain.entities import (
    Organization,
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from src.modules.identity.infrastructure.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from src.shared_kernel.errors import ConflictError, NotFoundError, UnauthenticatedError
from src.shared_kernel.slugify import slugify


@dataclass
class TokenPair:
    access_token: str
    refresh_token: str


async def _unique_org_slug(org_repo: OrganizationRepository, base: str) -> str:
    slug = slugify(base)
    candidate = slug
    suffix = 1
    while await org_repo.get_by_slug(candidate) is not None:
        suffix += 1
        candidate = f"{slug}-{suffix}"
    return candidate


async def _unique_workspace_slug(
    workspace_repo: WorkspaceRepository, organization_id: UUID, base: str
) -> str:
    existing = {w.slug for w in await workspace_repo.list_for_organization(organization_id)}
    slug = slugify(base)
    candidate = slug
    suffix = 1
    while candidate in existing:
        suffix += 1
        candidate = f"{slug}-{suffix}"
    return candidate


async def _issue_token_pair(refresh_repo: RefreshTokenRepository, user_id: UUID) -> TokenPair:
    access_token = create_access_token(user_id)
    refresh_token, expires_at = create_refresh_token(user_id)
    await refresh_repo.store(
        user_id=user_id, token_hash=hash_token(refresh_token), expires_at=expires_at
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


class RegisterUserUseCase:
    """Creates the user plus a personal organization/workspace so they can start working now."""

    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        workspace_repo: WorkspaceRepository,
        membership_repo: WorkspaceMembershipRepository,
    ):
        self._users = user_repo
        self._orgs = org_repo
        self._workspaces = workspace_repo
        self._memberships = membership_repo

    async def execute(self, *, email: str, password: str, full_name: str) -> User:
        if await self._users.get_by_email(email) is not None:
            raise ConflictError("An account with this email already exists")

        user = await self._users.create(
            email=email, full_name=full_name, password_hash=hash_password(password)
        )
        await _create_personal_org_and_workspace(
            self._orgs, self._workspaces, self._memberships, user
        )
        return user


async def _create_personal_org_and_workspace(
    org_repo: OrganizationRepository,
    workspace_repo: WorkspaceRepository,
    membership_repo: WorkspaceMembershipRepository,
    user: User,
) -> tuple[Organization, Workspace]:
    org_slug = await _unique_org_slug(org_repo, f"{user.full_name}-org")
    organization = await org_repo.create(name=f"{user.full_name}'s Organization", slug=org_slug)

    workspace_slug = await _unique_workspace_slug(workspace_repo, organization.id, "personal")
    workspace = await workspace_repo.create(
        organization_id=organization.id, name="Personal", slug=workspace_slug
    )

    await membership_repo.create(
        workspace_id=workspace.id, user_id=user.id, role=WorkspaceRole.ADMIN
    )
    return organization, workspace


class LoginUseCase:
    def __init__(self, user_repo: UserRepository, refresh_repo: RefreshTokenRepository):
        self._users = user_repo
        self._refresh_tokens = refresh_repo

    async def execute(self, *, email: str, password: str) -> tuple[User, TokenPair]:
        user = await self._users.get_by_email(email)
        if user is None or user.password_hash is None:
            raise UnauthenticatedError("Invalid email or password")
        if not verify_password(password, user.password_hash):
            raise UnauthenticatedError("Invalid email or password")

        tokens = await _issue_token_pair(self._refresh_tokens, user.id)
        return user, tokens


class OAuthLoginUseCase:
    """Finds or creates a user for a verified OAuth identity, then issues tokens."""

    def __init__(
        self,
        user_repo: UserRepository,
        org_repo: OrganizationRepository,
        workspace_repo: WorkspaceRepository,
        membership_repo: WorkspaceMembershipRepository,
        oauth_repo: OAuthIdentityRepository,
        refresh_repo: RefreshTokenRepository,
    ):
        self._users = user_repo
        self._orgs = org_repo
        self._workspaces = workspace_repo
        self._memberships = membership_repo
        self._oauth = oauth_repo
        self._refresh_tokens = refresh_repo

    async def execute(
        self, *, provider: str, provider_uid: str, email: str, full_name: str
    ) -> tuple[User, TokenPair]:
        existing_user_id = await self._oauth.get_user_id_by_provider(provider, provider_uid)
        if existing_user_id is not None:
            user = await self._users.get_by_id(existing_user_id)
            if user is None:
                raise NotFoundError("Linked user account no longer exists")
        else:
            user = await self._users.get_by_email(email)
            if user is None:
                user = await self._users.create(
                    email=email, full_name=full_name, password_hash=None
                )
                await _create_personal_org_and_workspace(
                    self._orgs, self._workspaces, self._memberships, user
                )
            await self._oauth.link(user_id=user.id, provider=provider, provider_uid=provider_uid)

        tokens = await _issue_token_pair(self._refresh_tokens, user.id)
        return user, tokens


class RefreshAccessTokenUseCase:
    """Rotates the refresh token: the presented one is revoked and a new pair is issued."""

    def __init__(self, refresh_repo: RefreshTokenRepository, user_repo: UserRepository):
        self._refresh_tokens = refresh_repo
        self._users = user_repo

    async def execute(self, refresh_token: str) -> TokenPair:
        try:
            token_user_id = decode_token(refresh_token, expected_type="refresh")
        except InvalidTokenError as exc:
            raise UnauthenticatedError("Invalid or expired refresh token") from exc

        token_hash = hash_token(refresh_token)
        active_user_id = await self._refresh_tokens.get_active_user_id(token_hash)
        if active_user_id is None or active_user_id != token_user_id:
            raise UnauthenticatedError("Invalid or expired refresh token")

        await self._refresh_tokens.revoke(token_hash)
        return await _issue_token_pair(self._refresh_tokens, active_user_id)


class LogoutUseCase:
    def __init__(self, refresh_repo: RefreshTokenRepository):
        self._refresh_tokens = refresh_repo

    async def execute(self, refresh_token: str) -> None:
        await self._refresh_tokens.revoke(hash_token(refresh_token))


class CreateOrganizationUseCase:
    def __init__(self, org_repo: OrganizationRepository):
        self._orgs = org_repo

    async def execute(self, *, name: str) -> Organization:
        slug = await _unique_org_slug(self._orgs, name)
        return await self._orgs.create(name=name, slug=slug)


class CreateWorkspaceUseCase:
    def __init__(
        self, workspace_repo: WorkspaceRepository, membership_repo: WorkspaceMembershipRepository
    ):
        self._workspaces = workspace_repo
        self._memberships = membership_repo

    async def execute(
        self, *, organization_id: UUID, name: str, creator_user_id: UUID
    ) -> Workspace:
        slug = await _unique_workspace_slug(self._workspaces, organization_id, name)
        workspace = await self._workspaces.create(
            organization_id=organization_id, name=name, slug=slug
        )
        await self._memberships.create(
            workspace_id=workspace.id, user_id=creator_user_id, role=WorkspaceRole.ADMIN
        )
        return workspace


class UpdateWorkspaceUseCase:
    def __init__(self, workspace_repo: WorkspaceRepository):
        self._workspaces = workspace_repo

    async def execute(self, *, workspace_id: UUID, name: str) -> Workspace:
        if await self._workspaces.get_by_id(workspace_id) is None:
            raise NotFoundError("Workspace not found")
        return await self._workspaces.update_name(workspace_id, name)


class AddWorkspaceMemberUseCase:
    def __init__(self, membership_repo: WorkspaceMembershipRepository, user_repo: UserRepository):
        self._memberships = membership_repo
        self._users = user_repo

    async def execute(
        self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMembership:
        if await self._users.get_by_id(user_id) is None:
            raise NotFoundError("User not found")
        if await self._memberships.get(workspace_id, user_id) is not None:
            raise ConflictError("User is already a member of this workspace")
        return await self._memberships.create(workspace_id=workspace_id, user_id=user_id, role=role)


class UpdateWorkspaceMemberRoleUseCase:
    def __init__(self, membership_repo: WorkspaceMembershipRepository):
        self._memberships = membership_repo

    async def execute(
        self, *, workspace_id: UUID, user_id: UUID, role: WorkspaceRole
    ) -> WorkspaceMembership:
        if await self._memberships.get(workspace_id, user_id) is None:
            raise NotFoundError("Membership not found")
        return await self._memberships.update_role(workspace_id, user_id, role)


class RemoveWorkspaceMemberUseCase:
    def __init__(self, membership_repo: WorkspaceMembershipRepository):
        self._memberships = membership_repo

    async def execute(self, *, workspace_id: UUID, user_id: UUID) -> None:
        if await self._memberships.get(workspace_id, user_id) is None:
            raise NotFoundError("Membership not found")
        await self._memberships.delete(workspace_id, user_id)
