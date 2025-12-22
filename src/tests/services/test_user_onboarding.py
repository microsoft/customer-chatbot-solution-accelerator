from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models import OrderStatus, Transaction
from app.services.user_onboarding import (SAMPLE_USER_IDS,
                                          create_demo_order_history,
                                          create_fallback_demo_orders)


@pytest.fixture
def mock_cosmos_service():
    """Mock Cosmos DB service for testing"""
    service = MagicMock()
    service.get_orders_by_customer = AsyncMock()
    service.transactions_container = MagicMock()
    service.transactions_container.create_item = MagicMock()
    return service


@pytest.fixture
def sample_order_dict():
    """Sample order data from a sample user"""
    return {
        "id": "order-sample-1",
        "user_id": "sample-user-1",
        "order_number": "ORD-SAMPLE-0001",
        "status": "delivered",
        "items": [
            {
                "product_id": "prod-001",
                "product_title": "Test Paint",
                "quantity": 2,
                "unit_price": 45.99,
                "total_price": 91.98,
            },
            {
                "product_id": "prod-002",
                "product_title": "Paint Brush",
                "quantity": 1,
                "unit_price": 15.99,
                "total_price": 15.99,
            },
        ],
        "subtotal": 107.97,
        "tax": 8.64,
        "shipping": 9.99,
        "total": 126.60,
        "shipping_address": {
            "street": "456 Sample St",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "USA",
        },
        "payment_method": "Credit Card",
        "payment_reference": "PAY-123456",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }


@pytest.fixture
def multiple_sample_orders(sample_order_dict):
    """Multiple sample orders for testing replication"""
    orders = []
    for i in range(5):
        order = sample_order_dict.copy()
        order["id"] = f"order-sample-{i+1}"
        order["order_number"] = f"ORD-SAMPLE-{i+1:04d}"
        orders.append(order)
    return orders


# ============================================================================
# Test create_demo_order_history - Main Function
# ============================================================================


@pytest.mark.asyncio
async def test_create_demo_order_history_user_has_existing_orders(mock_cosmos_service):
    """Test that demo orders are NOT created if user already has orders"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        # Mock user already has orders
        mock_cosmos_service.get_orders_by_customer.return_value = [
            {"id": "existing-order-1"}
        ]

        result = await create_demo_order_history("test-user-123")

        assert result == []
        mock_cosmos_service.get_orders_by_customer.assert_called_once_with(
            "test-user-123", limit=1
        )
        # Should NOT create any new orders
        mock_cosmos_service.transactions_container.create_item.assert_not_called()


@pytest.mark.asyncio
async def test_create_demo_order_history_success_with_sample_orders(
    mock_cosmos_service, multiple_sample_orders
):
    """Test successful demo order creation by replicating sample orders"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        # Mock: user has no orders, sample users have orders
        mock_cosmos_service.get_orders_by_customer.side_effect = [
            [],  # New user has no orders
            multiple_sample_orders[:2],  # Sample user 1
            multiple_sample_orders[2:4],  # Sample user 2
            multiple_sample_orders[4:],  # Sample user 3
        ]

        # Mock random to be predictable
        with patch("app.services.user_onboarding.random.randint", return_value=3):
            with patch(
                "app.services.user_onboarding.random.sample",
                return_value=multiple_sample_orders[:3],
            ):
                result = await create_demo_order_history("new-user-456")

        # Should have created 3 orders
        assert len(result) == 3
        assert all(isinstance(order, Transaction) for order in result)
        assert all(order.user_id == "new-user-456" for order in result)
        assert all(order.status == OrderStatus.DELIVERED for order in result)

        # Verify create_item was called 3 times
        assert (
            mock_cosmos_service.transactions_container.create_item.call_count == 3
        )  # noqa: E501


@pytest.mark.asyncio
async def test_create_demo_order_history_no_sample_orders_fallback(mock_cosmos_service):
    """Test fallback to generic demo orders when no sample orders exist"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        # Mock: no existing orders for anyone
        mock_cosmos_service.get_orders_by_customer.return_value = []

        result = await create_demo_order_history("new-user-789")

        # Should have created 3 fallback orders
        assert len(result) == 3
        assert all(isinstance(order, Transaction) for order in result)
        assert all(order.user_id == "new-user-789" for order in result)

        # Verify create_item was called 3 times
        assert (
            mock_cosmos_service.transactions_container.create_item.call_count == 3
        )  # noqa: E501


@pytest.mark.asyncio
async def test_create_demo_order_history_sample_user_error_handling(
    mock_cosmos_service, sample_order_dict
):
    """Test error handling when fetching sample user orders fails"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        # Mock: new user has no orders, sample users throw errors
        mock_cosmos_service.get_orders_by_customer.side_effect = [
            [],  # New user check
            Exception("Database error 1"),  # Sample user 1 fails
            Exception("Database error 2"),  # Sample user 2 fails
            Exception("Database error 3"),  # Sample user 3 fails
        ]

        result = await create_demo_order_history("new-user-error")

        # Should fall back to generic demo orders
        assert len(result) == 3
        assert all(order.user_id == "new-user-error" for order in result)


