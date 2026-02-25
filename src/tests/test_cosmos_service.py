from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from app.cosmos_service import CosmosDatabaseService  # noqa: E402
from app.cosmos_service import _prepare_query_parameters


@pytest.fixture
def mock_cosmos_client():
    """Mock CosmosClient for all tests"""
    with patch("app.cosmos_service.CosmosClient") as mock_client:
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        # Mock database and containers
        mock_db = MagicMock()
        mock_instance.get_database_client.return_value = mock_db
        mock_instance.create_database_if_not_exists.return_value = mock_db

        # Mock containers
        mock_products = MagicMock()
        mock_users = MagicMock()
        mock_chat = MagicMock()
        mock_cart = MagicMock()
        mock_transactions = MagicMock()

        mock_db.create_container_if_not_exists.side_effect = [
            mock_products,
            mock_users,
            mock_chat,
            mock_cart,
            mock_transactions,
        ]

        yield {
            "client": mock_instance,
            "database": mock_db,
            "products": mock_products,
            "users": mock_users,
            "chat": mock_chat,
            "cart": mock_cart,
            "transactions": mock_transactions,
        }


@pytest.fixture
def mock_settings():
    """Mock settings for Cosmos DB configuration"""
    with patch("app.cosmos_service.settings") as mock_settings:
        mock_settings.cosmos_db_endpoint = (
            "https://test-cosmos.documents.azure.com:443/"
        )
        mock_settings.cosmos_db_database_name = "test-db"
        mock_settings.cosmos_db_containers = {
            "products": "products",
            "users": "users",
            "chat_sessions": "chat_sessions",
            "carts": "carts",
            "transactions": "transactions",
        }
        mock_settings.azure_client_id = "test-client-id"
        mock_settings.azure_client_secret = "test-secret"
        mock_settings.azure_tenant_id = "test-tenant-id"
        yield mock_settings


@pytest.fixture
def sample_product_dict():
    """Sample product data as dictionary"""
    return {
        "id": "prod-123",
        "title": "Test Product",
        "price": 99.99,
        "original_price": 129.99,
        "rating": 4.5,
        "review_count": 100,
        "image": "https://example.com/image.jpg",
        "category": "Electronics",
        "in_stock": True,
        "description": "A great test product",
        "tags": ["test", "electronics"],
        "specifications": {"color": "blue"},
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }


@pytest.fixture
def cosmos_service(mock_cosmos_client, mock_settings):
    """Initialized CosmosDatabaseService with mocked dependencies"""
    with patch("app.cosmos_service.get_azure_credential") as mock_get_cred:
        mock_get_cred.return_value = MagicMock()
        service = CosmosDatabaseService()
        service.products_container = mock_cosmos_client["products"]
        service.users_container = mock_cosmos_client["users"]
        service.chat_container = mock_cosmos_client["chat"]
        service.cart_container = mock_cosmos_client["cart"]
        service.transactions_container = mock_cosmos_client["transactions"]
        return service


# ============================================================================
# Test Helper Functions
# ============================================================================


def test_prepare_query_parameters():
    """Test query parameter preparation helper function"""
    params = [
        {"name": "@category", "value": "electronics"},
        {"name": "@min_price", "value": 10.0},
        {"name": "@max_price", "value": 100.0},
    ]

    result = _prepare_query_parameters(params)

    assert len(result) == 3
    assert result[0] == {"name": "@category", "value": "electronics"}
    assert result[1] == {"name": "@min_price", "value": 10.0}
    assert result[2] == {"name": "@max_price", "value": 100.0}

# ============================================================================
# Test Initialization and Authentication
# ============================================================================


def test_cosmos_init_with_client_secret(mock_cosmos_client, mock_settings):
    """Test initialization with get_azure_credential"""
    with patch("app.cosmos_service.get_azure_credential") as mock_get_cred:
        mock_get_cred.return_value = MagicMock()
        service = CosmosDatabaseService()

        assert service.client is not None
        mock_get_cred.assert_called_once()


def test_cosmos_init_with_default_credential(mock_cosmos_client, mock_settings):
    """Test initialization with get_azure_credential when no client credentials"""
    # Remove client credentials - credential utility handles this internally
    mock_settings.azure_client_id = None
    mock_settings.azure_client_secret = None
    mock_settings.azure_tenant_id = None

    with patch("app.cosmos_service.get_azure_credential") as mock_get_cred:
        mock_get_cred.return_value = MagicMock()
        service = CosmosDatabaseService()

        assert service.client is not None
        mock_get_cred.assert_called_once()


def test_cosmos_init_missing_endpoint(mock_cosmos_client, mock_settings):
    """Negative test: Missing Cosmos DB endpoint"""
    mock_settings.cosmos_db_endpoint = None

    with pytest.raises(Exception, match="Cosmos DB endpoint is required"):
        CosmosDatabaseService()


def test_cosmos_init_generic_auth_error(mock_settings):
    """Negative test: Generic authentication error"""
    with patch("app.cosmos_service.get_azure_credential") as mock_get_cred:
        mock_get_cred.side_effect = Exception("Unknown authentication error")

        with pytest.raises(Exception, match="Cannot authenticate to Cosmos DB"):
            CosmosDatabaseService()


# ============================================================================
# Test Serialization/Deserialization
# ============================================================================


