import asyncio
from functools import lru_cache
from typing import Any

import jwt
from jwt import PyJWKClient

from ..config import settings


class EntraAuthConfigurationError(Exception):
    """Raised when Microsoft Entra token validation is not configured."""


class InvalidEntraTokenError(Exception):
    """Raised when a bearer token cannot be validated."""


def get_sample_user() -> dict[str, Any]:
    return {
        "user_principal_id": "guest-user-00000000",
        "user_name": "Guest User",
        "auth_provider": None,
        "auth_token": None,
        "aad_id_token": None,
        "client_principal_b64": None,
        "is_guest": True,
    }


@lru_cache(maxsize=4)
def _get_jwk_client(jwks_url: str) -> PyJWKClient:
    return PyJWKClient(jwks_url, cache_keys=True)


async def validate_entra_token(token: str) -> dict[str, Any]:
    tenant_id = (settings.entra_auth_tenant_id or "").strip()
    client_id = (settings.entra_auth_client_id or "").strip()
    if not tenant_id or not client_id:
        raise EntraAuthConfigurationError(
            "ENTRA_AUTH_TENANT_ID and ENTRA_AUTH_CLIENT_ID are required"
        )

    issuer = f"https://login.microsoftonline.com/{tenant_id}/v2.0"
    jwks_url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"

    try:
        signing_key = await asyncio.to_thread(
            _get_jwk_client(jwks_url).get_signing_key_from_jwt, token
        )
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=issuer,
            leeway=60,
            options={"require": ["aud", "exp", "iat", "iss"]},
        )
    except (jwt.PyJWTError, ValueError) as exc:
        raise InvalidEntraTokenError("Bearer token validation failed") from exc

    principal_id = str(claims.get("oid") or claims.get("sub") or "").strip()
    if not principal_id or claims.get("tid") != tenant_id:
        raise InvalidEntraTokenError("Bearer token has invalid identity claims")

    return claims
