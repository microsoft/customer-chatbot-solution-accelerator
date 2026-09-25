from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from starlette.requests import Request

from app import auth
from app.config import settings
from app.utils import auth_utils
from app.utils.auth_utils import InvalidEntraTokenError


def create_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = [
        (key.lower().encode("ascii"), value.encode("ascii"))
        for key, value in (headers or {}).items()
    ]
    return Request({"type": "http", "method": "GET", "path": "/", "headers": raw_headers})


def create_signed_token(
    audience: str, scope: str | None = "user_impersonation"
) -> tuple[str, object]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "aud": audience,
            "exp": now + timedelta(minutes=5),
            "iat": now,
            "iss": "https://login.microsoftonline.com/test-tenant/v2.0",
            "name": "Signed User",
            "oid": "signed-user-id",
            "preferred_username": "signed@example.com",
            **({"scp": scope} if scope is not None else {}),
            "sub": "subject-id",
            "tid": "test-tenant",
        },
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key"},
    )
    return token, private_key.public_key()


@pytest.mark.asyncio
async def test_validator_accepts_correctly_signed_token(monkeypatch: pytest.MonkeyPatch) -> None:
    token, public_key = create_signed_token("test-client")
    monkeypatch.setattr(settings, "entra_auth_client_id", "test-client")
    monkeypatch.setattr(settings, "entra_auth_tenant_id", "test-tenant")
    monkeypatch.setattr(
        auth_utils,
        "_get_jwk_client",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=public_key)
        ),
    )

    claims = await auth_utils.validate_entra_token(token)

    assert claims["oid"] == "signed-user-id"


@pytest.mark.asyncio
async def test_validator_rejects_wrong_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    token, public_key = create_signed_token("wrong-client")
    monkeypatch.setattr(settings, "entra_auth_client_id", "test-client")
    monkeypatch.setattr(settings, "entra_auth_tenant_id", "test-tenant")
    monkeypatch.setattr(
        auth_utils,
        "_get_jwk_client",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=public_key)
        ),
    )

    with pytest.raises(InvalidEntraTokenError):
        await auth_utils.validate_entra_token(token)


@pytest.mark.asyncio
@pytest.mark.parametrize("scope", [None, "openid profile"])
async def test_validator_rejects_missing_or_wrong_api_scope(
    monkeypatch: pytest.MonkeyPatch, scope: str | None
) -> None:
    token, public_key = create_signed_token("test-client", scope)
    monkeypatch.setattr(settings, "entra_auth_client_id", "test-client")
    monkeypatch.setattr(settings, "entra_auth_tenant_id", "test-tenant")
    monkeypatch.setattr(
        auth_utils,
        "_get_jwk_client",
        lambda _: SimpleNamespace(
            get_signing_key_from_jwt=lambda _: SimpleNamespace(key=public_key)
        ),
    )

    with pytest.raises(InvalidEntraTokenError):
        await auth_utils.validate_entra_token(token)


@pytest.mark.asyncio
async def test_forged_easy_auth_headers_are_ignored() -> None:
    request = create_request(
        {
            "x-ms-client-principal-id": "victim-id",
            "x-ms-client-principal-name": "victim@example.com",
        }
    )

    user = await auth.get_current_user(request)

    assert user["is_guest"] is True
    assert user["id"] == "guest-user-00000000"


@pytest.mark.asyncio
async def test_valid_bearer_token_uses_validated_claims(monkeypatch: pytest.MonkeyPatch) -> None:
    validator = AsyncMock(
        return_value={
            "oid": "signed-user-id",
            "sub": "subject-id",
            "name": "Signed User",
            "preferred_username": "signed@example.com",
        }
    )
    monkeypatch.setattr(auth, "validate_entra_token", validator)
    request = create_request(
        {
            "authorization": "Bearer signed-token",
            "x-ms-client-principal-id": "forged-user-id",
        }
    )

    user = await auth.get_current_user(request)

    validator.assert_awaited_once_with("signed-token")
    assert user["id"] == "signed-user-id"
    assert user["email"] == "signed@example.com"
    assert user["is_guest"] is False


@pytest.mark.asyncio
async def test_invalid_bearer_token_returns_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        auth,
        "validate_entra_token",
        AsyncMock(side_effect=InvalidEntraTokenError()),
    )

    with pytest.raises(HTTPException) as exc_info:
        await auth.get_current_user(create_request({"authorization": "Bearer invalid"}))

    assert exc_info.value.status_code == 401
