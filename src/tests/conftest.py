"""
Test configuration and fixtures for endpoint testing
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing modules
os.environ["ENVIRONMENT"] = "test"
os.environ["COSMOS_DB_ENDPOINT"] = ""
os.environ["COSMOS_DB_KEY"] = ""
os.environ["AZURE_SEARCH_ENDPOINT"] = ""
os.environ["AZURE_OPENAI_ENDPOINT"] = ""

# Add the src/api directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

# Mock the database service globally to prevent Azure connections
with patch("app.cosmos_service.CosmosDatabaseService") as mock_cosmos_service:
    # Create a mock that doesn't try to connect
    mock_instance = Mock()

    # Add all necessary async mock methods
    mock_methods = [
        "get_user",
        "get_user_by_email",
        "get_user_by_id",
        "create_user",
        "get_products",
        "get_product",
        "create_product",
        "update_product",
        "delete_product",
        "get_cart",
        "update_cart",
        "get_chat_sessions",
        "get_chat_session",
        "create_chat_session",
        "delete_chat_session",
        "add_message",
    ]

    for method_name in mock_methods:
        setattr(mock_instance, method_name, AsyncMock(return_value=None))

    mock_cosmos_service.return_value = mock_instance

    # Now import the application modules
    from app.config import Settings
    from app.database import DatabaseService
    from app.main import app
    from app.models import Cart, ChatSession, Product, User, UserRole


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    """Test settings fixture"""
    return Settings(
        ENVIRONMENT="test",
        COSMOS_DB_ENDPOINT="https://test.documents.azure.com",
        COSMOS_DB_KEY="test-key",
        COSMOS_DB_DATABASE_NAME="test-db",
        AZURE_SEARCH_ENDPOINT="https://test.search.windows.net",
        AZURE_SEARCH_KEY="test-key",
        AZURE_SEARCH_INDEX="test-index",
        AZURE_OPENAI_ENDPOINT="https://test.openai.azure.com",
        AZURE_OPENAI_KEY="test-key",
        AZURE_OPENAI_DEPLOYMENT="test-deployment",
        LOG_LEVEL="DEBUG",
        CORS_ORIGINS=["http://localhost:3000"],
    )


@pytest.fixture
def mock_db_service():
    """Mock database service fixture"""
    mock_service = Mock(spec=DatabaseService)

    # Mock all database methods with AsyncMock
    mock_service.get_user = AsyncMock()
    mock_service.create_user = AsyncMock()
    mock_service.update_user = AsyncMock()
    mock_service.delete_user = AsyncMock()

    mock_service.get_products = AsyncMock()
    mock_service.get_product = AsyncMock()
    mock_service.create_product = AsyncMock()
    mock_service.update_product = AsyncMock()
    mock_service.delete_product = AsyncMock()

    mock_service.get_chat_sessions = AsyncMock()
    mock_service.get_chat_session = AsyncMock()
    mock_service.create_chat_session = AsyncMock()
    mock_service.update_chat_session = AsyncMock()
    mock_service.delete_chat_session = AsyncMock()

    mock_service.get_cart = AsyncMock()
    mock_service.create_cart = AsyncMock()
    mock_service.update_cart = AsyncMock()
    mock_service.add_to_cart = AsyncMock()
    mock_service.remove_from_cart = AsyncMock()
    mock_service.clear_cart = AsyncMock()

    return mock_service


@pytest.fixture
def sample_user():
    """Sample user fixture for endpoint testing"""
    return User(
        id="test-user-123",
        name="Test User",
        email="test@example.com",
        role=UserRole.CUSTOMER,
        preferences={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_product():
    """Sample product fixture for endpoint testing"""
    return Product(
        id="prod-123",
        title="Test Product",
        price=29.99,
        description="A test product",
        category="test",
        image="https://example.com/image.jpg",
        rating=4.5,
        review_count=10,
        in_stock=True,
        tags=["test", "sample"],
        specifications={"color": "blue", "size": "medium"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_chat_session():
    """Sample chat session fixture for endpoint testing"""
    return ChatSession(
        id="session-123",
        user_id="user-123",
        session_name="Test Chat",
        message_count=2,
        last_message_at=datetime.utcnow(),
        is_active=True,
        messages=[],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_cart():
    """Sample cart fixture for endpoint testing"""
    return Cart(
        id="cart-123",
        user_id="user-123",
        items=[],
        total_items=0,
        total_price=0.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def client(mock_db_service):
    """FastAPI test client fixture with mocked dependencies"""
    # Simple approach - just patch the main database services
    with patch("app.database.get_db_service", return_value=mock_db_service), patch(
        "app.cosmos_service.get_cosmos_service", return_value=mock_db_service
    ):
        with TestClient(app) as test_client:
            yield test_client
