---
title: Set up Microsoft Entra authentication
description: Configure Microsoft Entra sign-in and API authorization after deployment
---

## Overview

This document provides instructions to configure authentication for the application.

The frontend uses Azure App Service authentication to sign users in and request a
delegated access token for the application API. The frontend sends that access
token to the backend as an `Authorization: Bearer` credential. The Python backend
validates the token signature, issuer, API audience, tenant, expiration, and
`user_impersonation` scope before using any identity claims.

## Prerequisites

* Access to Microsoft Entra ID
* Permission to create or manage app registrations
* Permission to update the deployed App Services
* Azure CLI and Azure Developer CLI (`azd`)

## Manual post-deployment configuration

After `azd up` creates the App Services, run the platform-specific authentication
configuration script from the repository root:

- **For PowerShell (Windows/Linux/macOS):**
```powershell
./infra/scripts/post-provision/configure_auth.ps1
```

- **For Bash (Linux/macOS/WSL):**
```bash
bash ./infra/scripts/post-provision/configure_auth.sh
```

The script:

* Creates a single-tenant Microsoft Entra app registration or reuses the client
  ID stored in `AZURE_ENV_ENTRA_CLIENT_ID`
* Adds callback URLs for both frontend App Services without removing existing
  redirect URLs
* Exposes the `api://<client-id>/user_impersonation` delegated API scope
* Creates a client credential when the frontends do not already have one
* Enables Easy Auth and requests the API scope on both frontends
* Sets `ENTRA_AUTH_CLIENT_ID` and `ENTRA_AUTH_TENANT_ID` on both backends
* Stores the application client ID and object ID in the current `azd` environment

The frontends allow anonymous requests at the App Service layer so deployments
without authentication can continue in guest mode. When Easy Auth is configured,
each frontend detects the identity provider and redirects unauthenticated users
to Microsoft Entra sign-in before loading application data. After sign-in, users
return to the application route they originally requested. The Python backends
authenticate signed-in requests by validating the forwarded API access token.

> [!IMPORTANT]
> The signed-in Azure CLI identity must be allowed to create app registrations in
> the tenant. If tenant policy blocks application creation, ask an administrator
> to create the registration, then set its client ID before running the script:

```powershell
azd env set AZURE_ENV_ENTRA_CLIENT_ID <application-client-id>
```

The deployment identity must be an owner of, or otherwise have permission to
update, an existing registration.

## Rerun the configuration

Both scripts accept explicit resource group, App Service, client ID, and display
name arguments. With no arguments, they read deployment outputs from the current
`azd` environment. Reruns reuse the persisted app registration and existing
credential when possible.

## Configure backend token validation

The post-deploy script sets these backend application settings:

* `ENTRA_AUTH_CLIENT_ID` to the API application client ID used as the token audience
* `ENTRA_AUTH_TENANT_ID` to the deployment subscription tenant ID

For local development, set the same values in each backend `.env` file. A client
secret is not required because the backend validates tokens and does not acquire
tokens as the application.

Tokenless requests continue as guest requests. Requests with malformed, expired,
wrong-tenant, wrong-audience, missing-scope, or invalid-signature bearer tokens
receive `401 Unauthorized`.

## Verify the configuration

1. Open a frontend App Service and confirm that it redirects to Microsoft Entra.
2. Complete sign-in and confirm that the browser returns directly to the
  application.
3. Confirm that `/.auth/me` returns an `access_token` for the application API.
4. Call `/api/auth/me` through the frontend and confirm that it returns
   `is_authenticated: true`.
