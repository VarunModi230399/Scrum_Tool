from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.domain.entities import User, WorkspaceRole
from src.modules.identity.infrastructure.repositories import (
    SqlAlchemyOAuthIdentityRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWorkspaceMembershipRepository,
    SqlAlchemyWorkspaceRepository,
)
from src.modules.identity.infrastructure.security import InvalidTokenError, decode_token
from src.platform.db import get_db
from src.shared_kernel.errors import ForbiddenError, UnauthenticatedError

_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_organization_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyOrganizationRepository:
    return SqlAlchemyOrganizationRepository(db)


def get_workspace_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyWorkspaceRepository:
    return SqlAlchemyWorkspaceRepository(db)


def get_membership_repo(
    db: AsyncSession = Depends(get_db),
) -> SqlAlchemyWorkspaceMembershipRepository:
    return SqlAlchemyWorkspaceMembershipRepository(db)


def get_oauth_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyOAuthIdentityRepository:
    return SqlAlchemyOAuthIdentityRepository(db)


def get_refresh_token_repo(db: AsyncSession = Depends(get_db)) -> SqlAlchemyRefreshTokenRepository:
    return SqlAlchemyRefreshTokenRepository(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repo),
) -> User:
    if credentials is None:
        raise UnauthenticatedError("Missing bearer token")
    try:
        user_id = decode_token(credentials.credentials, expected_type="access")
    except InvalidTokenError as exc:
        raise UnauthenticatedError("Invalid or expired access token") from exc

    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise UnauthenticatedError("User no longer exists")
    return user


def require_workspace_role(*allowed_roles: WorkspaceRole):
    """Dependency factory: 403s unless the user holds one of `allowed_roles` in the workspace."""

    async def _check(
        workspace_id: UUID,
        current_user: User = Depends(get_current_user),
        membership_repo: SqlAlchemyWorkspaceMembershipRepository = Depends(get_membership_repo),
    ) -> User:
        membership = await membership_repo.get(workspace_id, current_user.id)
        if membership is None or membership.role not in allowed_roles:
            raise ForbiddenError("You do not have access to this workspace")
        return current_user

    return _check