class TestCosmosDatabaseServiceMethods:
    """Test individual methods of CosmosDatabaseService"""

    def test_serialize_datetime_fields(self):
        """Test datetime serialization for Cosmos DB"""
        # Mock the service without initialization
        service = Mock(spec=CosmosDatabaseService)
        method = CosmosDatabaseService._serialize_datetime_fields
        service._serialize_datetime_fields = method.__get__(service)

        # Test data with datetime
        test_datetime = datetime(2023, 12, 17, 10, 30, 45)
        data = {
            "id": "test-123",
            "name": "Test Product",
            "created_at": test_datetime,
            "updated_at": test_datetime,
            "price": 99.99,
        }

        result = service._serialize_datetime_fields(data)

        assert result["id"] == "test-123"
        assert result["name"] == "Test Product"
        assert result["price"] == 99.99
        assert result["created_at"] == "2023-12-17T10:30:45Z"
        assert result["updated_at"] == "2023-12-17T10:30:45Z"

    def test_serialize_datetime_fields_with_timezone(self):
        """Test datetime serialization with timezone info"""
        service = Mock(spec=CosmosDatabaseService)
        service._serialize_datetime_fields = (
            CosmosDatabaseService._serialize_datetime_fields.__get__(service)
        )

        # Test with timezone-aware datetime
        test_datetime = datetime(2023, 12, 17, 10, 30, 45, tzinfo=timezone.utc)
        data = {"created_at": test_datetime}

        result = service._serialize_datetime_fields(data)

        assert result["created_at"] == "2023-12-17T10:30:45+00:00"

    def test_deserialize_datetime_fields(self):
        """Test datetime deserialization from Cosmos DB"""
        service = Mock(spec=CosmosDatabaseService)
        service._deserialize_datetime_fields = (
            CosmosDatabaseService._deserialize_datetime_fields.__get__(service)
        )

        # Test data with ISO string datetimes
        data = {
            "id": "test-123",
            "name": "Test Product",
            "created_at": "2023-12-17T10:30:45Z",
            "updated_at": "2023-12-17T10:30:45+00:00",
            "price": 99.99,
            "last_login": "2023-12-17T15:20:10Z",
        }

        result = service._deserialize_datetime_fields(data)

        assert result["id"] == "test-123"
        assert result["name"] == "Test Product"
        assert result["price"] == 99.99
        assert isinstance(result["created_at"], datetime)
        assert isinstance(result["updated_at"], datetime)
        assert isinstance(result["last_login"], datetime)

    def test_deserialize_datetime_fields_no_datetime(self):
        """Test deserialization with no datetime fields"""
        service = Mock(spec=CosmosDatabaseService)
        service._deserialize_datetime_fields = (
            CosmosDatabaseService._deserialize_datetime_fields.__get__(service)
        )

        data = {"id": "test-123", "name": "Test Product", "price": 99.99}

        result = service._deserialize_datetime_fields(data)

        assert result == data

    def test_deserialize_datetime_fields_invalid_format(self):
        """Test deserialization with invalid datetime format"""
        service = Mock(spec=CosmosDatabaseService)
        service._deserialize_datetime_fields = (
            CosmosDatabaseService._deserialize_datetime_fields.__get__(service)
        )

        data = {"created_at": "invalid-date-format"}

        # This should raise ValueError for invalid format
        with pytest.raises(ValueError):
            service._deserialize_datetime_fields(data)


@patch("app.cosmos_service.settings")
@patch("app.cosmos_service.CosmosClient")
@patch("app.cosmos_service.get_azure_credential")
def test_cosmos_service_initialization_success(
    mock_get_credential, mock_client, mock_settings
):
    """Test successful Cosmos DB service initialization"""
    # Mock settings
    mock_settings.cosmos_db_endpoint = "https://test-cosmos.documents.azure.com:443/"
    mock_settings.cosmos_db_database_name = "test-db"
    mock_settings.cosmos_db_containers = {
        "products": "products",
        "users": "users",
        "chat_sessions": "chat_sessions",
        "carts": "carts",
        "transactions": "transactions",
    }
    mock_settings.azure_client_id = None
    mock_settings.azure_client_secret = None
    mock_settings.azure_tenant_id = None

    # Mock credential and client
    mock_cred_instance = Mock()
    mock_get_credential.return_value = mock_cred_instance

    mock_client_instance = Mock()
    mock_client.return_value = mock_client_instance

    mock_database = Mock()
    mock_client_instance.get_database_client.return_value = mock_database

    # Mock container creation
    mock_container = Mock()
    mock_database.create_container_if_not_exists.return_value = mock_container

    # Mock create_database_if_not_exists to return the same mock_database
    mock_client_instance.create_database_if_not_exists.return_value = mock_database

    # Initialize service
    service = CosmosDatabaseService()

    # Verify initialization
    assert service.client == mock_client_instance
    # The database is set by create_database_if_not_exists in _initialize_containers
    assert service.database == mock_database
    mock_client.assert_called_once_with(
        "https://test-cosmos.documents.azure.com:443/", credential=mock_cred_instance
    )


@patch("app.cosmos_service.settings")
def test_cosmos_service_initialization_no_endpoint(mock_settings):
    """Test Cosmos DB service initialization with missing endpoint"""
    mock_settings.cosmos_db_endpoint = None

    with pytest.raises(Exception) as exc_info:
        CosmosDatabaseService()

    assert "Cosmos DB endpoint is required" in str(exc_info.value)


@patch("app.cosmos_service.settings")
@patch("app.cosmos_service.CosmosClient")
@patch("app.cosmos_service.get_azure_credential")
def test_cosmos_service_initialization_auth_failure(
    mock_get_credential, mock_client, mock_settings
):
    """Test Cosmos DB service initialization with authentication failure"""
    # Mock settings
    mock_settings.cosmos_db_endpoint = "https://test-cosmos.documents.azure.com:443/"
    mock_settings.azure_client_id = None
    mock_settings.azure_client_secret = None
    mock_settings.azure_tenant_id = None

    # Mock authentication failure
    mock_client.side_effect = Exception("Authentication failed")

    with pytest.raises(Exception) as exc_info:
        CosmosDatabaseService()

    assert "Cannot authenticate to Cosmos DB" in str(exc_info.value)


