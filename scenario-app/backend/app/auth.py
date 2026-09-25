import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status

from .utils.auth_utils import (
    EntraAuthConfigurationError,
    InvalidEntraTokenError,
    validate_entra_token,
)

logger = logging.getLogger(__name__)

# Attribute name used by EntraAuthMiddleware to store the resolved user.
STATE_ATTR = "entra_user"
_UNSET = object()


def _build_user_from_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    principal_id = str(claims.get("oid") or claims["sub"])
    email = str(
        claims.get("email")
        or claims.get("preferred_username")
        or claims.get("upn")
        or ""
    )
    name = str(claims.get("name") or email or principal_id)
    return {
        "id": principal_id,
        "user_id": principal_id,
        "sub": principal_id,
        "name": name,
        "email": email,
        "preferred_username": email,
        "roles": ["customer"],
        "auth_provider": "aad",
    }


async def resolve_bearer_user(request: Request) -> Optional[Dict[str, Any]]:
    """Validate the Authorization bearer header. Returns None when absent.

    Raises HTTPException(401) for a malformed/invalid token and
    HTTPException(503) when JWT validation is not configured.
    """
    authorization = request.headers.get("authorization", "").strip()
    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = await validate_entra_token(token.strip())
    except EntraAuthConfigurationError:
        logger.error("Microsoft Entra JWT validation is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured",
        )
    except InvalidEntraTokenError:
        logger.warning("Rejected an invalid Microsoft Entra bearer token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return _build_user_from_claims(claims)


async def get_current_user(request: Request) -> Dict[str, Any]:
    """Return the authenticated customer or raise 401 when the caller is unauthenticated."""
    cached = getattr(request.state, STATE_ATTR, _UNSET)
    user = cached if cached is not _UNSET else await resolve_bearer_user(request)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Backwards-compatible alias; the strict get_current_user is the single canonical dependency.
get_current_authenticated_user = get_current_user
