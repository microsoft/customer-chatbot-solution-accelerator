import logging

from fastapi import APIRouter, HTTPException, Request

from ..auth import get_current_user
from ..database import get_db_service
from ..services.user_onboarding import create_demo_order_history
from ..utils.event_utils import track_event_if_configured

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.get("/me")
async def get_current_user_info(request: Request):
    try:
        current_user = await get_current_user(request)

        logger.info(
            "🔍 /api/auth/me: Authenticated user detected - will check/create in Azure Cosmos DB"
        )

        user_id = current_user.get("sub", current_user.get("id"))
        email = current_user.get("email", current_user.get("preferred_username"))
        name = current_user.get("name", "Unknown User")

        logger.info(
            f"🔍 /api/auth/me: Processing user - ID: {user_id}, Email: {email}, Name: {name}"
        )

        logger.info(f"Getting user info for: {email} (ID: {user_id})")

        db_service = get_db_service()
        user = None

        # First try to get user by Easy Auth ID
        if user_id:
            try:
                user = await db_service.get_user(user_id)
                logger.info(
                    f"Found existing user by ID: {user.email if user else 'None'}"
                )
            except Exception as e:
                logger.warning(f"Error getting user by ID: {e}")
        else:
            logger.warning("No user_id available from auth headers")

        # If not found by ID, try by email (for backward compatibility)
        if not user and email:
            try:
                user = await db_service.get_user_by_email(email)
                logger.info(
                    f"Found existing user by email: {user.email if user else 'None'}"
                )
            except Exception as e:
                logger.warning(f"Error getting user by email: {e}")

        if not user:
            logger.info(f"Creating new user: {email} with ID: {user_id}")

            # Ensure we have required fields for user creation
            if not email:
                logger.error("Cannot create user: email is missing")
                raise HTTPException(
                    status_code=400, detail="Email is required for user creation"
                )

            if not name:
                name = "Unknown User"  # Provide a default name

            try:
                user = await db_service.create_user_with_password(
                    email=email,
                    name=name,
                    password="",
                    user_id=user_id,  # Use Easy Auth user_principal_id as Azure Cosmos DB user ID
                )
                logger.info(f"Created new user: {user.email}")
                track_event_if_configured("Auth_User_Created", {"user_id": user_id, "email": email})

                try:
                    logger.info(f"Creating demo order history for new user: {user.id}")
                    await create_demo_order_history(user.id)
                    logger.info(f"Demo order history created for user: {user.id}")
                except Exception as e:
                    logger.error(f"Failed to create demo order history: {e}")

            except Exception as e:
                logger.error(f"Error creating user: {e}")
                return {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "roles": ["user"],
                    "is_authenticated": True,
                    "is_guest": False,
                }

        response_data = {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "roles": [user.role.value] if hasattr(user, "role") else ["user"],
            "is_authenticated": True,
            "is_guest": False,
        }
        track_event_if_configured("Auth_User_Authenticated", {"user_id": str(user.id)})
        logger.info(
            f"🔍 /api/auth/me: Returning authenticated user data: {response_data}"
        )
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user_info: {e}")
        raise HTTPException(status_code=500, detail="Error fetching current user")