def test_cosmos_service_datetime_serialization_edge_cases():
    """Test edge cases in datetime serialization"""
    service = Mock(spec=CosmosDatabaseService)
    method = CosmosDatabaseService._serialize_datetime_fields
    service._serialize_datetime_fields = method.__get__(service)

    # Test with None values
    data = {"created_at": None, "name": "Test"}
    result = service._serialize_datetime_fields(data)
    assert result["created_at"] is None
    assert result["name"] == "Test"

    # Test with nested dict (should not affect nested values)
    nested_data = {
        "created_at": datetime(2023, 12, 17),
        "metadata": {"updated_at": datetime(2023, 12, 18)},
    }
    result = service._serialize_datetime_fields(nested_data)
    assert "Z" in result["created_at"]
    # Nested datetime should remain unchanged
    assert isinstance(result["metadata"]["updated_at"], datetime)


# ============================================================================
# Test Product Operations with Mocking
# ============================================================================


@pytest.mark.asyncio
async def test_get_products_no_filters(cosmos_service, sample_product_dict):
    """Test get_products without filters"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]

    products = await cosmos_service.get_products()

    assert len(products) == 1
    assert products[0].id == "prod-123"
    assert products[0].title == "Test Product"


@pytest.mark.asyncio
async def test_get_products_with_category_filter(cosmos_service, sample_product_dict):
    """Test get_products with category filter"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]

    products = await cosmos_service.get_products({"category": "Electronics"})

    assert len(products) == 1
    cosmos_service.products_container.query_items.assert_called_once()


@pytest.mark.asyncio
async def test_get_products_with_all_filters(cosmos_service, sample_product_dict):
    """Test get_products with multiple filters combined"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]

    products = await cosmos_service.get_products(
        {
            "category": "Electronics",
            "min_price": 50.0,
            "max_price": 150.0,
            "min_rating": 4.0,
            "in_stock_only": True,
            "query": "test",
            "sort_by": "price",
            "sort_order": "desc",
        }
    )

    assert len(products) == 1


@pytest.mark.asyncio
async def test_get_products_error_handling(cosmos_service):
    """Negative test: get_products error handling"""
    error_msg = "Database connection error"
    cosmos_service.products_container.query_items.side_effect = Exception(error_msg)

    with pytest.raises(Exception, match=error_msg):
        await cosmos_service.get_products()


@pytest.mark.asyncio
async def test_get_product_found(cosmos_service, sample_product_dict):
    """Test get_product successfully finds a product"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]

    product = await cosmos_service.get_product("prod-123")

    assert product is not None
    assert product.id == "prod-123"
    assert product.title == "Test Product"


@pytest.mark.asyncio
async def test_get_product_not_found(cosmos_service):
    """Negative test: get_product returns None when not found"""
    cosmos_service.products_container.query_items.return_value = []

    product = await cosmos_service.get_product("non-existent")

    assert product is None


@pytest.mark.asyncio
async def test_get_product_by_sku_found(cosmos_service, sample_product_dict):
    """Test get_product_by_sku successfully finds product"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]

    product = await cosmos_service.get_product_by_sku("SKU-123")

    assert product is not None
    assert product.id == "prod-123"


@pytest.mark.asyncio
async def test_get_product_by_sku_error(cosmos_service):
    """Negative test: get_product_by_sku handles errors gracefully"""
    cosmos_service.products_container.query_items.side_effect = Exception("Query error")

    product = await cosmos_service.get_product_by_sku("SKU-123")

    assert product is None  # Should return None on error


@pytest.mark.asyncio
async def test_search_products_basic(cosmos_service, sample_product_dict):
    """Test basic search_products"""
    cosmos_service.products_container.query_items.return_value = [
        sample_product_dict
    ] * 5

    products = await cosmos_service.search_products("test", limit=3)

    assert len(products) == 3


@pytest.mark.asyncio
async def test_search_products_hybrid_fallback(cosmos_service, sample_product_dict):
    """Test search_products_hybrid falls back to enhanced search"""
    # Mock AI Search to fail
    with patch.dict(
        "sys.modules", {"services.search": MagicMock(side_effect=ImportError())}
    ):
        cosmos_service.products_container.query_items.return_value = [
            sample_product_dict
        ]

        products = await cosmos_service.search_products_hybrid("test query")

        # Should fall back and still return results
        assert isinstance(products, list)


@pytest.mark.asyncio
async def test_search_products_ai_search_error(cosmos_service):
    """Negative test: search_products_ai_search error handling"""
    with patch.dict(
        "sys.modules", {"services.search": MagicMock(side_effect=Exception("AI error"))}
    ):
        products = await cosmos_service.search_products_ai_search("test")

        assert products == []  # Should return empty list on error


@pytest.mark.asyncio
async def test_get_products_by_category(cosmos_service, sample_product_dict):
    """Test get_products_by_category"""
    cosmos_service.products_container.query_items.return_value = [
        sample_product_dict
    ] * 15

    products = await cosmos_service.get_products_by_category("Electronics", limit=10)

    assert len(products) == 10


# ============================================================================
# Test Order Operations with Mocking
# ============================================================================


@pytest.mark.asyncio
async def test_get_order_by_id_found(cosmos_service):
    """Test get_order_by_id successfully finds order"""
    order_dict = {"id": "order-123", "user_id": "user-1", "items": [], "total": 100.0}
    cosmos_service.transactions_container.query_items.return_value = [order_dict]

    order = await cosmos_service.get_order_by_id("order-123")

    assert order is not None
    assert order["id"] == "order-123"


@pytest.mark.asyncio
async def test_get_order_by_id_not_found(cosmos_service):
    """Negative test: get_order_by_id returns None when not found"""
    cosmos_service.transactions_container.query_items.return_value = []

    order = await cosmos_service.get_order_by_id("non-existent")

    assert order is None


@pytest.mark.asyncio
async def test_get_order_by_id_error(cosmos_service):
    """Negative test: get_order_by_id error handling"""
    cosmos_service.transactions_container.query_items.side_effect = Exception(
        "Query failed"
    )

    order = await cosmos_service.get_order_by_id("order-123")

    assert order is None  # Should return None on error


@pytest.mark.asyncio
async def test_get_orders_by_customer(cosmos_service):
    """Test get_orders_by_customer"""
    orders = [{"id": f"order-{i}", "user_id": "user-1"} for i in range(5)]
    cosmos_service.transactions_container.query_items.return_value = orders

    result = await cosmos_service.get_orders_by_customer("user-1", limit=3)

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_orders_by_customer_error(cosmos_service):
    """Negative test: get_orders_by_customer error handling"""
    cosmos_service.transactions_container.query_items.side_effect = Exception(
        "Query error"
    )

    result = await cosmos_service.get_orders_by_customer("user-1")

    assert result == []  # Should return empty list on error


# ============================================================================
# Cart Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_cart_success(cosmos_service):
    """Test get_cart returns cart successfully"""
    cart_data = {
        "id": "user-123",
        "user_id": "user-123",
        "items": [
            {
                "product_id": "prod-1",
                "product_title": "Product 1",
                "product_price": 19.99,
                "product_image": "https://example.com/image.jpg",
                "quantity": 2,
                "added_at": "2024-01-01T00:00:00Z",
            }
        ],
        "total_items": 1,
        "total_price": 39.98,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
    }

    cosmos_service.cart_container.query_items.return_value = [cart_data]

    cart = await cosmos_service.get_cart("user-123")

    assert cart is not None
    assert cart.user_id == "user-123"
    assert len(cart.items) == 1
    assert cart.total_price == 39.98
    assert cart.total_items == 1


@pytest.mark.asyncio
async def test_get_cart_not_found(cosmos_service):
    """Test get_cart returns None when cart doesn't exist"""
    cosmos_service.cart_container.query_items.return_value = []

    cart = await cosmos_service.get_cart("non-existent-user")

    assert cart is None


