#!/usr/bin/env bash
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
# SPDX-License-Identifier: MIT
set -euo pipefail

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:-}"
CHAT_BACKEND_APP="${CHAT_API_APP_NAME:-}"
CHAT_FRONTEND_APP="${CHAT_WEB_APP_NAME:-}"
SCENARIO_BACKEND_APP="${SCENARIO_API_APP_NAME:-}"
SCENARIO_FRONTEND_APP="${SCENARIO_WEB_APP_NAME:-}"
CLIENT_ID="${AZURE_ENV_ENTRA_CLIENT_ID:-}"
APP_DISPLAY_NAME=""
SECRET_SETTING_NAME="MICROSOFT_PROVIDER_AUTHENTICATION_SECRET"

usage() {
    cat <<'EOF'
Usage: configure_auth.sh [options]
  --resource-group <name>
  --chat-backend-app <name>
  --chat-frontend-app <name>
  --scenario-backend-app <name>
  --scenario-frontend-app <name>
  --client-id <application-client-id>
  --app-display-name <name>
EOF
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --resource-group) RESOURCE_GROUP="$2"; shift 2 ;;
        --chat-backend-app) CHAT_BACKEND_APP="$2"; shift 2 ;;
        --chat-frontend-app) CHAT_FRONTEND_APP="$2"; shift 2 ;;
        --scenario-backend-app) SCENARIO_BACKEND_APP="$2"; shift 2 ;;
        --scenario-frontend-app) SCENARIO_FRONTEND_APP="$2"; shift 2 ;;
        --client-id) CLIENT_ID="$2"; shift 2 ;;
        --app-display-name) APP_DISPLAY_NAME="$2"; shift 2 ;;
        -h|--help) usage; exit 0 ;;
        *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
done

command -v az >/dev/null 2>&1 || { echo "Azure CLI ('az') is required." >&2; exit 1; }
command -v azd >/dev/null 2>&1 || { echo "Azure Developer CLI ('azd') is required." >&2; exit 1; }
az account show --only-show-errors >/dev/null

azd_get() {
    local value
    value="$(azd env get-value "$1" 2>/dev/null)" || return 0
    case "$value" in *ERROR:*|*"not found in environment"*) return 0 ;; esac
    printf '%s' "$value"
}

resolve_value() {
    local current="$1" key="$2"
    if [[ -n "$current" ]]; then printf '%s' "$current"; else azd_get "$key"; fi
}

RESOURCE_GROUP="$(resolve_value "$RESOURCE_GROUP" AZURE_RESOURCE_GROUP)"
CHAT_BACKEND_APP="$(resolve_value "$CHAT_BACKEND_APP" CHAT_API_APP_NAME)"
CHAT_FRONTEND_APP="$(resolve_value "$CHAT_FRONTEND_APP" CHAT_WEB_APP_NAME)"
SCENARIO_BACKEND_APP="$(resolve_value "$SCENARIO_BACKEND_APP" SCENARIO_API_APP_NAME)"
SCENARIO_FRONTEND_APP="$(resolve_value "$SCENARIO_FRONTEND_APP" SCENARIO_WEB_APP_NAME)"
CLIENT_ID="$(resolve_value "$CLIENT_ID" AZURE_ENV_ENTRA_CLIENT_ID)"

for entry in \
    "ResourceGroup:$RESOURCE_GROUP" \
    "ChatBackendAppName:$CHAT_BACKEND_APP" \
    "ChatFrontendAppName:$CHAT_FRONTEND_APP" \
    "ScenarioBackendAppName:$SCENARIO_BACKEND_APP" \
    "ScenarioFrontendAppName:$SCENARIO_FRONTEND_APP"; do
    [[ -n "${entry#*:}" ]] || { echo "Missing ${entry%%:*}." >&2; exit 1; }
done

TENANT_ID="$(az account show --query tenantId -o tsv)"
SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
ENVIRONMENT_NAME="$(azd_get AZURE_ENV_NAME)"
if [[ -z "$APP_DISPLAY_NAME" ]]; then
    APP_DISPLAY_NAME="${ENVIRONMENT_NAME:-$CHAT_FRONTEND_APP}-customer-chatbot-auth"
