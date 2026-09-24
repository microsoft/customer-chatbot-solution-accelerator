import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status

from .utils.auth_utils import (
    EntraAuthConfigurationError,
    InvalidEntraTokenError,
    get_sample_user,
    validate_entra_token,
)

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user for e-commerce operations.
    Returns user details or guest user for anonymous shopping.
    """
    authorization = request.headers.get("authorization", "").strip()
    if not authorization:
        guest_user = get_sample_user()
        return {
            "id": guest_user["user_principal_id"],
            "user_id": guest_user["user_principal_id"],
            "sub": guest_user["user_principal_id"],
            "name": guest_user["user_name"],
            "email": "guest@ecommerce.com",
            "preferred_username": "guest@ecommerce.com",
            "roles": ["customer", "guest"],
            "is_guest": True,
        }

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
        "is_guest": False,
    }


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user but allow None return for optional authentication endpoints.
    """
    return await get_current_user(request)
