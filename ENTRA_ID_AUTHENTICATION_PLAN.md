# Microsoft Entra ID Authentication Implementation Plan

## Overview

This document provides a comprehensive plan to implement Microsoft Entra ID authentication for your e-commerce chat application, covering both local development and end-to-end Azure deployment scenarios.

## Current State Analysis

### Frontend (React + Vite)
- **Framework**: React 19 with TypeScript, Vite 6.3.5
- **UI Library**: Fluent UI React components + Radix UI
- **Current Auth**: Mock authentication system with JWT tokens
- **MSAL Libraries**: Already installed (`@azure/msal-browser`, `@azure/msal-react`)
- **Environment**: Supports both Vite env vars and runtime configuration

### Backend (FastAPI + Python)
- **Framework**: FastAPI with Python 3.11
- **Current Auth**: Mock JWT authentication with fallback to Entra ID validation
- **Database**: Azure Cosmos DB integration
- **Deployment**: Azure App Service with Bicep templates

### Current Authentication Flow
1. **Local Development**: Mock authentication with JWT tokens
2. **Production**: Entra ID token validation (partially implemented)
3. **Frontend**: Detects environment and uses appropriate auth method

## Implementation Plan

## Phase 1: Local Development Setup

### 1.1 Azure App Registration Setup

#### Create App Registration
```bash
# Using Azure CLI
az ad app create \
  --display-name "E-commerce Chat Local Dev" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "http://localhost:5173" "http://localhost:5173/auth/callback"
```

#### Configure App Registration
1. **Authentication**:
   - Platform: Single-page application (SPA)
   - Redirect URIs: 
     - `http://localhost:5173`
     - `http://localhost:5173/auth/callback`
   - Logout URL: `http://localhost:5173`
   - Implicit grant: Access tokens, ID tokens

2. **API Permissions**:
   - Microsoft Graph: `User.Read`
   - Microsoft Graph: `openid`
   - Microsoft Graph: `profile`

3. **Certificates & Secrets**:
   - Create client secret for backend validation
   - Note: For production, use certificates instead of secrets

### 1.2 Frontend Configuration

#### Update Environment Variables
Create `modern-e-commerce-ch/.env.local`:
```env
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Azure Entra ID Configuration
VITE_AZURE_CLIENT_ID=your-client-id-here
VITE_AZURE_TENANT_ID=your-tenant-id-here
VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/your-tenant-id-here
VITE_REDIRECT_URI=http://localhost:5173/auth/callback

# Environment Detection
VITE_ENVIRONMENT=development
```

#### Implement MSAL Configuration
Create `modern-e-commerce-ch/src/lib/msalConfig.ts`:
```typescript
import { Configuration, LogLevel } from '@azure/msal-browser';

export const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_AZURE_CLIENT_ID!,
    authority: import.meta.env.VITE_AZURE_AUTHORITY!,
    redirectUri: import.meta.env.VITE_REDIRECT_URI!,
    postLogoutRedirectUri: import.meta.env.VITE_REDIRECT_URI!,
  },
  cache: {
    cacheLocation: 'sessionStorage',
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            break;
          case LogLevel.Info:
            console.info(message);
            break;
          case LogLevel.Verbose:
            console.debug(message);
            break;
          case LogLevel.Warning:
            console.warn(message);
            break;
        }
      },
    },
  },
};

export const loginRequest = {
  scopes: ['User.Read'],
};

export const tokenRequest = {
  scopes: ['User.Read'],
  forceRefresh: false,
};
```

