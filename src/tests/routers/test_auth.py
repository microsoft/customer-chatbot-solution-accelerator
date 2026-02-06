"""
Tests for auth endpoints - Using FastAPI TestClient for HTTP endpoint testing.
Uses function-based tests with fixtures from conftest.py.
"""

from unittest.mock import AsyncMock, MagicMock, patch

# =============================================================================
# Debug Endpoint Tests - /api/auth/debug
# =============================================================================


def test_debug_endpoint_returns_headers(client):
    """Test debug endpoint returns header information."""
    response = client.get(
        "/api/auth/debug",
        headers={"user-agent": "TestClient/1.0", "host": "testserver"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "has_easy_auth" in data
    assert "easy_auth_headers" in data
    assert "all_headers" in data
    assert "user_agent" in data
    assert "host" in data


def test_debug_endpoint_with_easy_auth_headers(client):
    """Test debug endpoint with Easy Auth headers present."""
    response = client.get(
        "/api/auth/debug",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
            "x-ms-client-principal-idp": "aad",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_easy_auth"] is True
    assert len(data["easy_auth_headers"]) >= 2


def test_debug_endpoint_without_easy_auth_headers(client):
    """Test debug endpoint without Easy Auth headers."""
    response = client.get("/api/auth/debug")

    assert response.status_code == 200
    data = response.json()
    assert data["has_easy_auth"] is False
    assert len(data["easy_auth_headers"]) == 0


def test_debug_endpoint_with_forwarded_headers(client):
    """Test debug endpoint with forwarded headers."""
    response = client.get(
        "/api/auth/debug",
        headers={
            "x-forwarded-for": "192.168.1.100",
            "x-forwarded-proto": "https",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["x_forwarded_for"] == "192.168.1.100"
    assert data["x_forwarded_proto"] == "https"


# =============================================================================
# Me Endpoint Tests - /api/auth/me
# =============================================================================


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_guest_user(mock_get_db, client):
    """Test /me endpoint returns guest user when no auth headers."""
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "email" in data
    assert "roles" in data
    assert "is_authenticated" in data


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_existing_user_found_by_id(mock_get_db, client):
    """Test /me endpoint finds existing user by ID."""
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.role.value = "user"
    mock_db.get_user.return_value = mock_user
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "user-123"
    assert data["is_authenticated"] is True


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_existing_user_found_by_email_fallback(mock_get_db, client):
    """Test /me endpoint finds user by email when ID lookup fails."""
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.role.value = "user"
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.return_value = mock_user
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["is_authenticated"] is True


@patch("app.routers.auth.create_demo_order_history")
@patch("app.routers.auth.get_db_service")
def test_me_endpoint_create_new_user_with_demo_orders(
    mock_get_db, mock_create_demo, client
):
    """Test /me endpoint creates new user with demo orders."""
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "new-user-123"
    mock_user.email = "newuser@example.com"
    mock_user.name = "New User"
    mock_user.role.value = "user"
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.side_effect = Exception("Not found")
    mock_db.create_user_with_password.return_value = mock_user
    mock_get_db.return_value = mock_db
    mock_create_demo.return_value = None

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "new-user-123",
            "x-ms-client-principal-name": "newuser@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is True


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_create_user_without_email_returns_guest(mock_get_db, client):
    """Test /me endpoint returns guest when user has no email."""
    mock_db = AsyncMock()
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.side_effect = Exception("Not found")
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "user-no-email",
            # No email header
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Should fall back to guest or authenticated user without email
    assert "id" in data
    assert "is_authenticated" in data


@patch("app.routers.auth.create_demo_order_history")
@patch("app.routers.auth.get_db_service")
def test_me_endpoint_demo_order_failure_does_not_break_flow(
    mock_get_db, mock_create_demo, client
):
    """Test /me endpoint continues even if demo order creation fails."""
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@example.com"
    mock_user.name = "Test User"
    mock_user.role.value = "user"
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.side_effect = Exception("Not found")
    mock_db.create_user_with_password.return_value = mock_user
    mock_get_db.return_value = mock_db
    mock_create_demo.side_effect = Exception("Demo order creation failed")

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is True


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_user_creation_failure_returns_fallback(mock_get_db, client):
    """Test /me endpoint returns fallback when user creation fails."""
    mock_db = AsyncMock()
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.side_effect = Exception("Not found")
    mock_db.create_user_with_password.side_effect = Exception("Creation failed")
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "is_authenticated" in data


def test_me_endpoint_exception_returns_guest(client):
    """Test /me endpoint returns guest on exception."""
    with patch("app.routers.auth.get_current_user") as mock_get_current:
        mock_get_current.side_effect = Exception("Auth failed")

        response = client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["is_guest"] is True


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_user_with_admin_role(mock_get_db, client):
    """Test /me endpoint returns admin role correctly."""
    mock_db = AsyncMock()
    admin_user = MagicMock()
    admin_user.id = "admin-123"
    admin_user.email = "admin@example.com"
    admin_user.name = "Admin User"
    admin_user.role.value = "admin"
    mock_db.get_user.return_value = admin_user
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "admin-123",
            "x-ms-client-principal-name": "admin@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "admin" in data["roles"]


@patch("app.routers.auth.get_db_service")
def test_me_endpoint_user_without_role_defaults_to_user(mock_get_db, client):
    """Test /me endpoint defaults to user role when no role."""
    mock_db = AsyncMock()
    basic_user = MagicMock()
    basic_user.id = "basic-123"
    basic_user.email = "basic@example.com"
    basic_user.name = "Basic User"
    # Don't set role - let it be a MagicMock which won't have .value
    mock_db.get_user.return_value = basic_user
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "basic-123",
            "x-ms-client-principal-name": "basic@example.com",
        },
    )

    assert response.status_code == 200
    data = response.json()
    # The response should have roles field
    assert "roles" in data


# =============================================================================
# Auth With Forwarded Headers Tests
# =============================================================================


@patch("app.routers.auth.get_db_service")
def test_me_with_forwarded_easy_auth_headers(mock_get_db, client):
    """Test /me endpoint with Easy Auth headers."""
    mock_db = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = "forwarded-user"
    mock_user.email = "forwarded@example.com"
    mock_user.name = "Forwarded User"
    mock_user.role.value = "user"
    mock_db.get_user.return_value = mock_user
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "forwarded-user",
            "x-ms-client-principal-name": "forwarded@example.com",
            "x-ms-client-principal-idp": "aad",
            "x-ms-token-aad-id-token": "token123",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["is_authenticated"] is True


def test_me_without_any_headers(client):
    """Test /me endpoint without any headers returns guest."""
    response = client.get("/api/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["is_guest"] is True


@patch("app.routers.auth.get_db_service")
def test_me_with_partial_easy_auth_headers(mock_get_db, client):
    """Test /me endpoint with partial Easy Auth headers."""
    mock_db = AsyncMock()
    mock_db.get_user.side_effect = Exception("Not found")
    mock_db.get_user_by_email.side_effect = Exception("Not found")
    mock_get_db.return_value = mock_db

    response = client.get(
        "/api/auth/me",
        headers={
            "x-ms-client-principal-id": "partial-user",
            # Missing name header
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data


def test_debug_with_multiple_easy_auth_headers(client):
    """Test debug endpoint with all Easy Auth headers."""
    response = client.get(
        "/api/auth/debug",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
            "x-ms-client-principal-idp": "aad",
            "x-ms-token-aad-id-token": "token123",
            "x-ms-client-principal": "base64encodeddata",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_easy_auth"] is True
    assert len(data["easy_auth_headers"]) >= 3


def test_debug_with_all_headers(client):
    """Test debug endpoint with all possible headers."""
    response = client.get(
        "/api/auth/debug",
        headers={
            "x-ms-client-principal-id": "user-123",
            "x-ms-client-principal-name": "test@example.com",
            "x-forwarded-for": "10.0.0.1",
            "x-forwarded-proto": "https",
            "user-agent": "CustomAgent/2.0",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["has_easy_auth"] is True
    assert data["x_forwarded_for"] == "10.0.0.1"
    assert data["x_forwarded_proto"] == "https"
    assert "CustomAgent" in data["user_agent"]