fi

CHAT_REDIRECT_URI="https://$CHAT_FRONTEND_APP.azurewebsites.net/.auth/login/aad/callback"
SCENARIO_REDIRECT_URI="https://$SCENARIO_FRONTEND_APP.azurewebsites.net/.auth/login/aad/callback"

if [[ -n "$CLIENT_ID" ]]; then
    APP_OBJECT_ID="$(az ad app show --id "$CLIENT_ID" --query id -o tsv)"
    echo "Reusing Microsoft Entra app registration $CLIENT_ID."
else
    echo "Creating Microsoft Entra app registration '$APP_DISPLAY_NAME'."
    CLIENT_ID="$(az ad app create --display-name "$APP_DISPLAY_NAME" --sign-in-audience AzureADMyOrg --enable-id-token-issuance true --web-redirect-uris "$CHAT_REDIRECT_URI" "$SCENARIO_REDIRECT_URI" --query appId -o tsv)"
    APP_OBJECT_ID="$(az ad app show --id "$CLIENT_ID" --query id -o tsv)"
fi

REDIRECT_URIS=()
while IFS= read -r uri; do
    [[ -n "$uri" ]] && REDIRECT_URIS+=("$uri")
done < <(az ad app show --id "$CLIENT_ID" --query 'web.redirectUris[]' -o tsv)
for required_uri in "$CHAT_REDIRECT_URI" "$SCENARIO_REDIRECT_URI"; do
    found=false
    for uri in "${REDIRECT_URIS[@]}"; do [[ "$uri" == "$required_uri" ]] && found=true; done
    $found || REDIRECT_URIS+=("$required_uri")
done
az ad app update --id "$CLIENT_ID" --enable-id-token-issuance true --web-redirect-uris "${REDIRECT_URIS[@]}" --output none

API_IDENTIFIER_URI="api://$CLIENT_ID"
IDENTIFIER_URIS=()
while IFS= read -r uri; do
    [[ -n "$uri" ]] && IDENTIFIER_URIS+=("$uri")
done < <(az ad app show --id "$CLIENT_ID" --query 'identifierUris[]' -o tsv)
if [[ ! " ${IDENTIFIER_URIS[*]} " =~ " ${API_IDENTIFIER_URI} " ]]; then
    IDENTIFIER_URIS+=("$API_IDENTIFIER_URI")
fi

az ad app update --id "$CLIENT_ID" --identifier-uris "${IDENTIFIER_URIS[@]}" --output none
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required to configure the API scope." >&2; exit 1; }
API_CURRENT_FILE="$(mktemp)"
API_BODY_FILE="$(mktemp)"
trap 'rm -f "$API_CURRENT_FILE" "$API_BODY_FILE"' EXIT
az rest --method get --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID?\$select=api" --output json > "$API_CURRENT_FILE"
python3 - "$API_CURRENT_FILE" "$API_BODY_FILE" <<'PY'
import json
import sys
import uuid

with open(sys.argv[1], encoding="utf-8") as source:
    api = json.load(source).get("api") or {}

scopes = api.get("oauth2PermissionScopes") or []
if not any(scope.get("value") == "user_impersonation" for scope in scopes):
    scopes.append(
        {
            "adminConsentDescription": "Access the customer chatbot API on behalf of the signed-in user.",
            "adminConsentDisplayName": "Access the customer chatbot API",
            "id": str(uuid.uuid4()),
            "isEnabled": True,
            "type": "User",
            "userConsentDescription": "Allow this application to access the customer chatbot API on your behalf.",
            "userConsentDisplayName": "Access the customer chatbot API",
            "value": "user_impersonation",
        }
    )

api["oauth2PermissionScopes"] = scopes
api["requestedAccessTokenVersion"] = 2
with open(sys.argv[2], "w", encoding="utf-8") as destination:
    json.dump({"api": api}, destination, separators=(",", ":"))
