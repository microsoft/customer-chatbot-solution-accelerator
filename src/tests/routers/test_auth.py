"""
Tests for auth endpoints - Combined comprehensive test suite
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request


class MockHeaders:
    """Mock headers object for FastAPI Request."""

    def __init__(self, headers_dict):
        self._headers = headers_dict

    def get(self, key, default=None):
        return self._headers.get(key, default)

    def __contains__(self, key):
        return key in self._headers

    def __iter__(self):
        return iter(self._headers.items())

    def items(self):
        return self._headers.items()


def make_mock_request(headers_dict):
    """Create a mock FastAPI Request with headers."""
    request = MagicMock(spec=Request)
    request.headers = MockHeaders(headers_dict)
    return request


@pytest.fixture
def mock_db_service():
    """Create a mock database service."""
    service = AsyncMock()
    return service


@pytest.fixture
def mock_user():
    """Create a mock user object."""
    user = MagicMock()
    user.id = "user123"
    user.email = "test@contoso.com"
    user.name = "Test User"
    user.role.value = "user"
    return user


# ============================================================================
# Basic Client Tests
# ============================================================================


# ============================================================================
# Debug Endpoint Tests
# ============================================================================


class TestDebugAuthHeaders:
    """Tests for /api/auth/debug endpoint."""

    @pytest.mark.asyncio
    async def test_debug_auth_headers_with_easy_auth(self):
        """Test debug endpoint with Easy Auth headers present."""
        from app.routers.auth import debug_auth_headers

        headers_dict = {
            "x-ms-client-principal-id": "user123",
            "x-ms-client-principal-name": "test@contoso.com",
            "user-agent": "TestAgent/1.0",
            "host": "localhost:8000",
            "x-forwarded-for": "192.168.1.1",
            "x-forwarded-proto": "https",
        }
        request = make_mock_request(headers_dict)

        result = await debug_auth_headers(request)

        assert result["has_easy_auth"] is True
        assert len(result["easy_auth_headers"]) == 2
        assert "x-ms-client-principal-id" in result["easy_auth_headers"]
        assert result["user_agent"] == "TestAgent/1.0"
        assert result["host"] == "localhost:8000"
        assert result["x_forwarded_for"] == "192.168.1.1"
        assert result["x_forwarded_proto"] == "https"

    @pytest.mark.asyncio
    async def test_debug_auth_headers_without_easy_auth(self):
        """Test debug endpoint without Easy Auth headers."""
        from app.routers.auth import debug_auth_headers

        headers_dict = {"user-agent": "TestAgent/1.0", "host": "localhost:8000"}
        request = make_mock_request(headers_dict)

        result = await debug_auth_headers(request)

        assert result["has_easy_auth"] is False
        assert len(result["easy_auth_headers"]) == 0
        assert result["user_agent"] == "TestAgent/1.0"

    @pytest.mark.asyncio
    async def test_debug_auth_headers_missing_optional_headers(self):
        """Test debug endpoint with missing optional headers."""
        from app.routers.auth import debug_auth_headers

        headers_dict = {}
        request = make_mock_request(headers_dict)

        result = await debug_auth_headers(request)

        assert result["has_easy_auth"] is False
        assert result["user_agent"] == "unknown"
        assert result["host"] == "unknown"
        assert result["x_forwarded_for"] == "none"
        assert result["x_forwarded_proto"] == "none"


# ============================================================================
# Get Current User Info Tests
# ============================================================================


class TestGetCurrentUserInfo:
    """Tests for /api/auth/me endpoint."""

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_current_user")
    async def test_guest_user_returns_immediately(self, mock_get_current_user):
        """Test that guest user returns immediately without DB access."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "guest123",
            "name": "Guest User",
            "email": "guest@contoso.com",
            "roles": ["guest"],
            "is_guest": True,
        }

        result = await get_current_user_info(request)

        assert result["id"] == "guest123"
        assert result["name"] == "Guest User"
        assert result["email"] == "guest@contoso.com"
        assert result["roles"] == ["guest"]
        assert result["is_authenticated"] is False
        assert result["is_guest"] is True

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_existing_user_found_by_id(
        self, mock_get_current_user, mock_get_db_service, mock_db_service, mock_user
    ):
        """Test finding existing user by ID."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user123",
            "sub": "user123",
            "name": "Test User",
            "email": "test@contoso.com",
            "preferred_username": "test@contoso.com",
            "is_guest": False,
        }

        mock_db_service.get_user.return_value = mock_user
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        assert result["id"] == "user123"
        assert result["name"] == "Test User"
        assert result["email"] == "test@contoso.com"
        assert result["roles"] == ["user"]
        assert result["is_authenticated"] is True
        assert result["is_guest"] is False

        mock_db_service.get_user.assert_called_once_with("user123")

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_existing_user_found_by_email_fallback(
        self, mock_get_current_user, mock_get_db_service, mock_db_service, mock_user
    ):
        """Test finding existing user by email when ID lookup fails."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user123",
            "sub": "user123",
            "name": "Test User",
            "email": "test@contoso.com",
            "preferred_username": "test@contoso.com",
            "is_guest": False,
        }

        # First call (by ID) raises exception, second call (by email) succeeds
        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.return_value = mock_user
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        assert result["email"] == "test@contoso.com"
        mock_db_service.get_user.assert_called_once_with("user123")
        mock_db_service.get_user_by_email.assert_called_once_with("test@contoso.com")

    @pytest.mark.asyncio
    @patch("app.routers.auth.create_demo_order_history")
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_create_new_user_with_demo_orders(
        self,
        mock_get_current_user,
        mock_get_db_service,
        mock_create_demo,
        mock_db_service,
        mock_user,
    ):
        """Test creating a new user with demo order history."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "new_user123",
            "sub": "new_user123",
            "name": "New User",
            "email": "newuser@contoso.com",
            "preferred_username": "newuser@contoso.com",
            "is_guest": False,
        }

        # User not found by ID or email
        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_db_service.create_user_with_password.return_value = mock_user
        mock_get_db_service.return_value = mock_db_service
        mock_create_demo.return_value = None

        result = await get_current_user_info(request)

        assert result["is_authenticated"] is True
        mock_db_service.create_user_with_password.assert_called_once_with(
            email="newuser@contoso.com",
            name="New User",
            password="",
            user_id="new_user123",
        )
        mock_create_demo.assert_called_once_with("user123")

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_create_user_without_email_returns_guest(
        self, mock_get_current_user, mock_get_db_service, mock_db_service
    ):
        """Test that creating user without email falls back to guest due to exception."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user_no_email",
            "sub": "user_no_email",
            "name": "No Email User",
            "email": "",  # No email
            "preferred_username": "",
            "is_guest": False,
        }

        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        # HTTPException is raised but caught, returns guest
        assert result["is_guest"] is True
        assert result["email"] == "guest@contoso.com"

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_create_user_without_name_uses_default(
        self, mock_get_current_user, mock_get_db_service, mock_db_service, mock_user
    ):
        """Test creating user without name uses 'Unknown User' default."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user_no_name",
            "sub": "user_no_name",
            "name": "",  # No name
            "email": "noname@contoso.com",
            "preferred_username": "noname@contoso.com",
            "is_guest": False,
        }

        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_db_service.create_user_with_password.return_value = mock_user
        mock_get_db_service.return_value = mock_db_service

        with patch("app.routers.auth.create_demo_order_history"):
            await get_current_user_info(request)

        # Verify it used "Unknown User" as default
        call_args = mock_db_service.create_user_with_password.call_args
        assert call_args[1]["name"] == "Unknown User"

    @pytest.mark.asyncio
    @patch("app.routers.auth.create_demo_order_history")
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_demo_order_creation_failure_does_not_break_flow(
        self,
        mock_get_current_user,
        mock_get_db_service,
        mock_create_demo,
        mock_db_service,
        mock_user,
    ):
        """Test that demo order creation failure doesn't prevent user creation."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user_demo_fail",
            "sub": "user_demo_fail",
            "name": "Demo Fail User",
            "email": "demofail@contoso.com",
            "preferred_username": "demofail@contoso.com",
            "is_guest": False,
        }

        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_db_service.create_user_with_password.return_value = mock_user
        mock_get_db_service.return_value = mock_db_service

        # Simulate demo order creation failure
        mock_create_demo.side_effect = Exception("Demo order creation failed")

        result = await get_current_user_info(request)

        # User should still be returned successfully
        assert result["is_authenticated"] is True
        assert result["email"] == "test@contoso.com"

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_user_creation_failure_returns_fallback_data(
        self, mock_get_current_user, mock_get_db_service, mock_db_service
    ):
        """Test that user creation failure returns fallback user data."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "user_create_fail",
            "sub": "user_create_fail",
            "name": "Create Fail User",
            "email": "createfail@contoso.com",
            "preferred_username": "createfail@contoso.com",
            "is_guest": False,
        }

        mock_db_service.get_user.side_effect = Exception("Not found")
        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_db_service.create_user_with_password.side_effect = Exception(
            "Creation failed"
        )
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        # Should return fallback data
        assert result["id"] == "user_create_fail"
        assert result["name"] == "Create Fail User"
        assert result["email"] == "createfail@contoso.com"
        assert result["roles"] == ["user"]
        assert result["is_authenticated"] is True

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_current_user")
    async def test_exception_in_get_current_user_returns_guest(
        self, mock_get_current_user
    ):
        """Test that exception in overall flow returns guest user."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        # Simulate exception in get_current_user
        mock_get_current_user.side_effect = Exception("Auth failed")

        result = await get_current_user_info(request)

        assert result["id"] == "guest-user-00000000"
        assert result["name"] == "Guest User"
        assert result["email"] == "guest@contoso.com"
        assert result["roles"] == ["guest"]
        assert result["is_authenticated"] is False
        assert result["is_guest"] is True

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_user_without_user_id_field(
        self, mock_get_current_user, mock_get_db_service, mock_db_service
    ):
        """Test handling user without user_id field."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        # No user_id available
        mock_get_current_user.return_value = {
            "name": "No ID User",
            "email": "noid@contoso.com",
            "preferred_username": "noid@contoso.com",
            "is_guest": False,
        }

        mock_db_service.get_user_by_email.side_effect = Exception("Not found")
        mock_get_db_service.return_value = mock_db_service

        # Should raise error because no email for user creation
        result = await get_current_user_info(request)

        # Since we have email, user creation should be attempted
        assert result["is_authenticated"] is True

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_user_with_role_attribute(
        self, mock_get_current_user, mock_get_db_service, mock_db_service
    ):
        """Test user with role attribute returns correct role."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "admin123",
            "sub": "admin123",
            "name": "Admin User",
            "email": "admin@contoso.com",
            "preferred_username": "admin@contoso.com",
            "is_guest": False,
        }

        admin_user = MagicMock()
        admin_user.id = "admin123"
        admin_user.email = "admin@contoso.com"
        admin_user.name = "Admin User"
        admin_user.role.value = "admin"

        mock_db_service.get_user.return_value = admin_user
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        assert result["roles"] == ["admin"]

    @pytest.mark.asyncio
    @patch("app.routers.auth.get_db_service")
    @patch("app.routers.auth.get_current_user")
    async def test_user_without_role_attribute_defaults_to_user(
        self, mock_get_current_user, mock_get_db_service, mock_db_service
    ):
        """Test user without role attribute defaults to 'user' role."""
        from app.routers.auth import get_current_user_info

        request = make_mock_request({})

        mock_get_current_user.return_value = {
            "id": "basic123",
            "sub": "basic123",
            "name": "Basic User",
            "email": "basic@contoso.com",
            "preferred_username": "basic@contoso.com",
            "is_guest": False,
        }

        basic_user = MagicMock()
        basic_user.id = "basic123"
        basic_user.email = "basic@contoso.com"
        basic_user.name = "Basic User"
        # No role attribute
        del basic_user.role

        mock_db_service.get_user.return_value = basic_user
        mock_get_db_service.return_value = mock_db_service

        result = await get_current_user_info(request)

        assert result["roles"] == ["user"]
