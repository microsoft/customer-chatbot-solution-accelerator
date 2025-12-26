from unittest.mock import Mock, patch

import app.services.search as search_module
import pytest
from app.services.search import (get_product_search_client, get_search_client,
                                 has_azure_search_endpoint, search_products,
                                 search_products_fast, search_reference,
                                 search_reference_enhanced)


@pytest.fixture
def mock_settings():
    """Mock settings for Azure Search configuration"""
    with patch("app.services.search.settings") as mock:
        mock.azure_search_endpoint = "https://test-search.search.windows.net"
        mock.azure_search_index = "test-policies-index"
        mock.azure_search_product_index = "test-products-index"
        yield mock


@pytest.fixture
def mock_azure_credential():
    """Mock Azure credential"""
    with patch("app.services.search.get_azure_credential") as mock:
        mock_cred = Mock()
        mock.return_value = mock_cred
        yield mock


@pytest.fixture
def mock_search_client():
    """Mock SearchClient"""
    with patch("app.services.search.SearchClient") as mock:
        yield mock


@pytest.fixture
def mock_has_config():
    """Mock has_azure_search_config to return True"""
    with patch("app.services.search.has_azure_search_config", return_value=True):
        yield


@pytest.fixture(autouse=True)
def reset_clients():
    """Reset global client variables before each test"""
    search_module._client = None
    search_module._product_client = None
    yield


class TestConfigurationChecks:
    """Test configuration checking functions"""

    @patch("app.services.search.settings")
    def test_has_azure_search_endpoint_configured(self, mock_settings):
        """Test when Azure Search endpoint is configured"""
        mock_settings.azure_search_endpoint = "https://test.search.windows.net"

        result = has_azure_search_endpoint()

        assert result is True

    @patch("app.services.search.settings")
    def test_has_azure_search_endpoint_not_configured(self, mock_settings):
        """Test when Azure Search endpoint is None"""
        mock_settings.azure_search_endpoint = None

        result = has_azure_search_endpoint()

        assert result is False


class TestGetSearchClient:
    """Test get_search_client function"""

    def test_get_search_client_success(
        self, mock_settings, mock_azure_credential, mock_search_client, mock_has_config
    ):
        """Test successful search client initialization"""
        mock_client_instance = Mock()
        mock_search_client.return_value = mock_client_instance

        result = get_search_client()

        assert result == mock_client_instance
        mock_search_client.assert_called_once_with(
            endpoint="https://test-search.search.windows.net",
            index_name="test-policies-index",
            credential=mock_azure_credential.return_value,
        )

    def test_get_search_client_returns_cached(
        self, mock_settings, mock_azure_credential, mock_search_client, mock_has_config
    ):
        """Test that search client is cached after first call"""
        mock_client_instance = Mock()
        mock_search_client.return_value = mock_client_instance

        result1 = get_search_client()
        result2 = get_search_client()

        assert result1 == result2
        assert mock_search_client.call_count == 1  # Only called once

    @patch("app.services.search.has_azure_search_config", return_value=False)
    def test_get_search_client_no_config(self, mock_has_config):
        """Test when Azure Search is not configured"""
        result = get_search_client()

        assert result is None


class TestGetProductSearchClient:
    """Test get_product_search_client function"""

    def test_get_product_search_client_success(
        self, mock_settings, mock_azure_credential, mock_search_client, mock_has_config
    ):
        """Test successful product search client initialization"""
        mock_client_instance = Mock()
        mock_search_client.return_value = mock_client_instance

        result = get_product_search_client()

        assert result == mock_client_instance
        mock_search_client.assert_called_once_with(
            endpoint="https://test-search.search.windows.net",
            index_name="test-products-index",
            credential=mock_azure_credential.return_value,
        )

    def test_get_product_search_client_returns_cached(
        self, mock_settings, mock_azure_credential, mock_search_client, mock_has_config
    ):
        """Test that product search client is cached"""
        mock_client_instance = Mock()
        mock_search_client.return_value = mock_client_instance

        result1 = get_product_search_client()
        result2 = get_product_search_client()

        assert result1 == result2
        assert mock_search_client.call_count == 1

    @patch("app.services.search.has_azure_search_config", return_value=False)
    def test_get_product_search_client_no_config(self, mock_has_config):
        """Test when Azure Search is not configured"""
        result = get_product_search_client()

        assert result is None


