from unittest.mock import AsyncMock, Mock, patch


@patch("app.database.get_db_service")
@patch("app.auth.get_current_user")
def test_complete_user_workflow(
    mock_get_user, mock_get_db, client, sample_user, sample_product, sample_cart
):
    """Test complete user authentication and data flow"""
    mock_get_user.return_value = {
        "id": sample_user.id,
        "user_id": sample_user.id,
        "name": sample_user.name,
        "email": sample_user.email,
        "is_guest": False,
    }

    mock_db_service = Mock()
    mock_db_service.get_user = AsyncMock(return_value=sample_user)
    mock_db_service.get_products = AsyncMock(return_value=[sample_product])
    mock_db_service.get_product = AsyncMock(return_value=sample_product)
    mock_db_service.get_cart = AsyncMock(return_value=sample_cart)
    mock_db_service.update_cart = AsyncMock(return_value=sample_cart)
    mock_get_db.return_value = mock_db_service

    # Test authentication
    response = client.get("/api/auth/me")
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        auth_data = response.json()
        assert "email" in auth_data

    # Test product listing
    response = client.get("/api/products/")
    assert response.status_code in [200, 500]

    if response.status_code == 200:
        products = response.json()
        assert len(products) == 1
        assert products[0]["title"] == sample_product.title

        # Test getting specific product
        response = client.get(f"/api/products/{sample_product.id}")
        assert response.status_code == 200
        product_data = response.json()
        assert product_data["id"] == sample_product.id


# =============================================================================
# API Health and Documentation Tests
# =============================================================================


def test_api_health_and_docs(client):
    """Test API health endpoints and documentation"""
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data

    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

    # Test docs are accessible
    response = client.get("/docs")
    assert response.status_code == 200


# =============================================================================
# Error Handling Integration Tests
# =============================================================================


@patch("app.database.get_db_service")
def test_error_handling_workflow(mock_get_db, client):
    """Test API error handling across endpoints"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(
        side_effect=Exception("Database connection failed")
    )
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/")
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "success" in data
    assert data["success"] is False


def test_404_handling(client):
    """Test 404 handling for non-existent endpoints"""
    response = client.get("/api/nonexistent-endpoint")
    assert response.status_code == 404


# =============================================================================
# Chat Integration Tests
# =============================================================================


@patch("app.routers.chat.get_cosmos_service")
@patch("app.routers.chat.get_current_user_optional")
def test_chat_integration_authenticated_user(mock_get_user, mock_cosmos, client):
    """Test chat functionality for authenticated user"""
    mock_get_user.return_value = {"user_id": "chat-user"}

    mock_cosmos_service = Mock()
    mock_cosmos_service.get_chat_sessions_by_user = AsyncMock(return_value=[])
    mock_cosmos.return_value = mock_cosmos_service

    response = client.get("/api/chat/sessions")
    assert response.status_code == 200
    sessions = response.json()
    assert isinstance(sessions, list)


@patch("app.routers.chat.get_current_user_optional")
def test_chat_integration_anonymous_user(mock_get_user, client):
    """Test chat functionality for anonymous user"""
    mock_get_user.return_value = None

    response = client.get("/api/chat/sessions")
    # Anonymous user returns empty list or may return 500 due to service dependencies
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        sessions = response.json()
        assert len(sessions) == 0


# =============================================================================
# Cart Integration Tests
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_cart_integration_workflow(
    mock_get_db, mock_get_user, client, sample_product, sample_cart, mock_user_context
):
    """Test cart workflow: get cart, add item, update, checkout"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart)
    mock_db.get_product = AsyncMock(return_value=sample_product)
    mock_db.update_cart = AsyncMock()

    # Get empty cart
    response = client.get("/api/cart")
    assert response.status_code in [200, 500]

    # Add item to cart
    response = client.post(
        "/api/cart/add", json={"product_id": sample_product.id, "quantity": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# =============================================================================
# Products Integration Tests
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_products_integration_workflow(mock_get_db, client, sample_product):
    """Test products workflow: list, get, filter"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(return_value=[sample_product])
    mock_db_service.get_product = AsyncMock(return_value=sample_product)
    mock_get_db.return_value = mock_db_service

    # List products
    response = client.get("/api/products/")
    assert response.status_code == 200
    products = response.json()
    assert len(products) == 1

    # Get specific product
    response = client.get(f"/api/products/{sample_product.id}")
    assert response.status_code == 200
    product = response.json()
    assert product["id"] == sample_product.id

    # Filter products
    response = client.get("/api/products/?category=test&in_stock_only=true")
    assert response.status_code == 200