PY
az rest --method patch --uri "https://graph.microsoft.com/v1.0/applications/$APP_OBJECT_ID" --body "@$API_BODY_FILE" --output none
rm -f "$API_CURRENT_FILE" "$API_BODY_FILE"
trap - EXIT

get_frontend_secret() {
    local app_name="$1" auth_uri configured_client_id
    auth_uri="https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$app_name/config/authsettingsV2?api-version=2022-09-01"
    configured_client_id="$(az rest --method get --uri "$auth_uri" --query properties.identityProviders.azureActiveDirectory.registration.clientId -o tsv 2>/dev/null || true)"
    [[ "$configured_client_id" == "$CLIENT_ID" ]] || return 0
    az webapp config appsettings list --resource-group "$RESOURCE_GROUP" --name "$app_name" --query "[?name=='$SECRET_SETTING_NAME'].value | [0]" -o tsv 2>/dev/null || true
}

CLIENT_SECRET="$(get_frontend_secret "$CHAT_FRONTEND_APP")"
[[ -n "$CLIENT_SECRET" ]] || CLIENT_SECRET="$(get_frontend_secret "$SCENARIO_FRONTEND_APP")"
if [[ -z "$CLIENT_SECRET" ]]; then
    echo "Creating an App Service authentication credential."
    CLIENT_SECRET="$(az ad app credential reset --id "$CLIENT_ID" --append --display-name 'App Service Easy Auth' --years 2 --query password -o tsv)"
fi

configure_frontend() {
    local app_name="$1" auth_uri body_file
    echo "Configuring Easy Auth on '$app_name'."
    az webapp config appsettings set --resource-group "$RESOURCE_GROUP" --name "$app_name" --settings "$SECRET_SETTING_NAME=$CLIENT_SECRET" --output none
    auth_uri="https://management.azure.com/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Web/sites/$app_name/config/authsettingsV2?api-version=2022-09-01"
    body_file="$(mktemp)"
    trap 'rm -f "$body_file"' RETURN
    printf '%s' "{\"properties\":{\"platform\":{\"enabled\":true,\"runtimeVersion\":\"~1\"},\"globalValidation\":{\"requireAuthentication\":false,\"unauthenticatedClientAction\":\"AllowAnonymous\"},\"httpSettings\":{\"requireHttps\":true},\"identityProviders\":{\"azureActiveDirectory\":{\"enabled\":true,\"registration\":{\"clientId\":\"$CLIENT_ID\",\"clientSecretSettingName\":\"$SECRET_SETTING_NAME\",\"openIdIssuer\":\"https://login.microsoftonline.com/$TENANT_ID/v2.0\"},\"login\":{\"loginParameters\":[\"scope=openid profile email offline_access api://$CLIENT_ID/user_impersonation\"]},\"validation\":{\"allowedAudiences\":[\"$CLIENT_ID\"]}}},\"login\":{\"tokenStore\":{\"enabled\":true}}}}" > "$body_file"
    az rest --method put --uri "$auth_uri" --body "@$body_file" --output none
    rm -f "$body_file"
    trap - RETURN
}

configure_frontend "$CHAT_FRONTEND_APP"
configure_frontend "$SCENARIO_FRONTEND_APP"

for backend_app in "$CHAT_BACKEND_APP" "$SCENARIO_BACKEND_APP"; do
    echo "Configuring JWT validation on '$backend_app'."
    az webapp config appsettings set --resource-group "$RESOURCE_GROUP" --name "$backend_app" --settings "ENTRA_AUTH_CLIENT_ID=$CLIENT_ID" "ENTRA_AUTH_TENANT_ID=$TENANT_ID" --output none
done

azd env set AZURE_ENV_ENTRA_CLIENT_ID "$CLIENT_ID" >/dev/null
azd env set AZURE_ENV_ENTRA_APP_OBJECT_ID "$APP_OBJECT_ID" >/dev/null
echo "Authentication configured. Client ID: $CLIENT_ID"