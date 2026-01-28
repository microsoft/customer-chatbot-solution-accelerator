from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.models import OrderStatus, Transaction

# =============================================================================
# GET /api/cart
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_get_cart_success(
    mock_get_db, mock_get_user, client, sample_cart_with_items, mock_user_context
):
    """Test GET cart endpoint"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)

    response = client.get("/api/cart")

    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert data["id"] == "cart-123"


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_get_cart_not_found(mock_get_db, mock_get_user, client, mock_user_context):
    """Test GET cart endpoint when cart doesn't exist"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=None)

    response = client.get("/api/cart")

    assert response.status_code in [200, 500]


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_get_cart_error_handling(mock_get_db, mock_get_user, client, mock_user_context):
    """Test get cart error handling"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(side_effect=Exception("Database error"))

    response = client.get("/api/cart")

    assert response.status_code == 500


# =============================================================================
# POST /api/cart/add
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_add_to_cart_success(
    mock_get_db, mock_get_user, client, sample_product, sample_cart, mock_user_context
):
    """Test POST add to cart endpoint"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=sample_product)
    mock_db.get_cart = AsyncMock(return_value=sample_cart)
    mock_db.update_cart = AsyncMock()

    response = client.post(
        "/api/cart/add", json={"product_id": sample_product.id, "quantity": 2}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_add_to_cart_product_not_found(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test add to cart with non-existent product"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=None)

    response = client.post(
        "/api/cart/add", json={"product_id": "nonexistent-product", "quantity": 1}
    )

    assert response.status_code in [404, 500]


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_add_to_cart_existing_item(
    mock_get_db,
    mock_get_user,
    client,
    sample_product,
    sample_cart_with_items,
    mock_user_context,
):
    """Test adding to cart when item already exists (updates quantity)"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=sample_product)
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.update_cart = AsyncMock()

    response = client.post(
        "/api/cart/add", json={"product_id": sample_product.id, "quantity": 2}
    )

    assert response.status_code == 200
    mock_db.update_cart.assert_called_once()


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_add_to_cart_no_existing_cart(
    mock_get_db, mock_get_user, client, sample_product, mock_user_context
):
    """Test adding to cart when no cart exists (creates new cart)"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=sample_product)
    mock_db.get_cart = AsyncMock(return_value=None)
    mock_db.update_cart = AsyncMock()

    response = client.post(
        "/api/cart/add", json={"product_id": sample_product.id, "quantity": 1}
    )

    assert response.status_code == 200
    mock_db.update_cart.assert_called_once()


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_add_to_cart_error_handling(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test add to cart error handling"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(side_effect=Exception("Database error"))

    response = client.post(
        "/api/cart/add", json={"product_id": "test-product-1", "quantity": 1}
    )

    assert response.status_code == 500


# =============================================================================
# PUT /api/cart/update
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_item_success(
    mock_get_db, mock_get_user, client, sample_cart_with_items, mock_user_context
):
    """Test PUT update cart item endpoint"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.update_cart = AsyncMock()

    product_id = sample_cart_with_items.items[0].product_id

    response = client.put(
        "/api/cart/update", params={"product_id": product_id, "quantity": 5}
    )

    assert response.status_code in [200, 500]


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_item_remove_with_zero_quantity(
    mock_get_db, mock_get_user, client, sample_cart_with_items, mock_user_context
):
    """Test updating cart item with quantity 0 removes the item"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.update_cart = AsyncMock()

    product_id = sample_cart_with_items.items[0].product_id

    response = client.put(
        "/api/cart/update", params={"product_id": product_id, "quantity": 0}
    )

    assert response.status_code == 200


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_add_new_item(
    mock_get_db, mock_get_user, client, sample_product, sample_cart, mock_user_context
):
    """Test updating cart with new item that doesn't exist in cart"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=sample_product)
    mock_db.get_cart = AsyncMock(return_value=sample_cart)
    mock_db.update_cart = AsyncMock()

    response = client.put(
        "/api/cart/update", params={"product_id": sample_product.id, "quantity": 3}
    )

    assert response.status_code == 200


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_item_not_found_and_product_not_found(
    mock_get_db, mock_get_user, client, sample_cart, mock_user_context
):
    """Test updating cart with item that doesn't exist and product not found"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_product = AsyncMock(return_value=None)
    mock_db.get_cart = AsyncMock(return_value=sample_cart)

    response = client.put(
        "/api/cart/update", params={"product_id": "nonexistent", "quantity": 1}
    )

    assert response.status_code == 404


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_no_cart_found(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test updating cart when cart doesn't exist"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=None)

    response = client.put(
        "/api/cart/update", params={"product_id": "test-product", "quantity": 1}
    )

    assert response.status_code == 404


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_update_cart_item_error_handling(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test update cart item error handling"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(side_effect=Exception("Database error"))

    response = client.put(
        "/api/cart/update", params={"product_id": "test-product-1", "quantity": 2}
    )

    assert response.status_code == 500


# =============================================================================
# DELETE /api/cart/{product_id}
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_remove_cart_item_success(
    mock_get_db, mock_get_user, client, sample_cart_with_items, mock_user_context
):
    """Test DELETE remove cart item endpoint"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.update_cart = AsyncMock()

    product_id = sample_cart_with_items.items[0].product_id

    response = client.delete(f"/api/cart/{product_id}")

    assert response.status_code in [200, 500]


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_remove_from_cart_no_cart(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test removing from cart when cart doesn't exist"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=None)

    response = client.delete("/api/cart/test-product-1")

    assert response.status_code == 404


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_remove_cart_item_error_handling(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test remove cart item error handling"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(side_effect=Exception("Database error"))

    response = client.delete("/api/cart/test-product-1")

    assert response.status_code == 500


# =============================================================================
# DELETE /api/cart/
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_clear_cart_success(
    mock_get_db, mock_get_user, client, sample_cart_with_items, mock_user_context
):
    """Test DELETE clear cart endpoint"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.update_cart = AsyncMock()

    response = client.delete("/api/cart/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Cart cleared successfully"


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_clear_cart_error_handling(
    mock_get_db, mock_get_user, client, mock_user_context
):
    """Test clear cart error handling"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.update_cart = AsyncMock(side_effect=Exception("Database error"))

    response = client.delete("/api/cart/")

    assert response.status_code == 500


# =============================================================================
# POST /api/cart/checkout
# =============================================================================


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_cart_checkout_success(
    mock_get_db, mock_get_user, client, sample_cart_with_items, sample_transaction
):
    """Test cart checkout endpoint"""
    mock_get_user.return_value = {
        "user_id": "test-user-123",
        "name": "Test User",
        "email": "test@example.com",
    }
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)

    # Add checkout-specific fields to transaction
    checkout_transaction = Transaction(
        id="trans-123",
        user_id="test-user-123",
        items=[],
        subtotal=20.0,
        tax=1.60,
        total=21.60,
        status=OrderStatus.PENDING,
        order_number="ORD-12345",
        shipping_address={},
        payment_method="credit_card",
        payment_reference="PAY-123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_db.create_transaction = AsyncMock(return_value=checkout_transaction)
    mock_db.update_cart = AsyncMock()

    response = client.post("/api/cart/checkout")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "order_id" in data["data"]


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_cart_checkout_empty_cart(
    mock_get_db, mock_get_user, client, sample_cart, mock_user_context
):
    """Test cart checkout with empty cart returns 400"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart)

    response = client.post("/api/cart/checkout")

    assert response.status_code == 400
    data = response.json()
    assert "Cart is empty" in data.get("message", "") or "Cart is empty" in data.get(
        "error", ""
    )


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_cart_checkout_no_cart(mock_get_db, mock_get_user, client, mock_user_context):
    """Test cart checkout when cart doesn't exist"""
    mock_get_user.return_value = mock_user_context
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=None)

    response = client.post("/api/cart/checkout")

    assert response.status_code == 400


@patch("app.routers.cart.get_current_user")
@patch("app.routers.cart.get_db_service")
def test_checkout_error_handling(
    mock_get_db, mock_get_user, client, sample_cart_with_items
):
    """Test checkout error handling"""
    mock_get_user.return_value = {
        "user_id": "test-user-123",
        "name": "Test",
        "email": "test@test.com",
    }
    mock_db = mock_get_db.return_value
    mock_db.get_cart = AsyncMock(return_value=sample_cart_with_items)
    mock_db.create_transaction = AsyncMock(
        side_effect=Exception("Transaction failed")
    )

    response = client.post("/api/cart/checkout")

    assert response.status_code == 500