@pytest.mark.asyncio
async def test_create_demo_order_history_order_creation_partial_failure(
    mock_cosmos_service, multiple_sample_orders
):
    """Test that some orders succeed even if others fail"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        mock_cosmos_service.get_orders_by_customer.side_effect = [
            [],  # New user check
            multiple_sample_orders[:3],  # Sample orders
            [],
            [],
        ]

        # Mock create_item to fail on second call
        call_count = [0]

        def create_item_side_effect(item):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Cosmos DB write error")
            return item

        mock_cosmos_service.transactions_container.create_item.side_effect = (
            create_item_side_effect
        )

        with patch("app.services.user_onboarding.random.randint", return_value=3):
            with patch(
                "app.services.user_onboarding.random.sample",
                return_value=multiple_sample_orders[:3],
            ):
                result = await create_demo_order_history("partial-user")

        # Should have created 2 out of 3 orders (one failed)
        assert len(result) == 2


# ============================================================================
# Test create_fallback_demo_orders
# ============================================================================


@pytest.mark.asyncio
async def test_create_fallback_demo_orders_creates_three_orders(mock_cosmos_service):
    """Test that fallback creates exactly 3 demo orders"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        result = await create_fallback_demo_orders("fallback-user")

        assert len(result) == 3
        assert all(isinstance(order, Transaction) for order in result)
        assert all(order.user_id == "fallback-user" for order in result)


@pytest.mark.asyncio
async def test_create_fallback_demo_orders_all_delivered(mock_cosmos_service):
    """Test that all fallback orders are marked as delivered"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        result = await create_fallback_demo_orders("delivered-test")

        assert all(order.status == OrderStatus.DELIVERED for order in result)


@pytest.mark.asyncio
async def test_create_fallback_demo_orders_different_dates(mock_cosmos_service):
    """Test that fallback orders have different dates (15, 45, 90 days ago)"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        result = await create_fallback_demo_orders("date-variety")

        now = datetime.utcnow()

        # Check approximate dates
        order1_days = (now - result[0].created_at).days
        order2_days = (now - result[1].created_at).days
        order3_days = (now - result[2].created_at).days

        assert 14 <= order1_days <= 16  # ~15 days
        assert 44 <= order2_days <= 46  # ~45 days
        assert 89 <= order3_days <= 91  # ~90 days


@pytest.mark.asyncio
async def test_create_fallback_demo_orders_cosmos_error_handling(mock_cosmos_service):
    """Test error handling when Cosmos DB writes fail"""
    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        # Mock create_item to fail on second order
        call_count = [0]

        def create_item_side_effect(item):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Cosmos write failed")
            return item

        mock_cosmos_service.transactions_container.create_item.side_effect = (
            create_item_side_effect
        )

        result = await create_fallback_demo_orders("error-handling")

        # Should create 2 orders (third failed)
        assert len(result) == 2


# ============================================================================
# Test Edge Cases
# ============================================================================


@pytest.mark.asyncio
async def test_sample_user_ids_constant():
    """Test that SAMPLE_USER_IDS constant is defined correctly"""
    assert len(SAMPLE_USER_IDS) == 3
    assert "sample-user-1" in SAMPLE_USER_IDS
    assert "sample-user-2" in SAMPLE_USER_IDS
    assert "sample-user-3" in SAMPLE_USER_IDS


@pytest.mark.asyncio
async def test_create_demo_order_history_with_empty_items(mock_cosmos_service):
    """Test handling of sample orders with empty items"""
    empty_order = {
        "id": "order-empty",
        "user_id": "sample-user-1",
        "items": [],  # Empty items
        "subtotal": 0.0,
        "tax": 0.0,
        "shipping": 0.0,
        "total": 0.0,
    }

    with patch(
        "app.services.user_onboarding.get_cosmos_service",
        return_value=mock_cosmos_service,
    ):
        mock_cosmos_service.get_orders_by_customer.side_effect = [
            [],  # New user
            [empty_order],
            [],
            [],
        ]

        with patch("app.services.user_onboarding.random.randint", return_value=1):
            with patch(
                "app.services.user_onboarding.random.sample", return_value=[empty_order]
            ):
                result = await create_demo_order_history("empty-items-user")

        # Should still create order with empty items
        assert len(result) == 1
        assert len(result[0].items) == 0
