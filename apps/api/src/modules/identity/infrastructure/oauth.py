from dataclasses import dataclass
from urllib.parse import urlencode

import httpx

from src.platform.config import get_settings
from src.shared_kernel.errors import ValidationError

settings = get_settings()


@dataclass(frozen=True)
class OAuthProviderConfig:
    authorize_url: str
    token_url: str
    userinfo_url: str
    scope: str
    client_id: str | None
    client_secret: str | None


@dataclass(frozen=True)
class OAuthUserInfo:
    provider_uid: str
    email: str
    full_name: str
    avatar_url: str | None


def _providers() -> dict[str, OAuthProviderConfig]:
    return {
        "google": OAuthProviderConfig(
            authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
            token_url="https://oauth2.googleapis.com/token",
            userinfo_url="https://openidconnect.googleapis.com/v1/userinfo",
            scope="openid email profile",
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
        ),
        "microsoft": OAuthProviderConfig(
            authorize_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
            token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
            userinfo_url="https://graph.microsoft.com/oidc/userinfo",
            scope="openid email profile",
            client_id=settings.microsoft_oauth_client_id,
            client_secret=settings.microsoft_oauth_client_secret,
        ),
    }


def get_provider_config(provider: str) -> OAuthProviderConfig:
    config = _providers().get(provider)
    if config is None:
        raise ValidationError(f"Unknown OAuth provider '{provider}'")
    if not config.client_id or not config.client_secret:
        raise ValidationError(
            f"OAuth provider '{provider}' is not configured "
            f"(missing client id/secret in server settings)"
        )
    return config


def redirect_uri_for(provider: str) -> str:
    return f"{settings.api_base_url}/api/v1/auth/oauth/{provider}/callback"


def build_authorize_url(provider: str, state: str) -> str:
    config = get_provider_config(provider)
    params = {
        "client_id": config.client_id,
        "redirect_uri": redirect_uri_for(provider),
        "response_type": "code",
        "scope": config.scope,
        "state": state,
    }
    return f"{config.authorize_url}?{urlencode(params)}"


async def exchange_code_and_fetch_user(provider: str, code: str) -> OAuthUserInfo:
    config = get_provider_config(provider)
    async with httpx.AsyncClient(timeout=10.0) as client:
        token_response = await client.post(
            config.token_url,
            data={
                "client_id": config.client_id,
                "client_secret": config.client_secret,
                "code": code,
                "redirect_uri": redirect_uri_for(provider),
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        if token_response.status_code != 200:
            raise ValidationError(f"OAuth token exchange with '{provider}' failed")
        access_token = token_response.json()["access_token"]

        userinfo_response = await client.get(
            config.userinfo_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if userinfo_response.status_code != 200:
            raise ValidationError(f"OAuth userinfo fetch from '{provider}' failed")
        info = userinfo_response.json()

    return OAuthUserInfo(
        provider_uid=info["sub"],
        email=info["email"],
        full_name=info.get("name") or info["email"],
        avatar_url=info.get("picture"),
    )
