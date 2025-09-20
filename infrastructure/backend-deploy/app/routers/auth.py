"""
Authentication endpoints for Microsoft Entra ID
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
import requests
from datetime import datetime, timedelta
from ..config import settings
from ..auth import get_current_user, create_mock_token, verify_mock_token, create_access_token
from ..models import LoginRequest, User, Token, UserResponse, UserUpdate
from ..database import db_service

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.get("sub"),
        "name": current_user.get("name"),
        "email": current_user.get("email") or current_user.get("preferred_username"),
        "roles": current_user.get("roles", []),
        "is_authenticated": True
    }

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint - for local development with mock authentication"""
    
    # For local development, create a mock user
    if not settings.azure_tenant_id or not settings.azure_client_id:
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
    
    # Real Entra ID authentication would go here
    # This would involve redirecting to Microsoft's OAuth endpoint
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Entra ID authentication not configured. Please set AZURE_TENANT_ID and AZURE_CLIENT_ID environment variables."
    )

@router.post("/logout")
async def logout():
    """Logout endpoint"""
    return {"message": "Successfully logged out"}

@router.get("/config")
async def get_auth_config():
    """Get authentication configuration for frontend"""
    return {
        "client_id": settings.azure_client_id,
        "tenant_id": settings.azure_tenant_id,
        "authority": f"https://login.microsoftonline.com/{settings.azure_tenant_id}" if settings.azure_tenant_id else None,
        "redirect_uri": "http://localhost:5173/auth/callback",
        "scopes": ["openid", "profile", "email", "User.Read"],
        "is_configured": bool(settings.azure_tenant_id and settings.azure_client_id)
    }

@router.post("/email-login", response_model=Token)
async def login_with_email_password(login_data: LoginRequest):
    """Login with email and password (password is ignored for local testing)"""
    try:
        # Check if user exists
        user = await db_service.get_user_by_email(login_data.email)
        
        if not user:
            # Create new user if doesn't exist
            user = await db_service.create_user_with_password(
                email=login_data.email,
                name=login_data.email.split('@')[0],  # Use email prefix as name
                password=login_data.password
            )
        
        # Update last login
        user.last_login = datetime.utcnow()
        await db_service.update_user(user.id, UserUpdate(last_login=user.last_login))
        
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
    if settings.azure_tenant_id and settings.azure_client_id:
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
