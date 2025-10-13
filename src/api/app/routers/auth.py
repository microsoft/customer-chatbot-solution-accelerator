"""
Authentication endpoints for Microsoft Entra ID
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from ..config import settings, has_entra_id_config
from ..auth import get_current_user, create_mock_token, verify_mock_token, create_access_token
from ..models import LoginRequest, User, Token, UserResponse, UserUpdate
from ..database import get_db_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    try:
        # Extract user information from ID token
        user_id = current_user.get("sub", current_user.get("oid", current_user.get("user_id")))
        email = current_user.get("preferred_username", current_user.get("email"))
        name = current_user.get("name", "Unknown User")
        
        print(f"🔍 ID Token claims: sub={current_user.get('sub')}, oid={current_user.get('oid')}, preferred_username={current_user.get('preferred_username')}, name={current_user.get('name')}")
        
        print(f"🔍 Getting user info for: {email} (ID: {user_id})")
        
        # Try to get user from database
        db_service = get_db_service()
        user = None
        
        if email:
            try:
                user = await db_service.get_user_by_email(email)
                print(f"📊 Found existing user: {user.email if user else 'None'}")
            except Exception as e:
                print(f"⚠️ Error getting user by email: {e}")
        
        # If user doesn't exist, create them
        if not user:
            print(f"👤 Creating new user: {email}")
            try:
                user = await db_service.create_user_with_password(
                    email=email,
                    name=name,
                    password=""  # No password for Entra ID users
                )
                print(f"✅ Created new user: {user.email}")
            except Exception as e:
                print(f"❌ Error creating user: {e}")
                # Return basic info even if user creation fails
                return {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "roles": ["user"],
                    "is_authenticated": True
                }
        
        return {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "roles": [user.role.value] if hasattr(user, 'role') else ["user"],
            "is_authenticated": True
        }
        
    except Exception as e:
        print(f"❌ Error in get_current_user_info: {e}")
        # Fallback to basic token info
        return {
            "id": current_user.get("sub", current_user.get("user_id")),
            "name": current_user.get("name", "Unknown User"),
            "email": current_user.get("email", current_user.get("preferred_username")),
            "roles": current_user.get("roles", ["user"]),
            "is_authenticated": True
        }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - supports both mock and Entra ID authentication"""
    
    # Check if we have Entra ID configuration
    if has_entra_id_config():
        # Real Entra ID authentication - redirect to Microsoft
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Please use the frontend login flow for Entra ID authentication"
        )
    
    # Mock authentication for local development
    user_data = {
        "sub": "local-dev-user",
        "name": "Local Developer",
        "email": form_data.username or "dev@localhost.com",
        "roles": ["user"]
    }
    
    token = create_mock_token(user_data)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_data["sub"],
            "name": user_data["name"],
            "email": user_data["email"],
            "roles": user_data["roles"]
        }
    }

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Successfully logged out"}

@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend"""
    return {
        "azure_client_id": settings.azure_client_id,
        "azure_tenant_id": settings.azure_tenant_id,
        "azure_authority": f"https://login.microsoftonline.com/{settings.azure_tenant_id}" if settings.azure_tenant_id else None,
        "is_entra_id_configured": has_entra_id_config(),
        "is_local_dev": not has_entra_id_config()
    }

@router.post("/email-login", response_model=Token)
async def login_with_email_password(login_data: LoginRequest):
    """Login with email and password (password is ignored for local testing)"""
    try:
        # Check if user exists
        user = await get_db_service().get_user_by_email(login_data.email)
        
        if not user:
            # Create new user if doesn't exist
            user = await get_db_service().create_user_with_password(
                email=login_data.email,
                name=login_data.email.split('@')[0],  # Use email prefix as name
                password=login_data.password
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await get_db_service().update_user(user.id, UserUpdate(last_login=user.last_login))
        
        # Create JWT token
        access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "scopes": ["me"]}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": UserResponse(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role.value,
                is_active=user.is_active
            )
        }
        
    except Exception as e:
        import traceback
        print(f"Login error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@router.post("/mock-login")
async def mock_login(username: str = "dev@localhost.com", name: str = "Local Developer"):
    """Mock login endpoint for local development"""
    if has_entra_id_config():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mock login only available when Entra ID is not configured"
        )
    
    user_data = {
        "sub": f"mock-{username}",
        "name": name,
        "email": username,
        "roles": ["user"]
    }
    
    token = create_mock_token(user_data)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_data["sub"],
            "name": user_data["name"],
            "email": user_data["email"],
            "roles": user_data["roles"]
        }
    }
