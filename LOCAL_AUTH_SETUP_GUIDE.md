# Local Authentication Setup Guide

## Quick Start (Mock Authentication)

The application is now configured to work with both mock authentication (for local development) and Microsoft Entra ID authentication (for production).

### For Immediate Testing (Mock Auth)

1. **Start the Backend**:
   ```bash
   cd src/api
   pip install -r requirements.txt
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**:
   ```bash
   cd src/App
   npm install --legacy-peer-deps
   npm run dev
   ```

3. **Test the Application**:
   - Open http://localhost:5173
   - Click "Login" button
   - The app will use mock authentication automatically
   - You should be logged in as "Local Developer"

### For Entra ID Testing (Optional)

If you want to test with real Microsoft Entra ID authentication:

1. **Create Azure App Registration**:
   ```bash
   # Using Azure CLI
   az ad app create \
     --display-name "E-commerce Chat Local Dev" \
     --sign-in-audience "AzureADMyOrg" \
     --web-redirect-uris "http://localhost:5173" "http://localhost:5173/auth/callback"
   ```

2. **Configure App Registration**:
   - Go to Azure Portal > Azure Active Directory > App registrations
   - Find your app and go to "Authentication"
   - Add redirect URI: `http://localhost:5173/auth/callback`
   - Go to "API permissions" and add "Microsoft Graph" > "User.Read"

3. **Create Environment Files**:
   
   **Frontend** (`modern-e-commerce-ch/.env.local`):
   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_AZURE_CLIENT_ID=your-actual-client-id
   VITE_AZURE_TENANT_ID=your-actual-tenant-id
   VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/your-actual-tenant-id
   VITE_REDIRECT_URI=http://localhost:5173/auth/callback
   VITE_ENVIRONMENT=development
   ```

   **Backend** (`backend/.env.local`):
   ```env
   COSMOS_DB_ENDPOINT=your-cosmos-endpoint
   COSMOS_DB_KEY=your-cosmos-key
   COSMOS_DB_DATABASE_NAME=ecommerce_db
   AZURE_TENANT_ID=your-actual-tenant-id
   AZURE_CLIENT_ID=your-actual-client-id
   AZURE_CLIENT_SECRET=your-actual-client-secret
   JWT_SECRET_KEY=your-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
   ```

4. **Test Entra ID Authentication**:
   - Restart both frontend and backend
   - The app will now use Microsoft Entra ID for authentication
   - Click "Login" to be redirected to Microsoft login

## How It Works

### Environment Detection

The application automatically detects which authentication method to use:

- **Mock Authentication**: When `VITE_AZURE_CLIENT_ID` is not set or equals placeholder values
- **Entra ID Authentication**: When `VITE_AZURE_CLIENT_ID` contains a real Azure client ID

### Authentication Flow

1. **Mock Flow**:
   - User clicks "Login"
   - Frontend calls backend `/api/auth/mock-login`
   - Backend returns JWT token
   - Frontend stores token and shows user as logged in

2. **Entra ID Flow**:
   - User clicks "Login"
   - Frontend redirects to Microsoft login
   - User authenticates with Microsoft
   - Microsoft redirects back with authorization code
   - Frontend exchanges code for access token
   - Frontend sends token to backend for validation
   - Backend validates token with Microsoft
   - User is logged in

## Testing Checklist

- [ ] Mock authentication works (no Azure setup needed)
- [ ] Login/logout functionality works
- [ ] API calls work with authentication
- [ ] Chat functionality works with authenticated user
- [ ] Cart persistence works across sessions
- [ ] Entra ID authentication works (if configured)

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure backend has correct CORS settings
2. **Token Validation**: Check that backend can validate tokens
3. **Redirect URI Mismatch**: Ensure redirect URIs match exactly in Azure
4. **Environment Variables**: Verify all required variables are set

### Debug Commands

```bash
# Check backend health
curl http://localhost:8000/health

# Check auth config
curl http://localhost:8000/api/auth/config

# Test mock login
curl -X POST http://localhost:8000/api/auth/mock-login
```

## Next Steps

Once local testing is complete, you can proceed with the production deployment using the updated deployment scripts in the `ENTRA_ID_AUTHENTICATION_PLAN.md`.