#### Update AuthContext for MSAL Integration
Modify `modern-e-commerce-ch/src/contexts/AuthContext.tsx`:
```typescript
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useMsal, useIsAuthenticated } from '@azure/msal-react';
import { api } from '@/lib/api';
import { msalConfig, loginRequest, tokenRequest } from '@/lib/msalConfig';

// ... existing interfaces ...

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <MsalProvider instance={msalInstance}>
      <AuthContextProvider>{children}</AuthContextProvider>
    </MsalProvider>
  );
}

function AuthContextProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const { instance, accounts } = useMsal();
  const isAuthenticated = useIsAuthenticated();

  // Check if we're in local development mode
  const isLocalDev = !import.meta.env.VITE_AZURE_CLIENT_ID || 
                     import.meta.env.VITE_AZURE_CLIENT_ID === 'local-dev';

  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (isLocalDev) {
          // Local development mode - use mock authentication
          const token = localStorage.getItem('mock_token');
          if (token) {
            try {
              const response = await api.get('/api/auth/me', {
                headers: { Authorization: `Bearer ${token}` }
              });
              setUser(response.data);
            } catch (error) {
              console.error('Failed to validate mock token:', error);
              localStorage.removeItem('mock_token');
            }
          }
        } else if (isAuthenticated && accounts.length > 0) {
          // Entra ID authentication
          try {
            const response = await instance.acquireTokenSilent({
              ...tokenRequest,
              account: accounts[0],
            });
            
            // Send token to backend for validation
            const userResponse = await api.get('/api/auth/me', {
              headers: { Authorization: `Bearer ${response.accessToken}` }
            });
            setUser(userResponse.data);
          } catch (error) {
            console.error('Failed to acquire token:', error);
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, [isAuthenticated, accounts, instance, isLocalDev]);

  const login = async (email?: string, password?: string) => {
    try {
      if (isLocalDev) {
        // Mock login for local development
        if (email && password) {
          const response = await api.post('/api/auth/email-login', {
            email,
            password
          });
          const { access_token, user: userData } = response.data;
          localStorage.setItem('mock_token', access_token);
          setUser(userData);
        } else {
          const response = await api.post('/api/auth/mock-login', {
            username: 'dev@localhost.com',
            name: 'Local Developer'
          });
          const { access_token, user: userData } = response.data;
          localStorage.setItem('mock_token', access_token);
          setUser(userData);
        }
      } else {
        // Entra ID login
        await instance.loginPopup(loginRequest);
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const logout = async () => {
    try {
      if (isLocalDev) {
        localStorage.removeItem('mock_token');
        setUser(null);
      } else {
        await instance.logoutPopup({
          postLogoutRedirectUri: msalConfig.auth.redirectUri,
        });
        setUser(null);
      }
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // ... rest of the component
}
```

#### Update Main App Entry Point
Modify `modern-e-commerce-ch/src/main.tsx`:
```typescript
import React from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { FluentProvider, webLightTheme } from '@fluentui/react-components';
import { AuthProvider } from '@/contexts/AuthContext';
import App from './App.tsx';
import ErrorFallback from './ErrorFallback.tsx';
import './index.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 5 * 60 * 1000,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <FluentProvider theme={webLightTheme}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </FluentProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>,
);
```

### 1.3 Backend Configuration

#### Update Environment Variables
Create `backend/.env.local`:
```env
# Azure Cosmos DB
COSMOS_DB_ENDPOINT=your-cosmos-endpoint
COSMOS_DB_KEY=your-cosmos-key
COSMOS_DB_DATABASE_NAME=ecommerce_db

# Microsoft Entra ID
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

#### Update Auth Router
Modify `backend/app/routers/auth.py` to support Entra ID:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..auth import get_current_user, create_access_token, auth_handler
from ..models.user import UserResponse, UserUpdate
from ..services.cosmos_service import get_db_service
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["authentication"])

@router.get("/me")
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user information"""
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
    
    token = create_access_token(user_data)
    
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

# ... rest of existing endpoints
```

## Phase 2: Production Deployment Setup

### 2.1 Azure App Registration for Production

#### Create Production App Registration
```bash
# Using Azure CLI
az ad app create \
  --display-name "E-commerce Chat Production" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "https://your-frontend-app.azurewebsites.net" "https://your-frontend-app.azurewebsites.net/auth/callback"
```

#### Configure Production App Registration
1. **Authentication**:
   - Platform: Single-page application (SPA)
   - Redirect URIs: 
     - `https://your-frontend-app.azurewebsites.net`
     - `https://your-frontend-app.azurewebsites.net/auth/callback`
   - Logout URL: `https://your-frontend-app.azurewebsites.net`

2. **API Permissions**:
   - Microsoft Graph: `User.Read`
   - Microsoft Graph: `openid`
   - Microsoft Graph: `profile`

3. **Certificates & Secrets**:
   - Create client secret for backend validation
   - For production, consider using certificates for better security

