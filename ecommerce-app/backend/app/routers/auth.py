import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Depends

from ..auth import get_current_user
from ..database import get_db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/debug")
async def debug_auth_headers(request: Request):
    """Debug endpoint to see all headers and Easy Auth status for e-commerce"""
    headers = dict(request.headers)

    # Check for Easy Auth headers
    easy_auth_headers = {k: v for k, v in headers.items() if "x-ms-client" in k.lower()}

    return {
        "service": "ecommerce",
        "all_headers": headers,
        "easy_auth_headers": easy_auth_headers,
        "has_easy_auth": len(easy_auth_headers) > 0,
        "user_agent": headers.get("user-agent", "unknown"),
        "host": headers.get("host", "unknown"),
        "x_forwarded_for": headers.get("x-forwarded-for", "none"),
        "x_forwarded_proto": headers.get("x-forwarded-proto", "none"),
    }


@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current customer information for e-commerce"""
    try:
        # Enhanced debugging for Easy Auth headers in e-commerce context
        headers = dict(request.headers)
        logger.info("🛒 /api/auth/me: E-COMMERCE REQUEST HEADERS:")
        for key, value in headers.items():
            logger.info(f"  {key}: {value}")

        # Check specifically for Easy Auth headers (forwarded from frontend)
        easy_auth_headers = {
            k: v for k, v in headers.items() if "x-ms-client" in k.lower()
        }
        logger.info(f"🛒 /api/auth/me: Easy Auth headers found: {easy_auth_headers}")

        current_user = await get_current_user(request)
        logger.info(
            f"🛒 /api/auth/me: Current customer from get_current_user: {current_user}"
        )

        if current_user.get("is_guest"):
            guest_response = {
                "id": current_user["id"],
                "name": current_user["name"],
                "email": current_user["email"],
                "roles": current_user["roles"],
                "is_authenticated": False,
                "is_guest": True,
                "service": "ecommerce"
            }
            logger.info(f"🛒 /api/auth/me: Returning guest customer data: {guest_response}")
            return guest_response

        user_id = current_user.get("sub", current_user.get("id"))
        email = current_user.get("email", current_user.get("preferred_username"))
        logger.info(f"🛒 /api/auth/me: Processing authenticated customer: {user_id}")

        # Create or get customer profile in database
        try:
            customer = await get_db_service().get_or_create_customer(
                user_id=user_id,
                email=email,
                name=current_user.get("name", ""),
            )
            logger.info(f"🛒 /api/auth/me: Customer profile created/retrieved: {customer}")
        except Exception as e:
            logger.error(f"🛒 /api/auth/me: Error creating customer profile: {e}")
            customer = None

        return {
            "id": user_id,
            "name": current_user.get("name", ""),
            "email": email,
            "roles": current_user.get("roles", ["customer"]),
            "is_authenticated": True,
            "is_guest": False,
            "customer_profile": customer,
            "service": "ecommerce"
        }

    except Exception as e:
        logger.exception(f"🛒 /api/auth/me: Error in get current user info: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")


@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout current customer (clear session data)"""
    try:
        user_id = current_user.get("user_id")
        if user_id:
            # Clear any session-specific data if needed
            # For now, just return success - actual logout handled by frontend
            logger.info(f"🛒 Customer logout: {user_id}")

        return {"message": "Logout successful", "service": "ecommerce"}
    except Exception as e:
        logger.exception(f"🛒 Logout error: {e}")
        raise HTTPException(status_code=500, detail=f"Logout error: {str(e)}")


@router.get("/profile")
async def get_customer_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get detailed customer profile and order history"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        if current_user.get("is_guest"):
            return {
                "message": "Guest user - no profile available",
                "is_guest": True,
                "service": "ecommerce"
            }

        # Get customer profile
        customer = await get_db_service().get_customer(user_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer profile not found")

        # Get recent orders
        orders = await get_db_service().get_customer_orders(user_id, limit=10)

        return {
            "customer": customer,
            "recent_orders": orders,
            "service": "ecommerce"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"🛒 Error fetching customer profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")