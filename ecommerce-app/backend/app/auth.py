import logging
from typing import Any, Dict, Optional

from fastapi import Request

from .utils.auth_utils import (
    get_authenticated_user_details,
    get_sample_user,
    get_user_email,
)

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Get current authenticated user for e-commerce operations.
    Returns user details or guest user for anonymous shopping.
    """
    try:
        headers = dict(request.headers)

        # Check for forwarded Easy Auth headers from frontend
        forwarded_easy_auth_headers = {
            "x-ms-client-principal-id": headers.get("x-ms-client-principal-id"),
            "x-ms-client-principal-name": headers.get("x-ms-client-principal-name"),
            "x-ms-client-principal-idp": headers.get("x-ms-client-principal-idp"),
            "x-ms-client-principal": headers.get("x-ms-client-principal"),
            "x-ms-token-aad-id-token": headers.get("x-ms-token-aad-id-token"),
        }

        # Remove None values
        forwarded_easy_auth_headers = {
            k: v for k, v in forwarded_easy_auth_headers.items() if v is not None
        }

        logger.info(
            f"🛒 E-COMMERCE AUTH: Checking for forwarded Easy Auth headers: {list(forwarded_easy_auth_headers.keys())}"
        )

        if forwarded_easy_auth_headers and forwarded_easy_auth_headers.get(
            "x-ms-client-principal-id"
        ):
            logger.info(
                "🛒 E-COMMERCE AUTH: Found valid forwarded Easy Auth headers from frontend"
            )
            user_details: Dict[str, Any] = dict(forwarded_easy_auth_headers)
            user_details["is_guest"] = False
            user_details["user_principal_id"] = (
                forwarded_easy_auth_headers.get("x-ms-client-principal-id") or ""
            )
            user_details["user_name"] = (
                forwarded_easy_auth_headers.get("x-ms-client-principal-name") or ""
            )
            user_details["auth_provider"] = (
                forwarded_easy_auth_headers.get("x-ms-client-principal-idp") or ""
            )
        else:
            # Fall back to direct Easy Auth headers
            logger.info(
                "🛒 E-COMMERCE AUTH: No valid forwarded headers, checking for direct Easy Auth headers"
            )
            user_details = get_authenticated_user_details(headers)

        # Check if user is a guest (allow anonymous shopping)
        is_guest_value = user_details.get("is_guest")
        is_guest = (
            is_guest_value is True or is_guest_value == "true" or is_guest_value == True
        )

        if is_guest:
            logger.info("🛒 E-COMMERCE: Guest user shopping")
            return {
                "id": user_details["user_principal_id"],
                "user_id": user_details["user_principal_id"],
                "sub": user_details["user_principal_id"],
                "name": user_details["user_name"],
                "email": "guest@ecommerce.com",
                "preferred_username": "guest@ecommerce.com",
                "roles": ["customer", "guest"],
                "is_guest": True,
            }

        logger.info(
            f"🛒 E-COMMERCE: Authenticated customer: {user_details.get('user_name')} ({user_details.get('user_principal_id')})"
        )

        # Extract email from the client principal token if available
        user_email = ""
        client_principal_b64 = user_details.get(
            "client_principal_b64"
        ) or user_details.get("x-ms-client-principal")
        if client_principal_b64:
            user_email = get_user_email(client_principal_b64)

        # Fallback to user_name if no email found
        if not user_email:
            user_email = user_details.get("user_name", "")

        return {
            "id": user_details["user_principal_id"],
            "user_id": user_details["user_principal_id"],
            "sub": user_details["user_principal_id"],
            "name": user_details["user_name"],
            "email": user_email,
            "preferred_username": user_email or user_details["user_name"],
            "roles": ["customer"],
            "auth_provider": user_details.get("auth_provider"),
            "is_guest": False,
        }

    except Exception as e:
        logger.error(f"🛒 E-COMMERCE AUTH: Error getting user: {e}", exc_info=True)
        # Return guest user as fallback for anonymous shopping
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


async def get_current_user_optional(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get current user but allow None return for optional authentication endpoints.
    """
    try:
        return await get_current_user(request)
    except Exception:
        return None