### 2.2 Update Deployment Scripts

#### Modify Frontend Deployment Script
Update `infrastructure/deploy-phase2-frontend.ps1`:
```powershell
# Add Entra ID configuration to app settings
az webapp config appsettings set `
    --name $frontendAppServiceName `
    --resource-group $ResourceGroupName `
    --settings `
    VITE_API_BASE_URL="https://$backendAppServiceName.azurewebsites.net" `
    VITE_AZURE_CLIENT_ID="$env:AZURE_CLIENT_ID" `
    VITE_AZURE_TENANT_ID="$env:AZURE_TENANT_ID" `
    VITE_AZURE_AUTHORITY="https://login.microsoftonline.com/$env:AZURE_TENANT_ID" `
    VITE_REDIRECT_URI="https://$frontendAppServiceName.azurewebsites.net/auth/callback" `
    VITE_ENVIRONMENT="production" `
    --only-show-errors
```

#### Modify Backend Deployment Script
Update `infrastructure/deploy-phase3-backend.ps1`:
```powershell
# Add Entra ID configuration to app settings
az webapp config appsettings set `
    --name $backendAppServiceName `
    --resource-group $ResourceGroupName `
    --settings `
    AZURE_TENANT_ID="$env:AZURE_TENANT_ID" `
    AZURE_CLIENT_ID="$env:AZURE_CLIENT_ID" `
    AZURE_CLIENT_SECRET="$env:AZURE_CLIENT_SECRET" `
    --only-show-errors
```

#### Update Bicep Templates
Modify `infrastructure/backend-app-service.bicep`:
```bicep
// Add Entra ID configuration
{
  name: 'AZURE_TENANT_ID'
  value: azureTenantId
}
{
  name: 'AZURE_CLIENT_ID'
  value: azureClientId
}
{
  name: 'AZURE_CLIENT_SECRET'
  value: azureClientSecret
}
```

Modify `infrastructure/frontend-app-service.bicep`:
```bicep
// Add Entra ID configuration
{
  name: 'VITE_AZURE_CLIENT_ID'
  value: azureClientId
}
{
  name: 'VITE_AZURE_TENANT_ID'
  value: azureTenantId
}
{
  name: 'VITE_AZURE_AUTHORITY'
  value: 'https://login.microsoftonline.com/${azureTenantId}'
}
{
  name: 'VITE_REDIRECT_URI'
  value: 'https://${frontendAppServiceName}.azurewebsites.net/auth/callback'
}
```

### 2.3 Environment Variables for Deployment

#### Create Environment Configuration Script
Create `infrastructure/setup-entra-id.ps1`:
```powershell
param(
    [string]$ResourceGroupName = "ecommerce-chat-rg",
    [string]$Environment = "dev",
    [string]$AppNamePrefix = "ecommerce-chat",
    [string]$AzureTenantId,
    [string]$AzureClientId,
    [string]$AzureClientSecret
)

Write-Host "🔐 Setting up Entra ID Authentication" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Set environment variables for deployment scripts
$env:AZURE_TENANT_ID = $AzureTenantId
$env:AZURE_CLIENT_ID = $AzureClientId
$env:AZURE_CLIENT_SECRET = $AzureClientSecret

Write-Host "✅ Environment variables set for deployment" -ForegroundColor Green
Write-Host "Tenant ID: $AzureTenantId" -ForegroundColor Cyan
Write-Host "Client ID: $AzureClientId" -ForegroundColor Cyan
Write-Host "Client Secret: [HIDDEN]" -ForegroundColor Cyan