@pytest.mark.asyncio
async def test_get_cart_error_handling(cosmos_service):
    """Test get_cart error handling"""
    cosmos_service.cart_container.query_items.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        await cosmos_service.get_cart("user-123")


@pytest.mark.asyncio
async def test_update_cart_success(cosmos_service):
    """Test update_cart successfully updates cart"""
    from app.models import Cart, CartItem

    cart = Cart(
        id="user-123",
        user_id="user-123",
        items=[
            CartItem(
                product_id="prod-1",
                product_title="Product 1",
                product_price=29.99,
                product_image="https://example.com/image.jpg",
                quantity=1,
                added_at=datetime(2024, 1, 1),
            )
        ],
        total_items=1,
        total_price=29.99,
    )

    cosmos_service.cart_container.upsert_item.return_value = None

    updated_cart = await cosmos_service.update_cart("user-123", cart)

    assert updated_cart.user_id == "user-123"
    assert updated_cart.id == "user-123"
    cosmos_service.cart_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_cart_error_handling(cosmos_service):
    """Test update_cart error handling"""
    from app.models import Cart

    cart = Cart(
        id="user-123", user_id="user-123", items=[], total_items=0, total_price=0
    )

    cosmos_service.cart_container.upsert_item.side_effect = Exception("Upsert failed")

    with pytest.raises(Exception, match="Upsert failed"):
        await cosmos_service.update_cart("user-123", cart)


# ============================================================================
# Chat Session Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_chat_session_success(cosmos_service):
    """Test get_chat_session returns session successfully"""
    session_data = {
        "id": "session-123",
        "user_id": "user-123",
        "session_name": "Test Chat",
        "messages": [
            {
                "id": "msg-1",
                "session_id": "session-123",
                "message_type": "user",
                "content": "Hello",
                "created_at": "2024-01-01T00:00:00Z",
            }
        ],
        "message_count": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_message_at": "2024-01-01T00:00:00Z",
        "context": {},
        "is_active": True,
    }

    cosmos_service.chat_container.query_items.return_value = [session_data]

    session = await cosmos_service.get_chat_session("session-123")

    assert session is not None
    assert session.id == "session-123"
    assert session.user_id == "user-123"
    assert session.message_count == 1
    assert len(session.messages) == 1


@pytest.mark.asyncio
async def test_get_chat_session_not_found(cosmos_service):
    """Test get_chat_session returns None when session doesn't exist"""
    cosmos_service.chat_container.query_items.return_value = []

    session = await cosmos_service.get_chat_session("non-existent")

    assert session is None


@pytest.mark.asyncio
async def test_get_chat_session_error_handling(cosmos_service):
    """Test get_chat_session error handling"""
    cosmos_service.chat_container.query_items.side_effect = Exception("Query failed")

    with pytest.raises(Exception, match="Query failed"):
        await cosmos_service.get_chat_session("session-123")


@pytest.mark.asyncio
async def test_get_chat_sessions_by_user_success(cosmos_service):
    """Test get_chat_sessions_by_user returns all user sessions"""
    sessions_data = [
        {
            "id": f"session-{i}",
            "user_id": "user-123",
            "session_name": f"Chat {i}",
            "messages": [],
            "message_count": 0,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "last_message_at": "2024-01-01T00:00:00Z",
            "context": {},
            "is_active": True,
        }
        for i in range(3)
    ]

    cosmos_service.chat_container.query_items.return_value = sessions_data

    sessions = await cosmos_service.get_chat_sessions_by_user("user-123")

    assert len(sessions) == 3
    assert all(s.user_id == "user-123" for s in sessions)


@pytest.mark.asyncio
async def test_get_chat_sessions_by_user_error_handling(cosmos_service):
    """Test get_chat_sessions_by_user error handling"""
    cosmos_service.chat_container.query_items.side_effect = Exception("Query error")

    with pytest.raises(Exception, match="Query error"):
        await cosmos_service.get_chat_sessions_by_user("user-123")


