import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request


class MockHeaders:
    """Mock headers object that behaves like fastapi.Request.headers."""

    def __init__(self, headers_dict):
        self._headers = headers_dict

    def get(self, key, default=None):
        return self._headers.get(key, default)

    def __contains__(self, key):
        return key in self._headers

    def __iter__(self):
        return iter(self._headers.items())

    def __getitem__(self, key):
        return self._headers[key]

    def items(self):
        return self._headers.items()


def make_mock_headers(headers_dict):
    """Create a mock headers object that behaves like fastapi.Request.headers."""
    return MockHeaders(headers_dict)


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request object."""
    request = MagicMock(spec=Request)
    request.headers = make_mock_headers({})
    return request


@pytest.fixture
def sample_user_details():
    """Sample user details from get_authenticated_user_details()."""
    return {
        "user_principal_id": "user123",
        "user_name": "test.user@contoso.com",
        "auth_provider": "aad",
    }


@pytest.fixture
def client_principal_token():
    """Create a valid client principal token."""
    claims = [
        {
            "typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
            "val": "test.user@contoso.com",
        },
        {"typ": "name", "val": "Test User"},
    ]
    principal = {
        "claims": claims,
        "auth_typ": "aad",
        "name_typ": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    }
    return base64.b64encode(json.dumps(principal).encode()).decode()


class TestGetCurrentUserForwardedHeaders:
    """Tests for get_current_user() with forwarded Easy Auth headers."""

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_forwarded_headers_authenticated_user_with_email(
        self, mock_get_user_email, mock_request, client_principal_token
    ):
        """Test with forwarded Easy Auth headers and valid email in token."""
        from app.auth import get_current_user

        # Setup forwarded headers
        headers_dict = {
            "x-ms-client-principal-id": "user123",
            "x-ms-client-principal-name": "test.user@contoso.com",
            "x-ms-client-principal-idp": "aad",
            "x-ms-client-principal": client_principal_token,
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = "test.user@contoso.com"

        result = await get_current_user(mock_request)

        assert result["id"] == "user123"
        assert result["user_id"] == "user123"
        assert result["sub"] == "user123"
        assert result["name"] == "test.user@contoso.com"
        assert result["email"] == "test.user@contoso.com"
        assert result["preferred_username"] == "test.user@contoso.com"
        assert result["roles"] == ["user"]
        assert result["auth_provider"] == "aad"
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_forwarded_headers_no_email_fallback_to_username(
        self, mock_get_user_email, mock_request
    ):
        """Test with forwarded headers but no email in token (fallback to user_name)."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "user456",
            "x-ms-client-principal-name": "fallback.user@contoso.com",
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = ""  # No email found

        result = await get_current_user(mock_request)

        assert result["email"] == "fallback.user@contoso.com"
        assert result["preferred_username"] == "fallback.user@contoso.com"
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_forwarded_headers_missing_username(
        self, mock_get_user_email, mock_request
    ):
        """Test with forwarded headers but missing user_name."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "user789"
            # No x-ms-client-principal-name
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = ""

        result = await get_current_user(mock_request)

        assert result["id"] == "user789"
        assert result["name"] == ""
        assert result["email"] == ""
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_forwarded_headers_with_auth_provider(
        self, mock_get_user_email, mock_request
    ):
        """Test that auth_provider is correctly extracted from forwarded headers."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "user_aad",
            "x-ms-client-principal-name": "aad.user@contoso.com",
            "x-ms-client-principal-idp": "aad",
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = "aad.user@contoso.com"

        result = await get_current_user(mock_request)

        assert result["auth_provider"] == "aad"

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_forwarded_headers_all_optional_fields(
        self, mock_get_user_email, mock_request, client_principal_token
    ):
        """Test with all optional forwarded header fields present."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "full_user",
            "x-ms-client-principal-name": "full@contoso.com",
            "x-ms-client-principal-idp": "aad",
            "x-ms-client-principal": client_principal_token,
            "x-ms-token-aad-id-token": "some-aad-token",
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = "full@contoso.com"

        result = await get_current_user(mock_request)

        assert result["email"] == "full@contoso.com"
        assert result["auth_provider"] == "aad"


class TestGetCurrentUserDirectHeaders:
    """Tests for get_current_user() with direct Easy Auth headers (fallback)."""

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    @patch("app.auth.get_authenticated_user_details")
    async def test_direct_headers_authenticated_user(
        self,
        mock_get_auth_details,
        mock_get_user_email,
        mock_request,
        client_principal_token,
    ):
        """Test with direct Easy Auth headers (no forwarded prefix)."""
        from app.auth import get_current_user

        # No forwarded headers, only direct headers
        headers_dict = {"x-ms-client-principal": client_principal_token}
        mock_request.headers = make_mock_headers(headers_dict)

        # get_authenticated_user_details called with headers
        mock_get_auth_details.return_value = {
            "user_principal_id": "direct123",
            "user_name": "direct@contoso.com",
            "auth_provider": "aad",
            "x-ms-client-principal": client_principal_token,
        }
        mock_get_user_email.return_value = "direct@contoso.com"

        result = await get_current_user(mock_request)

        assert result["id"] == "direct123"
        assert result["email"] == "direct@contoso.com"
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_authenticated_user_details")
    async def test_direct_headers_no_user_fallback_guest(
        self, mock_get_auth_details, mock_get_sample_user, mock_request
    ):
        """Test with no auth headers - should fall back to guest user."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        # get_authenticated_user_details returns None
        mock_get_auth_details.return_value = None

        guest_details = {"user_principal_id": "guest000", "user_name": "guest"}
        mock_get_sample_user.return_value = guest_details

        result = await get_current_user(mock_request)

        assert result["id"] == "guest000"
        assert result["name"] == "guest"
        assert result["email"] == "guest@contoso.com"
        assert result["roles"] == ["guest"]
        assert result["is_guest"] is True

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_authenticated_user_details")
    async def test_direct_headers_guest_user_flag_set(
        self, mock_get_auth_details, mock_get_sample_user, mock_request
    ):
        """Test when is_guest flag is set in user_details."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        guest_details = {
            "user_principal_id": "guest789",
            "user_name": "guest",
            "is_guest": True,
        }

        mock_get_auth_details.return_value = guest_details
        mock_get_sample_user.return_value = guest_details

        result = await get_current_user(mock_request)

        assert result["id"] == "guest789"
        assert result["is_guest"] is True
        assert result["roles"] == ["guest"]


class TestGetCurrentUserErrorHandling:
    """Tests for error handling and edge cases in get_current_user()."""

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_user_email")
    async def test_exception_in_email_extraction_falls_back_to_username(
        self, mock_get_user_email, mock_get_sample_user, mock_request
    ):
        """Test that exception during email extraction falls back to user_name."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "error_user",
            "x-ms-client-principal-name": "error@contoso.com",
        }
        mock_request.headers = make_mock_headers(headers_dict)

        # Simulate error during email extraction
        mock_get_user_email.side_effect = Exception("Email extraction error")

        result = await get_current_user(mock_request)

        # Should fall back to user_name
        assert result["email"] == "error@contoso.com"
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_authenticated_user_details")
    async def test_exception_during_auth_fallback_to_guest(
        self, mock_get_auth_details, mock_get_sample_user, mock_request
    ):
        """Test exception during authentication falls back to guest user."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        # Simulate error during authentication
        mock_get_auth_details.side_effect = Exception("Auth error")

        guest_details = {"user_principal_id": "guest_fallback", "user_name": "guest"}
        mock_get_sample_user.return_value = guest_details

        result = await get_current_user(mock_request)

        assert result["id"] == "guest_fallback"
        assert result["is_guest"] is True
        assert result["email"] == "guest@contoso.com"

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_empty_user_name_and_email(self, mock_get_user_email, mock_request):
        """Test handling of empty user_name and no email."""
        from app.auth import get_current_user

        headers_dict = {"x-ms-client-principal-id": "user_empty"}
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = ""

        result = await get_current_user(mock_request)

        assert result["email"] == ""
        assert result["preferred_username"] == ""
        assert result["name"] == ""


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional() function."""

    @pytest.mark.asyncio
    @patch("app.auth.get_current_user")
    async def test_returns_user_when_successful(
        self, mock_get_current_user, mock_request
    ):
        """Test returns user dict when get_current_user succeeds."""
        from app.auth import get_current_user_optional

        expected_user = {
            "id": "user123",
            "email": "test@contoso.com",
            "is_guest": False,
        }
        mock_get_current_user.return_value = expected_user

        result = await get_current_user_optional(mock_request)

        assert result == expected_user
        mock_get_current_user.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    @patch("app.auth.get_current_user")
    async def test_returns_none_on_exception(self, mock_get_current_user, mock_request):
        """Test returns None when get_current_user raises exception."""
        from app.auth import get_current_user_optional

        mock_get_current_user.side_effect = Exception("Auth failed")

        result = await get_current_user_optional(mock_request)

        assert result is None

    @pytest.mark.asyncio
    @patch("app.auth.get_current_user")
    async def test_returns_none_on_any_error(self, mock_get_current_user, mock_request):
        """Test returns None for any type of error."""
        from app.auth import get_current_user_optional

        mock_get_current_user.side_effect = ValueError("Invalid token")

        result = await get_current_user_optional(mock_request)

        assert result is None