class TestSearchReference:
    """Test search_reference function"""

    @patch("app.services.search.get_search_client")
    def test_search_reference_no_client(self, mock_get_client):
        """Test when search client is not available"""
        mock_get_client.return_value = None

        result = search_reference("test query")

        assert result == []

    @patch("app.services.search.get_search_client")
    def test_search_reference_semantic_success(self, mock_get_client):
        """Test successful semantic search"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock search results
        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Test Document",
            "content": "Test content",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.95)
        setattr(mock_result, "@search.answers", None)
        setattr(mock_result, "@search.captions", None)

        mock_client.search.return_value = [mock_result]

        result = search_reference("test query", top=5)

        assert len(result) == 1
        assert result[0]["id"] == "doc1"
        assert result[0]["title"] == "Test Document"
        assert result[0]["content"] == "Test content"
        assert result[0]["score"] == 0.95

        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["search_text"] == "test query"
        assert call_kwargs["top"] == 5
        assert call_kwargs["query_type"] == "semantic"

    @patch("app.services.search.get_search_client")
    def test_search_reference_semantic_fallback_to_simple(self, mock_get_client):
        """Test fallback from semantic to simple search"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # First call (semantic) fails, second call (simple) succeeds
        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Simple Result",
            "content": "Content",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.75)

        mock_client.search.side_effect = [
            Exception("Semantic search not available"),
            [mock_result],
        ]

        result = search_reference("fallback query")

        assert len(result) == 1
        assert result[0]["title"] == "Simple Result"
        assert mock_client.search.call_count == 2

    @patch("app.services.search.get_search_client")
    def test_search_reference_multiple_results(self, mock_get_client):
        """Test search returning multiple results"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = []
        for i in range(3):
            mock_result = Mock()
            mock_result.get = lambda key, default=None, idx=i: {
                "id": f"doc{idx}",
                "title": f"Document {idx}",
                "content": f"Content {idx}",
            }.get(key, default)
            setattr(mock_result, "@search.score", 0.9 - i * 0.1)
            setattr(mock_result, "@search.answers", None)
            setattr(mock_result, "@search.captions", None)
            mock_results.append(mock_result)

        mock_client.search.return_value = mock_results

        result = search_reference("multiple docs", top=10)

        assert len(result) == 3
        assert result[0]["id"] == "doc0"
        assert result[1]["id"] == "doc1"
        assert result[2]["id"] == "doc2"

    @patch("app.services.search.get_search_client")
    def test_search_reference_error(self, mock_get_client):
        """Test when search raises an error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = Exception("Search service error")

        result = search_reference("error query")

        assert result == []


class TestSearchReferenceEnhanced:
    """Test search_reference_enhanced function"""

    @patch("app.services.search.get_search_client")
    def test_search_reference_enhanced_no_client(self, mock_get_client):
        """Test when search client is not available"""
        mock_get_client.return_value = None

        result = search_reference_enhanced("test query")

        assert result == []

    @patch("app.services.search.get_search_client")
    def test_search_reference_enhanced_with_context(self, mock_get_client):
        """Test enhanced search with context"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Context Document",
            "content": "Content",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.92)

        mock_client.search.return_value = [mock_result]

        result = search_reference_enhanced("query", top=5, context="additional context")

        assert len(result) == 1
        assert result[0]["title"] == "Context Document"

        # Verify query was enhanced with context
        call_kwargs = mock_client.search.call_args[1]
        assert "query" in call_kwargs["search_text"]
        assert "additional context" in call_kwargs["search_text"]

    @patch("app.services.search.get_search_client")
    def test_search_reference_enhanced_semantic_strategy(self, mock_get_client):
        """Test enhanced search uses semantic strategy first"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Semantic Result",
            "content": "Content",
            "@search.answers": [{"text": "Semantic answer"}],
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.95)
        setattr(mock_result, "@search.answers", [{"text": "Semantic answer"}])

        mock_client.search.return_value = [mock_result]

        result = search_reference_enhanced("semantic query")

        assert len(result) == 1
        assert "answers" in result[0]
        assert result[0]["answers"] == ["Semantic answer"]

    @patch("app.services.search.get_search_client")
    def test_search_reference_enhanced_strategy_fallback(self, mock_get_client):
        """Test enhanced search tries multiple strategies"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Fallback Result",
            "content": "Content",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.8)

        # First strategy fails, third succeeds
        mock_client.search.side_effect = [
            Exception("Semantic failed"),
            Exception("Full search failed"),
            [mock_result],
        ]

        result = search_reference_enhanced("fallback query")

        assert len(result) == 1
        assert result[0]["title"] == "Fallback Result"
        assert mock_client.search.call_count == 3

    @patch("app.services.search.get_search_client")
    def test_search_reference_enhanced_with_highlights(self, mock_get_client):
        """Test enhanced search with highlights"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "doc1",
            "title": "Highlighted",
            "content": "Content",
            "@search.highlights": {"content": ["<mark>highlighted text</mark>"]},
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.87)
        setattr(
            mock_result,
            "@search.highlights",
            {"content": ["<mark>highlighted text</mark>"]},
        )

        # Make semantic fail to try full search with highlights
        mock_client.search.side_effect = [
            Exception("Semantic not available"),
            [mock_result],
        ]

        result = search_reference_enhanced("highlight query")

        assert len(result) == 1
        assert "highlights" in result[0]