@pytest.mark.asyncio
async def test_create_chat_session_success(cosmos_service):
    """Test create_chat_session creates new session"""
    from app.models import ChatSessionCreate

    session_create = ChatSessionCreate(
        user_id="user-123", session_name="New Chat", context={"key": "value"}
    )

    cosmos_service.chat_container.create_item.return_value = None

    session = await cosmos_service.create_chat_session(session_create)

    assert session.user_id == "user-123"
    assert session.session_name == "New Chat"
    assert session.message_count == 0
    assert len(session.messages) == 0
    cosmos_service.chat_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_create_chat_session_default_name(cosmos_service):
    """Test create_chat_session with default session name"""
    from app.models import ChatSessionCreate

    session_create = ChatSessionCreate(
        user_id="user-123", session_name=None, context={}
    )

    cosmos_service.chat_container.create_item.return_value = None

    session = await cosmos_service.create_chat_session(session_create)

    assert session.user_id == "user-123"
    assert "Chat" in session.session_name  # Default name includes "Chat"
    assert session.message_count == 0


@pytest.mark.asyncio
async def test_create_chat_session_error_handling(cosmos_service):
    """Test create_chat_session error handling"""
    from app.models import ChatSessionCreate

    session_create = ChatSessionCreate(user_id="user-123", session_name="Test")

    cosmos_service.chat_container.create_item.side_effect = Exception("Create failed")

    with pytest.raises(Exception, match="Create failed"):
        await cosmos_service.create_chat_session(session_create)


@pytest.mark.asyncio
async def test_update_chat_session_success(cosmos_service):
    """Test update_chat_session updates session successfully"""
    from app.models import ChatSession, ChatSessionUpdate

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Old Name",
        messages=[],
        message_count=0,
        context={},
        is_active=True,
    )

    # Mock get_chat_session to return existing session
    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.upsert_item.return_value = None

    session_update = ChatSessionUpdate(session_name="New Name", is_active=False)

    updated_session = await cosmos_service.update_chat_session(
        "session-123", session_update
    )

    assert updated_session is not None
    assert updated_session.session_name == "New Name"
    assert updated_session.is_active is False
    cosmos_service.chat_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_chat_session_not_found(cosmos_service):
    """Test update_chat_session returns None when session doesn't exist"""
    from app.models import ChatSessionUpdate

    # Mock get_chat_session to return None
    cosmos_service.chat_container.query_items.return_value = []

    session_update = ChatSessionUpdate(session_name="New Name")

    result = await cosmos_service.update_chat_session("non-existent", session_update)

    assert result is None


@pytest.mark.asyncio
async def test_update_chat_session_error_handling(cosmos_service):
    """Test update_chat_session error handling"""
    from app.models import ChatSession, ChatSessionUpdate

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.upsert_item.side_effect = Exception("Update failed")

    session_update = ChatSessionUpdate(session_name="New Name")

    with pytest.raises(Exception, match="Update failed"):
        await cosmos_service.update_chat_session("session-123", session_update)


@pytest.mark.asyncio
async def test_delete_chat_session_success(cosmos_service):
    """Test delete_chat_session deletes session successfully"""
    from app.models import ChatSession

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    # Mock get_chat_session to return existing session
    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.delete_item.return_value = None

    result = await cosmos_service.delete_chat_session("session-123")

    assert result is True
    cosmos_service.chat_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_chat_session_not_found(cosmos_service):
    """Test delete_chat_session returns False when session doesn't exist"""
    # Mock get_chat_session to return None
    cosmos_service.chat_container.query_items.return_value = []

    result = await cosmos_service.delete_chat_session("non-existent")

    assert result is False


@pytest.mark.asyncio
async def test_delete_chat_session_error_handling(cosmos_service):
    """Test delete_chat_session error handling"""
    from app.models import ChatSession

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.delete_item.side_effect = Exception("Delete failed")

    with pytest.raises(Exception, match="Delete failed"):
        await cosmos_service.delete_chat_session("session-123")


@pytest.mark.asyncio
async def test_get_chat_messages_success(cosmos_service):
    """Test get_chat_messages returns messages from session"""
    from app.models import ChatMessage, ChatMessageType

    messages = [
        ChatMessage(
            id=f"msg-{i}",
            content=f"Message {i}",
            message_type=ChatMessageType.USER,
            metadata={},
        )
        for i in range(3)
    ]

    session_data = {
        "id": "session-123",
        "user_id": "user-123",
        "session_name": "Test",
        "messages": [m.model_dump() for m in messages],
        "message_count": 3,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_message_at": "2024-01-01T00:00:00Z",
        "context": {},
        "is_active": True,
    }

    cosmos_service.chat_container.query_items.return_value = [session_data]

    result = await cosmos_service.get_chat_messages("session-123")

    assert len(result) == 3


@pytest.mark.asyncio
async def test_get_chat_messages_session_not_found(cosmos_service):
    """Test get_chat_messages returns empty list when session doesn't exist"""
    cosmos_service.chat_container.query_items.return_value = []

    result = await cosmos_service.get_chat_messages("non-existent")

    assert result == []


@pytest.mark.asyncio
async def test_get_chat_messages_error_handling(cosmos_service):
    """Test get_chat_messages error handling"""
    cosmos_service.chat_container.query_items.side_effect = Exception("Query failed")

    result = await cosmos_service.get_chat_messages("session-123")

    assert result == []  # Should return empty list on error