Write-Host "`n📋 Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run Phase 2: Frontend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase2-frontend.ps1" -ForegroundColor Cyan
Write-Host "2. Run Phase 3: Backend Deployment" -ForegroundColor White
Write-Host "   .\deploy-phase3-backend.ps1" -ForegroundColor Cyan
```

## Phase 3: Testing and Validation

### 3.1 Local Testing

#### Test Mock Authentication
1. Start backend: `cd backend && python -m uvicorn app.main:app --reload`
2. Start frontend: `cd modern-e-commerce-ch && npm run dev`
3. Test login/logout functionality
4. Verify API calls work with authentication

#### Test Entra ID Authentication
1. Set up `.env.local` with real Entra ID credentials
2. Test login flow with Microsoft
3. Verify token validation
4. Test API calls with Entra ID tokens

### 3.2 Production Testing

#### Deploy with Entra ID
1. Run `.\setup-entra-id.ps1` with production credentials
2. Deploy frontend: `.\deploy-phase2-frontend.ps1`
3. Deploy backend: `.\deploy-phase3-backend.ps1`
4. Test authentication flow in production

#### Integration Testing
1. Test login/logout flow
2. Verify API calls work with authentication
3. Test chat functionality with authenticated users
4. Verify cart persistence across sessions

## Phase 4: Security Hardening

### 4.1 Security Best Practices

#### Use Certificates Instead of Secrets
```bash
# Generate certificate for production
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Upload certificate to Azure App Registration
az ad app credential reset --id $CLIENT_ID --cert @cert.pem
```

#### Implement Token Refresh
```typescript
// In AuthContext
const refreshToken = async () => {
  try {
    const response = await instance.acquireTokenSilent({
      ...tokenRequest,
      account: accounts[0],
    });
    return response.accessToken;
  } catch (error) {
    // Handle token refresh failure
    await logout();
    throw error;
  }
};
```

#### Add Rate Limiting
```python
# In backend
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # ... login logic
```

### 4.2 Monitoring and Logging

#### Add Authentication Logging
```python
# In backend
import logging

logger = logging.getLogger(__name__)

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt for user: {form_data.username}")
    # ... login logic
```

#### Add Frontend Error Handling
```typescript
// In AuthContext
const handleAuthError = (error: any) => {
  console.error('Authentication error:', error);
  // Log to monitoring service
  // Show user-friendly error message
};
```

## Implementation Checklist

### Local Development
- [ ] Create Azure App Registration for local development
- [ ] Set up environment variables (`.env.local`)
- [ ] Implement MSAL configuration
- [ ] Update AuthContext for MSAL integration
- [ ] Test mock authentication
- [ ] Test Entra ID authentication
- [ ] Verify API integration

### Production Deployment
- [ ] Create production Azure App Registration
- [ ] Update deployment scripts with Entra ID configuration
- [ ] Update Bicep templates
- [ ] Deploy frontend with Entra ID settings
- [ ] Deploy backend with Entra ID settings
- [ ] Test production authentication flow
- [ ] Verify all functionality works

### Security & Monitoring
- [ ] Implement certificate-based authentication
- [ ] Add token refresh logic
- [ ] Implement rate limiting
- [ ] Add authentication logging
- [ ] Set up monitoring and alerting
- [ ] Test security measures

## Troubleshooting Guide

### Common Issues

#### 1. CORS Errors
**Problem**: Frontend can't call backend API
**Solution**: Ensure CORS is properly configured in backend with frontend URL

#### 2. Token Validation Failures
**Problem**: Backend rejects Entra ID tokens
**Solution**: Verify tenant ID, client ID, and token audience match

#### 3. Redirect URI Mismatch
**Problem**: Microsoft login fails with redirect URI error
**Solution**: Ensure redirect URIs in App Registration match exactly

#### 4. Environment Variable Issues
**Problem**: Frontend can't find Azure configuration
**Solution**: Verify environment variables are set correctly in deployment

### Debug Commands

```bash
# Check Azure App Registration
az ad app show --id $CLIENT_ID

# Check App Service configuration
az webapp config appsettings list --name $APP_NAME --resource-group $RG_NAME

# Test backend health
curl https://your-backend.azurewebsites.net/health

# Test authentication endpoint
curl https://your-backend.azurewebsites.net/api/auth/config
```

## Conclusion

This plan provides a comprehensive approach to implementing Microsoft Entra ID authentication for your e-commerce chat application. The implementation supports both local development with mock authentication and production deployment with full Entra ID integration.

The key benefits of this approach:
- **Seamless Development**: Mock authentication for local development
- **Production Ready**: Full Entra ID integration for production
- **Security**: Industry-standard authentication with Microsoft
- **Scalability**: Supports enterprise scenarios with proper user management
- **Maintainability**: Clear separation between mock and production auth flows

Follow the phases sequentially, and ensure each phase is tested thoroughly before proceeding to the next one.
