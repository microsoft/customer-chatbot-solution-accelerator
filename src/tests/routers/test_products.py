"""
Test cases for products endpoints (/api/products)
Uses FastAPI TestClient with function-based tests.
"""

from unittest.mock import AsyncMock, Mock, patch

# =============================================================================
# GET /api/products/
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_get_products_endpoint(mock_get_db, client, sample_product):
    """Test GET /api/products/ endpoint"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(return_value=[sample_product])
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Product"
    assert data[0]["price"] == 29.99


@patch("app.routers.products.get_db_service")
def test_get_products_with_query_parameters(mock_get_db, client, sample_product):
    """Test GET /api/products/ endpoint with query parameters"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(return_value=[sample_product])
    mock_get_db.return_value = mock_db_service

    params = {
        "category": "test",
        "min_price": 20,
        "max_price": 50,
        "min_rating": 4,
        "in_stock_only": True,
        "query": "test",
        "sort_by": "price",
        "sort_order": "asc",
        "page": 1,
        "page_size": 10,
    }

    response = client.get("/api/products/", params=params)

    assert response.status_code == 200
    mock_db_service.get_products.assert_called_once()
    call_args = mock_db_service.get_products.call_args[0][0]
    assert call_args["category"] == "test"
    assert call_args["min_price"] == 20.0
    assert call_args["in_stock_only"] is True


@patch("app.routers.products.get_db_service")
def test_get_products_pagination(mock_get_db, client, sample_products_list):
    """Test GET /api/products/ endpoint pagination"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(return_value=sample_products_list)
    mock_get_db.return_value = mock_db_service

    # Test first page
    response = client.get("/api/products/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10

    # Test third page (should have 5 items)
    response = client.get("/api/products/?page=3&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


@patch("app.routers.products.get_db_service")
def test_get_products_error_handling(mock_get_db, client):
    """Test GET /api/products/ endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(side_effect=Exception("Database error"))
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/")

    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "success" in data
    assert data["success"] is False
    assert "database" in data["message"].lower() or "error" in data["error"].lower()


# =============================================================================
# GET /api/products/{product_id}
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_get_product_by_id_endpoint(mock_get_db, client, sample_product):
    """Test GET /api/products/{product_id} endpoint"""
    mock_db_service = Mock()
    mock_db_service.get_product = AsyncMock(return_value=sample_product)
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/prod-123")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "prod-123"
    assert data["title"] == "Test Product"


@patch("app.routers.products.get_db_service")
def test_get_product_by_id_not_found(mock_get_db, client):
    """Test GET /api/products/{product_id} endpoint - product not found"""
    mock_db_service = Mock()
    mock_db_service.get_product = AsyncMock(return_value=None)
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Product not found"
    assert data["success"] is False


@patch("app.routers.products.get_db_service")
def test_get_product_by_id_error_handling(mock_get_db, client):
    """Test GET /api/products/{product_id} endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.get_product = AsyncMock(
        side_effect=Exception("Database connection error")
    )
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/prod-123")

    assert response.status_code == 500
    data = response.json()
    assert "error" in data


# =============================================================================
# POST /api/products/
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_create_product_endpoint(mock_get_db, client, sample_product):
    """Test POST /api/products/ endpoint"""
    mock_db_service = Mock()
    mock_db_service.create_product = AsyncMock(return_value=sample_product)
    mock_get_db.return_value = mock_db_service

    product_data = {
        "title": "New Product",
        "price": 49.99,
        "description": "A new product",
        "category": "new",
        "image": "https://example.com/new.jpg",
        "in_stock": True,
        "tags": ["new", "test"],
        "specifications": {"color": "red"},
    }

    response = client.post("/api/products/", json=product_data)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    mock_db_service.create_product.assert_called_once()


@patch("app.routers.products.get_db_service")
def test_create_product_error_handling(mock_get_db, client):
    """Test POST /api/products/ endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.create_product = AsyncMock(
        side_effect=Exception("Failed to create product")
    )
    mock_get_db.return_value = mock_db_service

    product_data = {
        "title": "New Product",
        "price": 49.99,
        "description": "A new product",
        "category": "new",
        "image": "https://example.com/new.jpg",
        "in_stock": True,
        "tags": [],
        "specifications": {},
    }

    response = client.post("/api/products/", json=product_data)

    assert response.status_code == 500


