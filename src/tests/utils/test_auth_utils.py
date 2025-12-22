import base64
import json

from app.utils.auth_utils import (get_authenticated_user_details,
                                  get_sample_user, get_tenantid,
                                  get_user_email)


def test_get_sample_user():
    """Test that sample user returns correct guest user structure."""
    user = get_sample_user()

    assert user["user_principal_id"] == "guest-user-00000000"
    assert user["user_name"] == "Guest User"
    assert user["auth_provider"] is None
    assert user["auth_token"] is None
    assert user["aad_id_token"] is None
    assert user["client_principal_b64"] is None
    assert user["is_guest"] is True


def test_get_authenticated_user_details_no_easy_auth_headers():
    """Test user details extraction when no Easy Auth headers present."""
    headers = {"content-type": "application/json", "user-agent": "test-agent"}

    user = get_authenticated_user_details(headers)

    assert user["is_guest"] is True
    assert user["user_principal_id"] == "guest-user-00000000"
    assert user["user_name"] == "Guest User"
    assert user["auth_provider"] is None
    assert user["auth_token"] is None


def test_get_authenticated_user_details_with_easy_auth_headers():
    """Test user details extraction with Easy Auth headers."""
    headers = {
        "x-ms-client-principal-id": "user-12345",
        "x-ms-client-principal-name": "john.doe@example.com",
        "x-ms-client-principal-idp": "aad",
        "x-ms-token-aad-id-token": "token-abc123",
        "x-ms-client-principal": "base64encodeddata",
    }

    user = get_authenticated_user_details(headers)

    assert user["is_guest"] is False
    assert user["user_principal_id"] == "user-12345"
    assert user["user_name"] == "john.doe@example.com"
    assert user["auth_provider"] == "aad"
    assert user["auth_token"] == "token-abc123"
    assert user["client_principal_b64"] == "base64encodeddata"
    assert user["aad_id_token"] == "token-abc123"


def test_get_authenticated_user_details_case_insensitive_headers():
    """Test that header detection is case-insensitive but value extraction uses original keys."""
    headers = {
        "X-MS-CLIENT-PRINCIPAL-ID": "user-67890",
        "X-Ms-Client-Principal-Name": "jane.doe@example.com",
        "X-MS-CLIENT-PRINCIPAL-IDP": "aad",
    }

    user = get_authenticated_user_details(headers)

    # Detection is case-insensitive, but extraction uses raw headers
    assert user["is_guest"] is False
    # Since the function uses .get() with exact keys, these may be None
    assert user["user_principal_id"] is None  # Key doesn't match exactly
    assert user["user_name"] is None  # Key doesn't match exactly


def test_get_authenticated_user_details_partial_headers():
    """Test user details with only some Easy Auth headers."""
    headers = {
        "x-ms-client-principal-id": "user-partial",
        "x-ms-client-principal-name": "partial@example.com",
        # Missing other headers
    }

    user = get_authenticated_user_details(headers)

    assert user["is_guest"] is False
    assert user["user_principal_id"] == "user-partial"
    assert user["user_name"] == "partial@example.com"
    assert user["auth_provider"] is None
    assert user["auth_token"] is None


def test_get_tenantid_valid_base64():
    """Test tenant ID extraction from valid base64 encoded client principal."""
    user_info = {"tid": "tenant-123-abc"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    tenant_id = get_tenantid(encoded)

    assert tenant_id == "tenant-123-abc"


def test_get_tenantid_no_tid_field():
    """Test tenant ID extraction when tid field is missing."""
    user_info = {"sub": "user-123", "name": "Test User"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    tenant_id = get_tenantid(encoded)

    assert tenant_id is None


def test_get_tenantid_invalid_base64():
    """Test tenant ID extraction with invalid base64 string."""
    invalid_base64 = "not-valid-base64!@#$"

    tenant_id = get_tenantid(invalid_base64)

    assert tenant_id == ""


def test_get_user_email_with_email_field():
    """Test email extraction when email field is present."""
    user_info = {"email": "user@example.com", "tid": "tenant-123"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "user@example.com"


def test_get_user_email_with_upn_field():
    """Test email extraction when upn (User Principal Name) is used."""
    user_info = {"upn": "user.upn@example.com", "tid": "tenant-123"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "user.upn@example.com"


def test_get_user_email_with_preferred_username():
    """Test email extraction when preferred_username is used."""
    user_info = {"preferred_username": "preferred@example.com"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "preferred@example.com"


def test_get_user_email_with_unique_name():
    """Test email extraction when unique_name is used."""
    user_info = {"unique_name": "unique@example.com"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "unique@example.com"


def test_get_user_email_priority_order():
    """Test that email field takes priority over other fields."""
    user_info = {
        "email": "email@example.com",
        "upn": "upn@example.com",
        "preferred_username": "preferred@example.com",
        "unique_name": "unique@example.com",
    }
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "email@example.com"


def test_get_user_email_upn_priority_over_preferred():
    """Test that upn takes priority over preferred_username when email is missing."""
    user_info = {
        "upn": "upn@example.com",
        "preferred_username": "preferred@example.com",
        "unique_name": "unique@example.com",
    }
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == "upn@example.com"


def test_get_user_email_no_email_fields():
    """Test email extraction when no email fields are present."""
    user_info = {"tid": "tenant-123", "sub": "user-id"}
    json_string = json.dumps(user_info)
    encoded = base64.b64encode(json_string.encode("utf-8")).decode("utf-8")

    email = get_user_email(encoded)

    assert email == ""