class TestSearchProducts:
    """Test search_products function"""

    @patch("app.services.search.get_product_search_client")
    def test_search_products_no_client(self, mock_get_client):
        """Test when product search client is not available"""
        mock_get_client.return_value = None

        result = search_products("test product")

        assert result == []

    @patch("app.services.search.get_product_search_client")
    def test_search_products_success(self, mock_get_client):
        """Test successful product search"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "prod1",
            "title": "Test Product",
            "description": "Product description",
            "price": 29.99,
            "category": "Electronics",
            "inventory": 50,
            "image": "product.jpg",
            "tags": "electronic,gadget",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.93)

        mock_client.search.return_value = [mock_result]

        result = search_products("test product", top=5)

        assert len(result) == 1
        assert result[0]["id"] == "prod1"
        assert result[0]["title"] == "Test Product"
        assert result[0]["price"] == 29.99
        assert result[0]["category"] == "Electronics"

    @patch("app.services.search.get_product_search_client")
    def test_search_products_with_context(self, mock_get_client):
        """Test product search with context"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "prod1",
            "title": "Context Product",
            "description": "Description",
            "price": 19.99,
            "category": "Tools",
            "inventory": 100,
            "image": "tool.jpg",
            "tags": "",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.88)

        mock_client.search.return_value = [mock_result]

        result = search_products("hammer", context="for woodworking")

        assert len(result) == 1
        call_kwargs = mock_client.search.call_args[1]
        assert "hammer" in call_kwargs["search_text"]
        assert "woodworking" in call_kwargs["search_text"]

    @patch("app.services.search.get_product_search_client")
    def test_search_products_multiple_strategies(self, mock_get_client):
        """Test product search tries multiple strategies"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "prod1",
            "title": "Product",
            "description": "Desc",
            "price": 9.99,
            "category": "Other",
            "inventory": 10,
            "image": "img.jpg",
            "tags": "",
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.75)

        # Multiple strategies fail before one succeeds
        mock_client.search.side_effect = [
            Exception("Semantic failed"),
            Exception("Full failed"),
            Exception("Simple failed"),
            [mock_result],  # Basic search succeeds
        ]

        result = search_products("product query")

        assert len(result) == 1
        assert mock_client.search.call_count == 4

    @patch("app.services.search.get_product_search_client")
    def test_search_products_error(self, mock_get_client):
        """Test when all product search strategies fail"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = Exception("Search service down")

        result = search_products("error query")

        assert result == []


class TestSearchProductsFast:
    """Test search_products_fast function"""

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_no_client(self, mock_get_client):
        """Test when product search client is not available"""
        mock_get_client.return_value = None

        result = search_products_fast("fast query")

        assert result == []

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_semantic_success(self, mock_get_client):
        """Test fast product search with semantic search"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "fast1",
            "title": "Fast Product",
            "description": "Quick description",
            "price": 14.99,
            "category": "Quick",
            "inventory": 200,
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.91)
        setattr(mock_result, "@search.answers", None)

        mock_client.search.return_value = [mock_result]

        result = search_products_fast("fast query", top=3)

        assert len(result) == 1
        assert result[0]["id"] == "fast1"
        assert result[0]["title"] == "Fast Product"
        assert "image" not in result[0]  # Fast search omits image for speed

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_fallback_to_basic(self, mock_get_client):
        """Test fast search falls back to basic when semantic fails"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_result = Mock()
        mock_result.get = lambda key, default=None: {
            "id": "basic1",
            "title": "Basic Result",
            "description": "Desc",
            "price": 9.99,
            "category": "Cat",
            "inventory": 10,
        }.get(key, default)
        setattr(mock_result, "@search.score", 0.70)

        # Semantic fails, basic succeeds
        mock_client.search.side_effect = [
            Exception("Semantic not available"),
            [mock_result],
        ]

        result = search_products_fast("fallback query")

        assert len(result) == 1
        assert result[0]["title"] == "Basic Result"
        assert mock_client.search.call_count == 2

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_multiple_results(self, mock_get_client):
        """Test fast search with multiple results"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        mock_results = []
        for i in range(3):
            mock_result = Mock()
            mock_result.get = lambda key, default=None, idx=i: {
                "id": f"prod{idx}",
                "title": f"Product {idx}",
                "description": f"Desc {idx}",
                "price": 10.0 + idx,
                "category": "Multi",
                "inventory": 100,
            }.get(key, default)
            setattr(mock_result, "@search.score", 0.9 - i * 0.05)
            setattr(mock_result, "@search.answers", None)
            mock_results.append(mock_result)

        mock_client.search.return_value = mock_results

        result = search_products_fast("multiple products", top=3)

        assert len(result) == 3
        assert result[0]["id"] == "prod0"
        assert result[1]["id"] == "prod1"
        assert result[2]["id"] == "prod2"

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_error(self, mock_get_client):
        """Test when fast search encounters error"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = Exception("Service unavailable")

        result = search_products_fast("error query")

        assert result == []

    @patch("app.services.search.get_product_search_client")
    def test_search_products_fast_default_top_value(self, mock_get_client):
        """Test fast search uses default top=3"""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = []

        search_products_fast("default top query")

        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["top"] == 3
