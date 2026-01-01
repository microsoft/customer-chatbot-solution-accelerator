import base64
import json
import logging

logger = logging.getLogger(__name__)


def get_sample_user():
    return {
        "user_principal_id": "guest-user-00000000",
        "user_name": "Guest User",
        "auth_provider": None,
        "auth_token": None,
        "aad_id_token": None,
        "client_principal_b64": None,
        "is_guest": True,
    }


def get_authenticated_user_details(request_headers):
    user_object = {}

    normalized_headers = {k.lower(): v for k, v in request_headers.items()}

    # Enhanced debugging: Log all headers to see what we're getting
    logger.info(
        f"🔍 AUTH_UTILS: All request headers received: {list(request_headers.keys())}"
    )
    logger.info(
        f"🔍 AUTH_UTILS: Looking for Easy Auth headers: {[k for k in normalized_headers.keys() if 'x-ms-client' in k]}"
    )

    # Log the actual Easy Auth header values if they exist
    easy_auth_headers = {
        k: v for k, v in request_headers.items() if "x-ms-client" in k.lower()
    }
    if easy_auth_headers:
        logger.info("🔍 AUTH_UTILS: Easy Auth headers found with values:")
        for key, value in easy_auth_headers.items():
            logger.info(f"  {key}: {value}")
    else:
        logger.info("🔍 AUTH_UTILS: NO Easy Auth headers found!")

    # Check for Easy Auth headers (either direct or forwarded)
    if "x-ms-client-principal-id" not in normalized_headers:
        logger.info("No Easy Auth headers found, using sample guest user")
        raw_user_object = get_sample_user()
        user_object["is_guest"] = True
        # For guest users, use the guest user data directly
        user_object["user_principal_id"] = raw_user_object["user_principal_id"]
        user_object["user_name"] = raw_user_object["user_name"]
        user_object["auth_provider"] = raw_user_object["auth_provider"]
        user_object["auth_token"] = raw_user_object["auth_token"]
        user_object["client_principal_b64"] = raw_user_object["client_principal_b64"]
        user_object["aad_id_token"] = raw_user_object["aad_id_token"]
    else:
        logger.info("Easy Auth headers found, extracting user details")
        raw_user_object = {k: v for k, v in request_headers.items()}
        user_object["is_guest"] = False
        logger.info(
            f"Easy Auth user ID: {raw_user_object.get('x-ms-client-principal-id')}"
        )
        logger.info(
            f"Easy Auth user name: {raw_user_object.get('x-ms-client-principal-name')}"
        )
        # For authenticated users, extract from Easy Auth headers
        user_object["user_principal_id"] = raw_user_object.get(
            "x-ms-client-principal-id"
        )
        user_object["user_name"] = raw_user_object.get("x-ms-client-principal-name")
        user_object["auth_provider"] = raw_user_object.get("x-ms-client-principal-idp")
        user_object["auth_token"] = raw_user_object.get("x-ms-token-aad-id-token")
        user_object["client_principal_b64"] = raw_user_object.get(
            "x-ms-client-principal"
        )
        user_object["aad_id_token"] = raw_user_object.get("x-ms-token-aad-id-token")

    return user_object


def get_tenantid(client_principal_b64):
    tenant_id = ""
    if client_principal_b64:
        try:
            decoded_bytes = base64.b64decode(client_principal_b64)
            decoded_string = decoded_bytes.decode("utf-8")
            user_info = json.loads(decoded_string)
            tenant_id = user_info.get("tid")
        except Exception as ex:
            logger.exception(f"Error decoding tenant ID: {ex}")
    return tenant_id


def get_user_email(client_principal_b64):
    """Extract user email from the x-ms-client-principal token"""
    email = ""
    if client_principal_b64:
        try:
            decoded_bytes = base64.b64decode(client_principal_b64)
            decoded_string = decoded_bytes.decode("utf-8")
            user_info = json.loads(decoded_string)
            # Try different possible email fields in the token
            email = (
                user_info.get("email")
                or user_info.get("upn")  # User Principal Name
                or user_info.get("preferred_username")
                or user_info.get("unique_name")
                or ""
            )
            logger.info(f"🔍 AUTH_UTILS: Extracted email from token: {email}")
            logger.info(
                f"🔍 AUTH_UTILS: Available claims in token: {list(user_info.keys())}"
            )
        except Exception as ex:
            logger.exception(f"Error decoding email from client principal: {ex}")
    return email