# =============================================================================
# PUT /api/products/{product_id}
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_update_product_endpoint(mock_get_db, client, sample_product):
    """Test PUT /api/products/{product_id} endpoint"""
    updated_product = sample_product.model_copy()
    updated_product.title = "Updated Product"

    mock_db_service = Mock()
    mock_db_service.update_product = AsyncMock(return_value=updated_product)
    mock_get_db.return_value = mock_db_service

    update_data = {"title": "Updated Product", "price": 39.99}

    response = client.put("/api/products/prod-123", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Product"


@patch("app.routers.products.get_db_service")
def test_update_product_not_found(mock_get_db, client):
    """Test PUT /api/products/{product_id} endpoint - product not found"""
    mock_db_service = Mock()
    mock_db_service.update_product = AsyncMock(return_value=None)
    mock_get_db.return_value = mock_db_service

    update_data = {"title": "Updated Product"}

    response = client.put("/api/products/nonexistent", json=update_data)

    assert response.status_code in [404, 500]
    if response.status_code == 404:
        data = response.json()
        assert data["message"] == "Product not found"
        assert data["success"] is False


@patch("app.routers.products.get_db_service")
def test_update_product_error_handling(mock_get_db, client):
    """Test PUT /api/products/{product_id} endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.update_product = AsyncMock(
        side_effect=Exception("Failed to update product")
    )
    mock_get_db.return_value = mock_db_service

    update_data = {"title": "Updated Product"}

    response = client.put("/api/products/prod-123", json=update_data)

    assert response.status_code == 500


# =============================================================================
# DELETE /api/products/{product_id}
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_delete_product_success(mock_get_db, client):
    """Test DELETE /api/products/{product_id} endpoint success"""
    mock_db_service = Mock()
    mock_db_service.delete_product = AsyncMock(return_value=True)
    mock_get_db.return_value = mock_db_service

    response = client.delete("/api/products/prod-123")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Product deleted successfully"


@patch("app.routers.products.get_db_service")
def test_delete_product_not_found(mock_get_db, client):
    """Test DELETE /api/products/{product_id} endpoint - product not found"""
    mock_db_service = Mock()
    mock_db_service.delete_product = AsyncMock(return_value=False)
    mock_get_db.return_value = mock_db_service

    response = client.delete("/api/products/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "Product not found"
    assert data["success"] is False


@patch("app.routers.products.get_db_service")
def test_delete_product_error_handling(mock_get_db, client):
    """Test DELETE /api/products/{product_id} endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.delete_product = AsyncMock(
        side_effect=Exception("Failed to delete product")
    )
    mock_get_db.return_value = mock_db_service

    response = client.delete("/api/products/prod-123")

    assert response.status_code == 500


# =============================================================================
# GET /api/products/categories/list
# =============================================================================


@patch("app.routers.products.get_db_service")
def test_get_categories_endpoint(mock_get_db, client, sample_products_with_categories):
    """Test GET /api/products/categories/list endpoint"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(return_value=sample_products_with_categories)
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/categories/list")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "cat1" in data
    assert "cat2" in data


@patch("app.routers.products.get_db_service")
def test_get_categories_error_handling(mock_get_db, client):
    """Test GET /api/products/categories/list endpoint error handling"""
    mock_db_service = Mock()
    mock_db_service.get_products = AsyncMock(
        side_effect=Exception("Failed to get categories")
    )
    mock_get_db.return_value = mock_db_service

    response = client.get("/api/products/categories/list")

    assert response.status_code == 500
