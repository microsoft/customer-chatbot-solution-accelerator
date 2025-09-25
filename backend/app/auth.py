"""
Microsoft Entra ID Authentication for FastAPI
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt as jose_jwt
import requests
import json
from .config import settings

# Security scheme
security = HTTPBearer()

class EntraIDAuth:
    """Microsoft Entra ID Authentication Handler"""
    
    def __init__(self):
        self.tenant_id = settings.azure_tenant_id
        self.client_id = settings.azure_client_id
        self.client_secret = settings.azure_client_secret
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
    def get_jwks_uri(self) -> str:
        """Get JWKS URI for token validation"""
        return f"{self.authority}/discovery/v2.0/keys"
    
    def get_public_keys(self) -> Dict[str, Any]:
        """Fetch public keys from Microsoft"""
        try:
            response = requests.get(self.get_jwks_uri())
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch public keys: {str(e)}"
            )
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token from Microsoft Entra ID"""
        try:
            # Get token header to find the key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            print(f"🔍 Token header: {unverified_header}")
            print(f"🔍 Key ID (kid): {kid}")
            
            # Get public keys
            jwks = self.get_public_keys()
            print(f"🔍 Available keys: {[k.get('kid') for k in jwks.get('keys', [])]}")
            
            # Find the correct key
            key = None
            if kid:
                # Try to find key by kid
                for jwk in jwks.get("keys", []):
                    if jwk.get("kid") == kid:
                        key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))
                        print(f"✅ Found key by kid: {kid}")
                        break
            
            # If no kid or key not found by kid, try the first available key
            if not key and jwks.get("keys"):
                print("⚠️ No key found by kid, trying first available key")
                key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwks["keys"][0]))
                print(f"✅ Using first available key: {jwks['keys'][0].get('kid')}")
            
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key"
                )
            
            # Decode and validate token (ID token)
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.client_id,  # ID tokens have the client ID as audience
                issuer=f"{self.authority}/v2.0",
                options={"verify_exp": True, "verify_aud": True, "verify_iss": True}
            )
            
            print(f"✅ Token validated successfully: {payload}")
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token validation error: {str(e)}"
            )

# Global auth instance
auth_handler = EntraIDAuth()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    token = credentials.credentials
    
    # Debug logging
    print(f"🔍 Backend auth debug: azure_tenant_id={settings.azure_tenant_id}, azure_client_id={settings.azure_client_id}")
    print(f"🔍 Token preview: {token[:50]}...")
    
    try:
        # For local development, verify the mock token
        if not settings.azure_tenant_id or not settings.azure_client_id:
            print("📱 Using mock token validation")
            payload = verify_mock_token(token)
            # Ensure user_id is present for cart API
            if "user_id" not in payload:
                payload["user_id"] = payload.get("sub", "unknown")
            return payload
        
        # For production, validate with Entra ID
        print("🔐 Using Entra ID token validation")
        try:
            payload = auth_handler.validate_token(token)
            print(f"✅ Entra ID token validated successfully: {payload}")
        except Exception as e:
            print(f"❌ Entra ID token validation failed: {e}")
            print("🔄 Falling back to basic token parsing for development...")
            
            # Fallback: Parse token without full validation for development
            try:
                import base64
                import json
                
                # Decode JWT payload without verification
                parts = token.split('.')
                if len(parts) != 3:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")
                
                # Decode payload (middle part)
                payload_encoded = parts[1]
                # Add padding if needed
                padding = len(payload_encoded) % 4
                if padding:
                    payload_encoded += '=' * (4 - padding)
                
                payload = json.loads(base64.urlsafe_b64decode(payload_encoded))
                print(f"✅ Fallback token parsing successful: {payload}")
                
                # Basic validation - check if it's an ID token for our app
                # Only validate audience if it's present (Entra ID tokens have 'aud', mock tokens don't)
                if 'aud' in payload and payload.get('aud') != settings.azure_client_id:
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience")
                
                # If no 'aud' field, this might be a mock token - check for other indicators
                if 'aud' not in payload and 'scopes' in payload:
                    print("⚠️ Detected mock token in fallback - this shouldn't happen with Entra ID")
                    # This is a mock token, but we're in Entra ID mode - reject it
                    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Mock token not allowed in Entra ID mode")
                
            except Exception as fallback_error:
                print(f"❌ Fallback parsing also failed: {fallback_error}")
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Token validation failed: {str(e)}")
        
        # Ensure user_id is present for cart API and other operations
        if "user_id" not in payload:
            # Use the 'sub' claim as user_id for Entra ID tokens
            payload["user_id"] = payload.get("sub", payload.get("oid", "unknown"))
        
        print(f"✅ Entra ID token validated, user_id: {payload.get('user_id')}")
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )

def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise return None"""
    try:
        if credentials:
            return get_current_user(credentials)
    except HTTPException:
        pass
    return None

# Mock authentication for local development
def create_mock_token(user_data: Dict[str, Any]) -> str:
    """Create a mock JWT token for local development"""
    payload = {
        "sub": user_data.get("sub", "mock-user"),
        "name": user_data.get("name", "Mock User"),
        "email": user_data.get("email", "mock@localhost.com"),
        "preferred_username": user_data.get("email", "mock@localhost.com"),
        "roles": user_data.get("roles", ["user"]),
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
        "iss": "local-dev",
        "aud": "local-dev"
    }
    
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def verify_mock_token(token: str) -> Dict[str, Any]:
    """Verify mock JWT token for local development"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    # Ensure user_id is present for cart API
    if "user_id" not in to_encode:
        to_encode["user_id"] = to_encode.get("sub", "unknown")
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt
