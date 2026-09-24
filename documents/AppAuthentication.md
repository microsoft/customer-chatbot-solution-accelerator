---
title: Set up Microsoft Entra authentication
description: Automate frontend App Service authentication and backend JWT validation
ms.date: 2026-09-23
ms.topic: how-to
---

The frontend uses Azure App Service authentication to sign users in. The frontend
sends the resulting signed Microsoft Entra token to the backend as an
`Authorization: Bearer` credential. The Python backend validates the token signature,
issuer, audience, tenant, and expiration before using any identity claims.

> [!IMPORTANT]
> Do not enable backend App Service authentication for this configuration. Do not
> send `X-MS-CLIENT-PRINCIPAL-*` headers from clients. The backend ignores those
> headers because callers can forge them.

## Prerequisites

* Access to Microsoft Entra ID
* Permission to create or manage app registrations
* Permission to update the deployed App Services
* Azure CLI and Azure Developer CLI (`azd`)

## Manual post-deployment configuration

After `azd up` creates the App Services, run the platform-specific authentication
configuration script from the repository root:

```powershell
./infra/scripts/post-provision/configure_auth.ps1
```

```bash
bash ./infra/scripts/post-provision/configure_auth.sh
```

The script:

* Creates a single-tenant Microsoft Entra app registration or reuses the client
  ID stored in `AZURE_ENV_ENTRA_CLIENT_ID`
* Adds callback URLs for both frontend App Services without removing existing
  redirect URLs
* Creates a client credential when the frontends do not already have one
* Enables Easy Auth and the token store on both frontends
* Sets `ENTRA_AUTH_CLIENT_ID` and `ENTRA_AUTH_TENANT_ID` on both backends
* Stores the application client ID and object ID in the current `azd` environment

The frontends allow anonymous requests so guest mode remains available. Users can
select **Sign in** to start the Easy Auth Microsoft Entra flow. The Python
backends authenticate signed-in requests by validating the forwarded ID token.

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

* `ENTRA_AUTH_CLIENT_ID` to the application client ID
* `ENTRA_AUTH_TENANT_ID` to the deployment subscription tenant ID

For local development, set the same values in each backend `.env` file. A client
secret is not required because the backend validates tokens and does not acquire
tokens as the application.

Tokenless requests continue as guest requests. Requests with malformed, expired,
wrong-tenant, wrong-audience, or invalid-signature bearer tokens receive `401
Unauthorized`.

## Verify the configuration

1. Sign in through a frontend App Service.
2. Confirm that `/.auth/me` returns an `id_token`.
3. Call `/api/auth/me` through the frontend and confirm that it returns
   `is_authenticated: true`.
4. Call the backend with forged `X-MS-CLIENT-PRINCIPAL-ID` and
   `X-MS-CLIENT-PRINCIPAL-NAME` headers but without a bearer token.
5. Confirm that the backend returns the guest identity rather than the forged user.
6. Alter one character in a bearer token and confirm that the backend returns `401`.
