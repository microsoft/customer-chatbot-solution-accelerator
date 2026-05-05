# Local Authentication Setup Guide

This guide will help you set up Microsoft Entra ID authentication for local development.

## Quick Start (Mock Authentication)

For immediate local development, the app uses mock authentication by default. No setup required!

## Real Entra ID Setup (Optional)

If you want to use real Microsoft Entra ID authentication:

### 1. Create Environment File

Create `.env.local` in the `modern-e-commerce-ch` directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_AZURE_CLIENT_ID=your-azure-client-id
VITE_AZURE_AUTHORITY=https://login.microsoftonline.com/your-tenant-id
```

### 2. Backend Environment

Update your backend `.env` file:

```env
# Azure Cosmos DB
COSMOS_DB_ENDPOINT=your-cosmos-endpoint
COSMOS_DB_KEY=your-cosmos-key
COSMOS_DB_DATABASE_NAME=ecommerce-db

# Microsoft Entra ID (optional for local dev)
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
```

### 3. Azure App Registration

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to "Azure Active Directory" > "App registrations"
3. Click "New registration"
4. Fill in:
   - Name: "E-commerce Chat Local Dev"
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: "Single-page application (SPA)" - `http://localhost:5173`
5. Click "Register"
6. Copy the "Application (client) ID" and "Directory (tenant) ID"
7. Go to "Authentication" and add redirect URI: `http://localhost:5173/auth/callback`
8. Go to "API permissions" and add "Microsoft Graph" > "User.Read"

## Running the Application

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd modern-e-commerce-ch
npm install
npm run dev
```

## Features

- **Mock Authentication**: Works out of the box for local development
- **Real Entra ID**: Optional integration with Microsoft Entra ID
- **Automatic Token Handling**: Tokens are automatically included in API requests
- **User Context**: User information available throughout the app
- **Login/Logout**: Simple login and logout functionality

## Troubleshooting

### Mock Authentication Not Working
- Check that the backend is running on `http://localhost:8000`
- Check browser console for errors
- Try refreshing the page

### Real Entra ID Not Working
- Verify environment variables are set correctly
- Check that the app registration is configured properly
- Ensure redirect URIs match exactly
- Check browser console for detailed error messages
