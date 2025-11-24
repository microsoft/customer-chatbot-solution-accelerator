import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data
    assert "openai" in data
    assert "auth" in data

def test_products_endpoint():
    """Test products endpoint"""
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:  # If products exist
        product = data[0]
        assert "id" in product
        assert "title" in product
        assert "price" in product
        assert "category" in product

def test_products_with_filters():
    """Test products endpoint with filters"""
    response = client.get("/api/products?category=Electronics&min_price=100")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_product_by_id():
    """Test get product by ID"""
    # First get all products to find a valid ID
    response = client.get("/api/products")
    assert response.status_code == 200
    products = response.json()
    
    if products:
        product_id = products[0]["id"]
        response = client.get(f"/api/products/{product_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id

def test_product_not_found():
    """Test get non-existent product"""
    response = client.get("/api/products/non-existent-id")
    assert response.status_code == 404

def test_chat_history():
    """Test chat history endpoint"""
    response = client.get("/api/chat/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_send_chat_message():
    """Test send chat message"""
    message_data = {
        "content": "Hello, I need help finding a product",
        "session_id": "test-session"
    }
    response = client.post("/api/chat/message", json=message_data)
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    assert "id" in data

def test_cart_endpoints():
    """Test cart endpoints"""
    # Get cart
    response = client.get("/api/cart")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    
    # Add to cart
    response = client.post("/api/cart/add?product_id=1&quantity=2")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    
    # Update cart
    response = client.put("/api/cart/update?product_id=1&quantity=3")
    assert response.status_code == 200
    
    # Remove from cart
    response = client.delete("/api/cart/1")
    assert response.status_code == 200

def test_categories_endpoint():
    """Test categories endpoint"""
    response = client.get("/api/products/categories/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_ai_status():
    """Test AI status endpoint"""
    response = client.get("/api/chat/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "configured" in data["data"]