@pytest.mark.asyncio
async def test_create_transaction_success(cosmos_service):
    """Test create_transaction creates transaction successfully"""
    from app.models import TransactionCreate, TransactionItem

    transaction_create = TransactionCreate(
        items=[
            TransactionItem(
                product_id="prod-1",
                product_title="Product 1",
                unit_price=20.00,
                quantity=2,
                total_price=40.00,
            )
        ],
        shipping_address={
            "street": "123 Main St",
            "city": "City",
            "state": "State",
            "postal_code": "12345",
            "country": "Country",
        },
        payment_method="CREDIT_CARD",
        payment_reference="ref-123",
    )

    cosmos_service.transactions_container.create_item.return_value = None

    transaction = await cosmos_service.create_transaction(
        transaction_create, "user-123"
    )

    assert transaction.user_id == "user-123"
    assert transaction.subtotal == 40.00
    assert transaction.tax > 0
    assert transaction.total > 40.00
    assert transaction.order_number.startswith("ORD-")
    cosmos_service.transactions_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_create_transaction_error_handling(cosmos_service):
    """Test create_transaction error handling"""
    from app.models import TransactionCreate, TransactionItem

    transaction_create = TransactionCreate(
        items=[
            TransactionItem(
                product_id="prod-1",
                product_title="Product 1",
                unit_price=20.00,
                quantity=1,
                total_price=20.00,
            )
        ],
        shipping_address={
            "street": "123 Main St",
            "city": "City",
            "state": "State",
            "postal_code": "12345",
            "country": "Country",
        },
        payment_method="CREDIT_CARD",
    )

    cosmos_service.transactions_container.create_item.side_effect = Exception(
        "Create failed"
    )

    with pytest.raises(Exception, match="Create failed"):
        await cosmos_service.create_transaction(transaction_create, "user-123")


@pytest.mark.asyncio
async def test_get_products_with_sorting(cosmos_service):
    """Test get_products with different sort options"""
    products_data = [
        {"id": f"prod-{i}", "title": f"Product {i}", "price": 10.0 * i}
        for i in range(3)
    ]
    cosmos_service.products_container.query_items.return_value = products_data

    # Test sort by price desc
    search_params = {"sort_by": "price", "sort_order": "desc"}
    products = await cosmos_service.get_products(search_params)

    assert len(products) == 3


@pytest.mark.asyncio
async def test_get_products_with_filters(cosmos_service):
    """Test get_products with multiple filters"""
    products_data = [
        {
            "id": "prod-1",
            "title": "Test Product",
            "price": 50.0,
            "category": "Electronics",
        }
    ]
    cosmos_service.products_container.query_items.return_value = products_data

    search_params = {
        "category": "Electronics",
        "min_price": 40.0,
        "max_price": 60.0,
        "min_rating": 4.0,
        "in_stock_only": True,
        "query": "Test",
    }
    products = await cosmos_service.get_products(search_params)

    assert len(products) == 1


@pytest.mark.asyncio
async def test_get_orders_in_date_range_success(cosmos_service):
    """Test get_orders_in_date_range returns orders within date range"""
    orders_data = [
        {
            "id": f"order-{i}",
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
        }
        for i in range(2)
    ]
    cosmos_service.transactions_container.query_items.return_value = orders_data

    orders = await cosmos_service.get_orders_in_date_range("user-123", days=180)

    assert len(orders) == 2


@pytest.mark.asyncio
async def test_get_orders_in_date_range_error(cosmos_service):
    """Test get_orders_in_date_range error handling"""
    cosmos_service.transactions_container.query_items.side_effect = Exception(
        "Query error"
    )

    orders = await cosmos_service.get_orders_in_date_range("user-123")

    assert orders == []


@pytest.mark.asyncio
async def test_add_message_to_session_success(cosmos_service):
    """Test add_message_to_session adds message to existing session"""
    from app.models import ChatMessageCreate, ChatMessageType, ChatSession

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.upsert_item.return_value = None

    message_create = ChatMessageCreate(
        session_id="session-123", content="Hello", message_type=ChatMessageType.USER
    )

    # Mock the refetch of updated session
    updated_session = existing_session
    updated_session.message_count = 1
    cosmos_service.chat_container.query_items.side_effect = [
        [existing_session.model_dump()],  # First call: get existing session
        [updated_session.model_dump()],  # Second call: refetch updated session
    ]

    result = await cosmos_service.add_message_to_session("session-123", message_create)

    assert result is not None
    assert result.id == "session-123"
    cosmos_service.chat_container.upsert_item.assert_called_once()


@pytest.mark.asyncio
async def test_add_message_to_session_not_found(cosmos_service):
    """Test add_message_to_session returns False when session not found"""
    from app.models import ChatMessageCreate, ChatMessageType

    # When session not found, it creates a new one
    new_session_data = {
        "id": "non-existent",
        "user_id": "user-123",
        "session_name": "Chat",
        "messages": [{"content": "Hello", "message_type": "user"}],
        "message_count": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "last_message_at": "2024-01-01T00:00:00Z",
        "context": {},
        "is_active": True,
    }
    cosmos_service.chat_container.query_items.side_effect = [
        [],  # First call: session not found
        [new_session_data],  # Second call: refetch new session
    ]
    cosmos_service.chat_container.create_item.return_value = None
    cosmos_service.chat_container.upsert_item.return_value = None

    message_create = ChatMessageCreate(
        session_id="non-existent", content="Hello", message_type=ChatMessageType.USER
    )

    result = await cosmos_service.add_message_to_session(
        "non-existent", message_create, "user-123"
    )

    assert result is not None
    assert result.id == "non-existent"


@pytest.mark.asyncio
async def test_add_message_to_session_error_handling(cosmos_service):
    """Test add_message_to_session error handling"""
    from app.models import ChatMessageCreate, ChatMessageType, ChatSession

    existing_session = ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.upsert_item.side_effect = Exception("Update failed")

    message_create = ChatMessageCreate(
        session_id="session-123", content="Hello", message_type=ChatMessageType.USER
    )

    with pytest.raises(Exception, match="Update failed"):
        await cosmos_service.add_message_to_session("session-123", message_create)


@pytest.mark.asyncio
async def test_create_chat_message_success(cosmos_service):
    """Test create_chat_message creates message and adds to session"""
    from app.models import ChatMessageCreate, ChatMessageType, ChatSession

    existing_session = ChatSession(
        id="default",
        user_id="user-123",
        session_name="Test",
        messages=[],
        message_count=0,
    )

    cosmos_service.chat_container.query_items.return_value = [
        existing_session.model_dump()
    ]
    cosmos_service.chat_container.upsert_item.return_value = None

    message_create = ChatMessageCreate(
        session_id="default", content="Hello", message_type=ChatMessageType.USER
    )

    message = await cosmos_service.create_chat_message(message_create)

    assert message.content == "Hello"
    assert message.message_type == ChatMessageType.USER


