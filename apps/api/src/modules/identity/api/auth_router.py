import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.api.dependencies import get_current_user
from src.modules.identity.api.schemas import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairOut,
    UserOut,
)
from src.modules.identity.application.use_cases import (
    LoginUseCase,
    LogoutUseCase,
    OAuthLoginUseCase,
    RefreshAccessTokenUseCase,
    RegisterUserUseCase,
)
from src.modules.identity.domain.entities import User
from src.modules.identity.infrastructure.oauth import (
    build_authorize_url,
    exchange_code_and_fetch_user,
)
from src.modules.identity.infrastructure.repositories import (
    SqlAlchemyOAuthIdentityRepository,
    SqlAlchemyOrganizationRepository,
    SqlAlchemyRefreshTokenRepository,
    SqlAlchemyUserRepository,
    SqlAlchemyWorkspaceMembershipRepository,
    SqlAlchemyWorkspaceRepository,
)
from src.platform.config import get_settings
from src.platform.db import get_db
from src.shared_kernel.errors import ValidationError
from src.shared_kernel.schemas import ItemResponse

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
settings = get_settings()

# In-memory OAuth state store: fine for a single-instance Phase 1 deployment,
# will move to Redis once the API runs with multiple replicas.
_oauth_states: set[str] = set()


@router.post("/register", response_model=ItemResponse[AuthResponse], status_code=201)
async def register(
    body: RegisterRequest, db: AsyncSession = Depends(get_db)
) -> ItemResponse[AuthResponse]:
    use_case = RegisterUserUseCase(
        SqlAlchemyUserRepository(db),
        SqlAlchemyOrganizationRepository(db),
        SqlAlchemyWorkspaceRepository(db),
        SqlAlchemyWorkspaceMembershipRepository(db),
    )
    user = await use_case.execute(
        email=body.email, password=body.password, full_name=body.full_name
    )

    login_use_case = LoginUseCase(
        SqlAlchemyUserRepository(db), SqlAlchemyRefreshTokenRepository(db)
    )
    _, tokens = await login_use_case.execute(email=body.email, password=body.password)
    await db.commit()

    return ItemResponse(
        data=AuthResponse(
            user=UserOut.model_validate(user),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    )


@router.post("/login", response_model=ItemResponse[AuthResponse])
async def login(
    body: LoginRequest, db: AsyncSession = Depends(get_db)
) -> ItemResponse[AuthResponse]:
    use_case = LoginUseCase(SqlAlchemyUserRepository(db), SqlAlchemyRefreshTokenRepository(db))
    user, tokens = await use_case.execute(email=body.email, password=body.password)
    await db.commit()

    return ItemResponse(
        data=AuthResponse(
            user=UserOut.model_validate(user),
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
        )
    )


@router.post("/refresh", response_model=ItemResponse[TokenPairOut])
async def refresh(
    body: RefreshRequest, db: AsyncSession = Depends(get_db)
) -> ItemResponse[TokenPairOut]:
    use_case = RefreshAccessTokenUseCase(
        SqlAlchemyRefreshTokenRepository(db), SqlAlchemyUserRepository(db)
    )
    tokens = await use_case.execute(body.refresh_token)
    await db.commit()
    return ItemResponse(
        data=TokenPairOut(access_token=tokens.access_token, refresh_token=tokens.refresh_token)
    )


@router.post("/logout", status_code=204)
async def logout(body: LogoutRequest, db: AsyncSession = Depends(get_db)) -> None:
    use_case = LogoutUseCase(SqlAlchemyRefreshTokenRepository(db))
    await use_case.execute(body.refresh_token)
    await db.commit()


@router.get("/me", response_model=ItemResponse[UserOut])
async def me(current_user: User = Depends(get_current_user)) -> ItemResponse[UserOut]:
    return ItemResponse(data=UserOut.model_validate(current_user))


@router.get("/oauth/{provider}/start")
async def oauth_start(provider: str) -> RedirectResponse:
    state = secrets.token_urlsafe(24)
    _oauth_states.add(state)
    return RedirectResponse(build_authorize_url(provider, state))


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str, code: str, state: str, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    if state not in _oauth_states:
        raise ValidationError("Invalid or expired OAuth state")
    _oauth_states.discard(state)

    user_info = await exchange_code_and_fetch_user(provider, code)

    use_case = OAuthLoginUseCase(
        SqlAlchemyUserRepository(db),
        SqlAlchemyOrganizationRepository(db),
        SqlAlchemyWorkspaceRepository(db),
        SqlAlchemyWorkspaceMembershipRepository(db),
        SqlAlchemyOAuthIdentityRepository(db),
        SqlAlchemyRefreshTokenRepository(db),
    )
    _, tokens = await use_case.execute(
        provider=provider,
        provider_uid=user_info.provider_uid,
        email=user_info.email,
        full_name=user_info.full_name,
    )
    await db.commit()

    fragment = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
    )
    return RedirectResponse(f"{settings.frontend_url}/auth/callback#{fragment}")
