import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Depends

from ..auth import get_current_user
from ..database import get_db_service
from ..scenario_config import current_scenario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/me")
async def get_current_user_info(request: Request):
    """Get current customer information for e-commerce"""
    try:
        current_user = await get_current_user(request)

        if current_user.get("is_guest"):
            guest_response = {
                "id": current_user["id"],
                "name": current_user["name"],
                "email": current_user["email"],
                "roles": current_user["roles"],
                "is_authenticated": False,
                "is_guest": True,
                "service": current_scenario()
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
            "service": current_scenario()
        }

    except HTTPException:
        raise
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

        return {"message": "Logout successful", "service": current_scenario()}
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
                "service": current_scenario()
            }

        # Get customer profile
        customer = await get_db_service().get_customer(user_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer profile not found")

        # Get recent orders
        orders = await get_db_service().get_customer_orders(user_id, page_size=10)

        return {
            "customer": customer,
            "recent_orders": orders,
            "service": current_scenario()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"🛒 Error fetching customer profile: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")