@pytest.mark.asyncio
async def test_create_chat_message_error_handling(cosmos_service):
    """Test create_chat_message error handling"""
    from app.models import ChatMessageCreate, ChatMessageType

    cosmos_service.chat_container.query_items.side_effect = Exception("Query failed")

    message_create = ChatMessageCreate(
        session_id="default", content="Hello", message_type=ChatMessageType.USER
    )

    with pytest.raises(Exception, match="Query failed"):
        await cosmos_service.create_chat_message(message_create)


# ============================================================================
# Test Product Create/Update/Delete Operations
# ============================================================================


@pytest.mark.asyncio
async def test_create_product_success(cosmos_service):
    """Test create_product successfully creates a product"""
    from app.models import ProductCreate

    cosmos_service.products_container.create_item.return_value = None

    product_create = ProductCreate(
        title="New Product",
        price=49.99,
        original_price=59.99,
        category="Electronics",
        description="A new test product",
        image="https://example.com/new.jpg",
    )

    product = await cosmos_service.create_product(product_create)

    assert product.title == "New Product"
    assert product.price == 49.99
    assert product.category == "Electronics"
    cosmos_service.products_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_create_product_error_handling(cosmos_service):
    """Test create_product error handling"""
    from app.models import ProductCreate

    cosmos_service.products_container.create_item.side_effect = Exception(
        "Create failed"
    )

    product_create = ProductCreate(
        title="New Product",
        price=49.99,
        category="Electronics",
        image="https://example.com/error.jpg",
    )

    with pytest.raises(Exception, match="Create failed"):
        await cosmos_service.create_product(product_create)


@pytest.mark.asyncio
async def test_update_product_success(cosmos_service, sample_product_dict):
    """Test update_product successfully updates a product"""
    from app.models import ProductUpdate

    cosmos_service.products_container.query_items.return_value = [sample_product_dict]
    cosmos_service.products_container.replace_item.return_value = None

    product_update = ProductUpdate(title="Updated Product", price=79.99)

    product = await cosmos_service.update_product("prod-123", product_update)

    assert product is not None
    assert product.title == "Updated Product"
    assert product.price == 79.99
    cosmos_service.products_container.replace_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_product_not_found(cosmos_service):
    """Test update_product returns None when product not found"""
    from app.models import ProductUpdate

    cosmos_service.products_container.query_items.return_value = []

    product_update = ProductUpdate(title="Updated Product")

    product = await cosmos_service.update_product("nonexistent-id", product_update)

    assert product is None


@pytest.mark.asyncio
async def test_update_product_error_handling(cosmos_service, sample_product_dict):
    """Test update_product error handling"""
    from app.models import ProductUpdate

    cosmos_service.products_container.query_items.return_value = [sample_product_dict]
    cosmos_service.products_container.replace_item.side_effect = Exception(
        "Update failed"
    )

    product_update = ProductUpdate(title="Updated Product")

    with pytest.raises(Exception, match="Update failed"):
        await cosmos_service.update_product("prod-123", product_update)


