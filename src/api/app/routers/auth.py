from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Dict, Any
from ..auth import get_current_user
from ..database import get_db_service
from ..services.user_onboarding import create_demo_order_history
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/debug")
async def debug_auth_headers(request: Request):
    """Debug endpoint to see all headers and Easy Auth status"""
    headers = dict(request.headers)
    
    # Check for Easy Auth headers
    easy_auth_headers = {k: v for k, v in headers.items() if 'x-ms-client' in k.lower()}
    
    return {
        "all_headers": headers,
        "easy_auth_headers": easy_auth_headers,
        "has_easy_auth": len(easy_auth_headers) > 0,
        "user_agent": headers.get("user-agent", "unknown"),
        "host": headers.get("host", "unknown"),
        "x_forwarded_for": headers.get("x-forwarded-for", "none"),
        "x_forwarded_proto": headers.get("x-forwarded-proto", "none")
    }

@router.get("/me")
async def get_current_user_info(request: Request):
    try:
        # Enhanced debugging for Easy Auth headers
        headers = dict(request.headers)
        logger.info(f"🔍 /api/auth/me: ALL REQUEST HEADERS:")
        for key, value in headers.items():
            logger.info(f"  {key}: {value}")
        
        # Check specifically for Easy Auth headers (forwarded from frontend)
        easy_auth_headers = {k: v for k, v in headers.items() if 'x-ms-client' in k.lower()}
        logger.info(f"🔍 /api/auth/me: Easy Auth headers found: {easy_auth_headers}")
        
        # Check for other potential auth headers
        auth_headers = {k: v for k, v in headers.items() if 'auth' in k.lower() or 'token' in k.lower()}
        logger.info(f"🔍 /api/auth/me: Other auth-related headers: {auth_headers}")
        
        current_user = await get_current_user(request)
        logger.info(f"🔍 /api/auth/me: Current user from get_current_user: {current_user}")
        
        # Additional logging for user creation process
        if not current_user.get("is_guest"):
            logger.info(f"🔍 /api/auth/me: Authenticated user detected - will check/create in Cosmos DB")
        
        if current_user.get("is_guest"):
            guest_response = {
                "id": current_user["id"],
                "name": current_user["name"],
                "email": current_user["email"],
                "roles": current_user["roles"],
                "is_authenticated": False,
                "is_guest": True
            }
            logger.info(f"🔍 /api/auth/me: Returning guest user data: {guest_response}")
            return guest_response
        
        user_id = current_user.get("sub", current_user.get("id"))
        email = current_user.get("preferred_username", current_user.get("email"))
        name = current_user.get("name", "Unknown User")
        
        logger.info(f"🔍 /api/auth/me: Processing user - ID: {user_id}, Email: {email}, Name: {name}")
        
        logger.info(f"Getting user info for: {email} (ID: {user_id})")
        
        db_service = get_db_service()
        user = None
        
        # First try to get user by Easy Auth ID
        if user_id:
            try:
                user = await db_service.get_user(user_id)
                logger.info(f"Found existing user by ID: {user.email if user else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting user by ID: {e}")
        else:
            logger.warning("No user_id available from auth headers")
        
        # If not found by ID, try by email (for backward compatibility)
        if not user and email:
            try:
                user = await db_service.get_user_by_email(email)
                logger.info(f"Found existing user by email: {user.email if user else 'None'}")
            except Exception as e:
                logger.warning(f"Error getting user by email: {e}")
        
        if not user:
            logger.info(f"Creating new user: {email} with ID: {user_id}")
            
            # Ensure we have required fields for user creation
            if not email:
                logger.error("Cannot create user: email is missing")
                raise HTTPException(status_code=400, detail="Email is required for user creation")
            
            if not name:
                name = "Unknown User"  # Provide a default name
                
            try:
                user = await db_service.create_user_with_password(
                    email=email,
                    name=name,
                    password="",
                    user_id=user_id  # Use Easy Auth user_principal_id as Cosmos DB user ID
                )
                logger.info(f"Created new user: {user.email}")
                
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
                    "is_guest": False
                }
        
        response_data = {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "roles": [user.role.value] if hasattr(user, 'role') else ["user"],
            "is_authenticated": True,
            "is_guest": False
        }
        logger.info(f"🔍 /api/auth/me: Returning authenticated user data: {response_data}")
        return response_data
        
    except Exception as e:
        logger.error(f"Error in get_current_user_info: {e}")
        return {
            "id": "guest-user-00000000",
            "name": "Guest User",
            "email": "guest@contoso.com",
            "roles": ["guest"],
            "is_authenticated": False,
            "is_guest": True
        }
