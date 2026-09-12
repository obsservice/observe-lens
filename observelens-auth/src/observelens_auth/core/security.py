import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from observelens_auth.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def new_service_token() -> str:
    return f"olsa_{secrets.token_urlsafe(36)}"


def create_access_token(
    *, user_id: str, tenant_id: str, role: str, permissions: list[str], session_id: str
) -> tuple[str, datetime, str]:
    settings = get_settings()
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    jti = str(uuid4())
    payload: dict[str, Any] = {
        "sub": user_id,
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "permissions": permissions,
        "session_id": session_id,
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, expires_at, jti


def decode_access_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],
        options={"require": ["exp", "iat", "jti", "sub", "tenant_id"]},
    )