@pytest.mark.asyncio
async def test_delete_product_success(cosmos_service, sample_product_dict):
    """Test delete_product successfully deletes a product"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]
    cosmos_service.products_container.delete_item.return_value = None

    result = await cosmos_service.delete_product("prod-123")

    assert result is True
    cosmos_service.products_container.delete_item.assert_called_once()


@pytest.mark.asyncio
async def test_delete_product_not_found(cosmos_service):
    """Test delete_product returns False when product not found"""
    cosmos_service.products_container.query_items.return_value = []

    result = await cosmos_service.delete_product("nonexistent-id")

    assert result is False


@pytest.mark.asyncio
async def test_delete_product_error_handling(cosmos_service, sample_product_dict):
    """Test delete_product error handling"""
    cosmos_service.products_container.query_items.return_value = [sample_product_dict]
    cosmos_service.products_container.delete_item.side_effect = Exception(
        "Delete failed"
    )

    with pytest.raises(Exception, match="Delete failed"):
        await cosmos_service.delete_product("prod-123")


# ============================================================================
# Test User Operations
# ============================================================================


@pytest.fixture
def sample_user_dict():
    """Sample user data as dictionary"""
    return {
        "id": "user-123",
        "email": "test@example.com",
        "name": "Test User",
        "role": "customer",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "last_login": "2024-01-03T00:00:00Z",
    }


@pytest.mark.asyncio
async def test_get_user_success(cosmos_service, sample_user_dict):
    """Test get_user successfully retrieves a user"""
    cosmos_service.users_container.query_items.return_value = [sample_user_dict]

    user = await cosmos_service.get_user("user-123")

    assert user is not None
    assert user.id == "user-123"
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(cosmos_service):
    """Test get_user returns None when user not found"""
    cosmos_service.users_container.query_items.return_value = []

    user = await cosmos_service.get_user("nonexistent-id")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_error_handling(cosmos_service):
    """Test get_user error handling"""
    cosmos_service.users_container.query_items.side_effect = Exception("Query failed")

    with pytest.raises(Exception, match="Query failed"):
        await cosmos_service.get_user("user-123")


@pytest.mark.asyncio
async def test_get_user_by_id_success(cosmos_service, sample_user_dict):
    """Test get_user_by_id successfully retrieves a user"""
    cosmos_service.users_container.query_items.return_value = [sample_user_dict]

    user = await cosmos_service.get_user_by_id("user-123")

    assert user is not None
    assert user.id == "user-123"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(cosmos_service):
    """Test get_user_by_id returns None when user not found"""
    cosmos_service.users_container.query_items.return_value = []

    user = await cosmos_service.get_user_by_id("nonexistent-id")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_success(cosmos_service, sample_user_dict):
    """Test get_user_by_email successfully retrieves a user"""
    cosmos_service.users_container.query_items.return_value = [sample_user_dict]

    user = await cosmos_service.get_user_by_email("test@example.com")

    assert user is not None
    assert user.email == "test@example.com"


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(cosmos_service):
    """Test get_user_by_email returns None when user not found"""
    cosmos_service.users_container.query_items.return_value = []

    user = await cosmos_service.get_user_by_email("notfound@example.com")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_error_handling(cosmos_service):
    """Test get_user_by_email error handling"""
    cosmos_service.users_container.query_items.side_effect = Exception("Query failed")

    with pytest.raises(Exception, match="Query failed"):
        await cosmos_service.get_user_by_email("test@example.com")


@pytest.mark.asyncio
async def test_create_user_success(cosmos_service):
    """Test create_user successfully creates a user"""
    from app.models import UserCreate

    cosmos_service.users_container.create_item.return_value = None

    user_create = UserCreate(email="new@example.com", name="New User", password="password123")

    user = await cosmos_service.create_user(user_create)

    assert user.email == "new@example.com"
    assert user.name == "New User"
    cosmos_service.users_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_error_handling(cosmos_service):
    """Test create_user error handling"""
    from app.models import UserCreate

    cosmos_service.users_container.create_item.side_effect = Exception("Create failed")

    user_create = UserCreate(email="new@example.com", name="New User", password="password123")

    with pytest.raises(Exception, match="Create failed"):
        await cosmos_service.create_user(user_create)


@pytest.mark.asyncio
async def test_create_user_with_password_success(cosmos_service):
    """Test create_user_with_password successfully creates a user"""
    cosmos_service.users_container.create_item.return_value = None

    user = await cosmos_service.create_user_with_password(
        email="new@example.com",
        name="New User",
        password="password123",
        user_id="custom-user-id",
    )

    assert user.email == "new@example.com"
    assert user.name == "New User"
    assert user.id == "custom-user-id"
    cosmos_service.users_container.create_item.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_with_password_auto_id(cosmos_service):
    """Test create_user_with_password generates UUID when no user_id provided"""
    cosmos_service.users_container.create_item.return_value = None

    user = await cosmos_service.create_user_with_password(
        email="new@example.com", name="New User", password="password123"
    )

    assert user.email == "new@example.com"
    assert user.id is not None
    assert len(user.id) == 36  # UUID format


@pytest.mark.asyncio
async def test_create_user_with_password_error_handling(cosmos_service):
    """Test create_user_with_password error handling"""
    cosmos_service.users_container.create_item.side_effect = Exception("Create failed")

    with pytest.raises(Exception, match="Create failed"):
        await cosmos_service.create_user_with_password(
            email="new@example.com", name="New User", password="password123"
        )


@pytest.mark.asyncio
async def test_update_user_success(cosmos_service, sample_user_dict):
    """Test update_user successfully updates a user"""
    from app.models import UserUpdate

    cosmos_service.users_container.query_items.return_value = [sample_user_dict]
    cosmos_service.users_container.replace_item.return_value = None

    user_update = UserUpdate(name="Updated Name")

    user = await cosmos_service.update_user("user-123", user_update)

    assert user is not None
    assert user.name == "Updated Name"
    cosmos_service.users_container.replace_item.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(cosmos_service):
    """Test update_user returns None when user not found"""
    from app.models import UserUpdate

    cosmos_service.users_container.query_items.return_value = []

    user_update = UserUpdate(name="Updated Name")

    user = await cosmos_service.update_user("nonexistent-id", user_update)

    assert user is None


@pytest.mark.asyncio
async def test_update_user_error_handling(cosmos_service, sample_user_dict):
    """Test update_user error handling"""
    from app.models import UserUpdate

    cosmos_service.users_container.query_items.return_value = [sample_user_dict]
    cosmos_service.users_container.replace_item.side_effect = Exception("Update failed")

    user_update = UserUpdate(name="Updated Name")

    with pytest.raises(Exception, match="Update failed"):
        await cosmos_service.update_user("user-123", user_update)


# ============================================================================
# Test is_order_returnable (used in plugins)
# ============================================================================


@pytest.mark.asyncio
async def test_is_order_returnable_true(cosmos_service):
    """Test is_order_returnable returns True for recent orders"""
    from datetime import datetime, timedelta

    recent_date = (datetime.utcnow() - timedelta(days=5)).isoformat() + "Z"
    order_dict = {"id": "order-123", "created_at": recent_date}
    cosmos_service.transactions_container.query_items.return_value = [order_dict]

    result = await cosmos_service.is_order_returnable("order-123")

    assert result is True


@pytest.mark.asyncio
async def test_is_order_returnable_false_too_old(cosmos_service):
    """Test is_order_returnable returns False for old orders"""
    from datetime import datetime, timedelta

    old_date = (datetime.utcnow() - timedelta(days=45)).isoformat() + "Z"
    order_dict = {"id": "order-123", "created_at": old_date}
    cosmos_service.transactions_container.query_items.return_value = [order_dict]

    result = await cosmos_service.is_order_returnable("order-123")

    assert result is False


@pytest.mark.asyncio
async def test_is_order_returnable_order_not_found(cosmos_service):
    """Test is_order_returnable returns False when order not found"""
    cosmos_service.transactions_container.query_items.return_value = []

    result = await cosmos_service.is_order_returnable("nonexistent-order")

    assert result is False


@pytest.mark.asyncio
async def test_is_order_returnable_no_created_at(cosmos_service):
    """Test is_order_returnable returns False when order has no created_at"""
    order_dict = {"id": "order-123"}
    cosmos_service.transactions_container.query_items.return_value = [order_dict]

    result = await cosmos_service.is_order_returnable("order-123")

    assert result is False


@pytest.mark.asyncio
async def test_is_order_returnable_error_handling(cosmos_service):
    """Test is_order_returnable returns False on error"""
    cosmos_service.transactions_container.query_items.side_effect = Exception(
        "Query failed"
    )

    result = await cosmos_service.is_order_returnable("order-123")

    assert result is False
