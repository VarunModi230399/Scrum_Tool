import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from src.platform.config import get_settings

settings = get_settings()

TokenType = Literal["access", "refresh"]

# bcrypt's own limit: longer secrets are rejected outright rather than silently truncated.
_MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    password_bytes = password.encode("utf-8")[:_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(password_bytes, password_hash.encode("ascii"))


def create_access_token(user_id: UUID) -> str:
    return _encode_token(user_id, "access", timedelta(minutes=settings.access_token_expire_minutes))


def create_refresh_token(user_id: UUID) -> tuple[str, datetime]:
    expires_at = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    token = _encode_token(user_id, "refresh", timedelta(days=settings.refresh_token_expire_days))
    return token, expires_at


def _encode_token(user_id: UUID, token_type: TokenType, expires_delta: timedelta) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str, expected_type: TokenType) -> UUID:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("Token is invalid or expired") from exc

    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token")

    return UUID(payload["sub"])


def hash_token(token: str) -> str:
    """One-way hash of a refresh token for storage/lookup (raw token is never persisted)."""
    return hashlib.sha256(token.encode()).hexdigest()


class InvalidTokenError(Exception):
    pass
