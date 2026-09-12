from datetime import UTC, datetime

import jwt

from observelens_auth.core.config import get_settings
from observelens_auth.core.security import create_access_token, decode_access_token, hash_token


def test_access_token_contains_required_authorization_claims() -> None:
    token, expires_at, jti = create_access_token(
        user_id="7d5bf017-53ee-4919-a983-b8fed48669ea",
        tenant_id="4eaf05fd-68c1-4275-9e2c-4957354bbf64",
        role="admin",
        permissions=["*"],
        session_id="f2ed0ad8-e651-4c93-98c3-291b5c7b7445",
    )

    payload = decode_access_token(token)

    assert payload["jti"] == jti
    assert payload["tenant_id"] == "4eaf05fd-68c1-4275-9e2c-4957354bbf64"
    assert payload["permissions"] == ["*"]
    assert payload["exp"] >= int(datetime.now(UTC).timestamp())
    assert expires_at > datetime.now(UTC)


def test_access_token_rejects_invalid_signature() -> None:
    token, _, _ = create_access_token(
        user_id="7d5bf017-53ee-4919-a983-b8fed48669ea",
        tenant_id="4eaf05fd-68c1-4275-9e2c-4957354bbf64",
        role="viewer",
        permissions=["trace:read"],
        session_id="f2ed0ad8-e651-4c93-98c3-291b5c7b7445",
    )
    settings = get_settings()
    forged = jwt.encode(
        {"sub": "attacker", "tenant_id": "attacker", "jti": "x", "iat": 1, "exp": 1893456000},
        "different-secret",
        algorithm=settings.jwt_algorithm,
    )

    assert token != forged
    try:
        decode_access_token(forged)
    except jwt.InvalidSignatureError:
        pass
    else:
        raise AssertionError("Expected forged token to be rejected")


def test_token_hash_is_deterministic_and_not_plaintext() -> None:
    token = "olsa_a_sensitive_token"

    assert hash_token(token) == hash_token(token)
    assert hash_token(token) != token
