"""
Test cases for main application endpoints.
Uses FastAPI TestClient with function-based tests.
"""

from unittest.mock import patch

# =============================================================================
# Root Endpoint Tests
# =============================================================================


def test_root_endpoint(client):
    """Test GET / endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data
    assert "status" in data
    assert data["status"] == "healthy"
    assert data["docs"] == "/docs"


# =============================================================================
# Health Endpoint Tests
# =============================================================================


def test_health_endpoint(client):
    """Test GET /health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "database" in data
    assert "openai" in data
    assert "auth" in data
    assert "version" in data


# =============================================================================
# Debug Auth Endpoint Tests
# =============================================================================


@patch("app.main.get_current_user")
def test_debug_auth_endpoint_success(mock_get_user, client):
    """Test GET /debug/auth endpoint with successful authentication"""
    mock_get_user.return_value = {
        "id": "test-user",
        "name": "Test User",
        "email": "test@example.com",
        "is_guest": False,
    }

    response = client.get("/debug/auth")
    assert response.status_code == 200
    data = response.json()
    assert "headers" in data
    assert "current_user" in data
    assert "debug_info" in data


@patch("app.main.get_current_user")
def test_debug_auth_endpoint_error(mock_get_user, client):
    """Test GET /debug/auth endpoint when exception occurs"""
    mock_get_user.side_effect = Exception("Auth error")

    response = client.get("/debug/auth")
    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert "headers" in data
    assert data["error"] == "Auth error"


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_nonexistent_endpoint(client):
    """Test accessing non-existent endpoint returns 404"""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


# =============================================================================
# CORS Tests
# =============================================================================


def test_cors_headers(client):
    """Test CORS functionality"""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert "access-control-allow-origin" in headers