class TestEmailExtraction:
    """Tests for email extraction logic in get_current_user()."""

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_email_from_client_principal_b64(
        self, mock_get_user_email, mock_request, client_principal_token
    ):
        """Test email extraction from client_principal_b64 field."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "user1",
            "x-ms-client-principal-name": "test@contoso.com",
            "x-ms-client-principal": client_principal_token,
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = "from_token@contoso.com"

        result = await get_current_user(mock_request)

        assert result["email"] == "from_token@contoso.com"
        # Verify get_user_email was called with the token
        mock_get_user_email.assert_called_once_with(client_principal_token)

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    @patch("app.auth.get_authenticated_user_details")
    async def test_email_from_x_ms_client_principal(
        self,
        mock_get_auth_details,
        mock_get_user_email,
        mock_request,
        client_principal_token,
    ):
        """Test fallback to x-ms-client-principal for email extraction."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        # Direct headers with x-ms-client-principal
        mock_get_auth_details.return_value = {
            "user_principal_id": "user2",
            "user_name": "test2@contoso.com",
            "x-ms-client-principal": client_principal_token,
        }
        mock_get_user_email.return_value = "from_xms@contoso.com"

        result = await get_current_user(mock_request)

        assert result["email"] == "from_xms@contoso.com"


class TestRolesAndGuestFlags:
    """Tests for roles array and is_guest flag logic."""

    @pytest.mark.asyncio
    @patch("app.auth.get_user_email")
    async def test_regular_user_gets_user_role(self, mock_get_user_email, mock_request):
        """Test that regular authenticated user gets ['user'] role."""
        from app.auth import get_current_user

        headers_dict = {
            "x-ms-client-principal-id": "regular_user",
            "x-ms-client-principal-name": "user@contoso.com",
        }
        mock_request.headers = make_mock_headers(headers_dict)
        mock_get_user_email.return_value = ""

        result = await get_current_user(mock_request)

        assert result["roles"] == ["user"]
        assert result["is_guest"] is False

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_authenticated_user_details")
    async def test_guest_user_gets_guest_role(
        self, mock_get_auth_details, mock_get_sample_user, mock_request
    ):
        """Test that guest user gets ['guest'] role."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        guest_details = {
            "user_principal_id": "guest",
            "user_name": "guest",
            "is_guest": True,
        }

        mock_get_auth_details.return_value = guest_details
        mock_get_sample_user.return_value = guest_details

        result = await get_current_user(mock_request)

        assert result["roles"] == ["guest"]
        assert result["is_guest"] is True

    @pytest.mark.asyncio
    @patch("app.auth.get_sample_user")
    @patch("app.auth.get_authenticated_user_details")
    async def test_exception_fallback_guest_role(
        self, mock_get_auth_details, mock_get_sample_user, mock_request
    ):
        """Test that exception fallback creates guest with guest role."""
        from app.auth import get_current_user

        headers_dict = {}
        mock_request.headers = make_mock_headers(headers_dict)

        mock_get_auth_details.return_value = None

        guest_details = {"user_principal_id": "exception_guest", "user_name": "guest"}
        mock_get_sample_user.return_value = guest_details

        result = await get_current_user(mock_request)

        assert result["roles"] == ["guest"]
        assert result["is_guest"] is True
        assert result["email"] == "guest@contoso.com"
