from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import uuid

from .models import (
    Product, ProductCreate, ProductUpdate,
    User, UserCreate, UserUpdate,
    ChatMessage, ChatMessageCreate, ChatSession,
    Cart, CartItem, Transaction, TransactionCreate
)
from .config import settings, has_cosmos_db_config

class DatabaseService(ABC):
    """Abstract base class for database operations"""
    
    @abstractmethod
    async def get_products(self, search_params: Optional[Dict[str, Any]] = None) -> List[Product]:
        pass
    
    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]:
        pass
    
    @abstractmethod
    async def create_product(self, product: ProductCreate) -> Product:
        pass
    
    @abstractmethod
    async def update_product(self, product_id: str, product: ProductUpdate) -> Optional[Product]:
        pass
    
    @abstractmethod
    async def delete_product(self, product_id: str) -> bool:
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create_user(self, user: UserCreate) -> User:
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user: UserUpdate) -> Optional[User]:
        pass
    
    @abstractmethod
    async def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
        pass
    
    @abstractmethod
    async def create_chat_message(self, message: ChatMessageCreate) -> ChatMessage:
        pass
    
    @abstractmethod
    async def get_cart(self, user_id: str) -> Optional[Cart]:
        pass
    
    @abstractmethod
    async def update_cart(self, user_id: str, cart: Cart) -> Cart:
        pass
    
    @abstractmethod
    async def create_transaction(self, transaction: TransactionCreate, user_id: str) -> Transaction:
        pass
    
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        pass
    
    @abstractmethod
    async def create_user_with_password(self, email: str, name: str, password: str, user_id: Optional[str] = None) -> User:
        pass

class MockDatabaseService(DatabaseService):
    """Mock database service using in-memory storage"""
    
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.users: Dict[str, User] = {}
        self.chat_messages: Dict[str, List[ChatMessage]] = {}
        self.carts: Dict[str, Cart] = {}
        self.transactions: Dict[str, Transaction] = {}
        self._initialize_mock_data()
    
    def _initialize_mock_data(self):
        """Initialize with mock data"""
        # Mock products
        mock_products = [
            {
                "id": "1",
                "title": "Modern Minimalist Desk Lamp",
                "price": 89.99,
                "original_price": 129.99,
                "rating": 4.5,
                "review_count": 128,
                "image": "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=400&h=400&fit=crop",
                "category": "Lighting",
                "in_stock": True,
                "description": "Sleek LED desk lamp with adjustable brightness and USB charging port",
                "tags": ["lighting", "desk", "led", "modern"],
                "specifications": {"wattage": "15W", "color_temperature": "3000K-6000K"}
            },
            {
                "id": "2", 
                "title": "Ergonomic Office Chair",
                "price": 1.99999999,
                "rating": 4.8,
                "review_count": 89,
                "image": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=400&h=400&fit=crop",
                "category": "Furniture",
                "in_stock": True,
                "description": "Premium ergonomic chair with lumbar support and adjustable height",
                "tags": ["furniture", "office", "ergonomic", "chair"],
                "specifications": {"weight_capacity": "300lbs", "adjustable_height": True}
            },
            {
                "id": "3",
                "title": "Wireless Noise-Canceling Headphones",
                "price": 179.99,
                "original_price": 249.99,
                "rating": 4.7,
                "review_count": 456,
                "image": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=400&fit=crop",
                "category": "Electronics",
                "in_stock": True,
                "description": "Premium wireless headphones with active noise cancellation",
                "tags": ["electronics", "audio", "wireless", "noise-canceling"],
                "specifications": {"battery_life": "30 hours", "bluetooth_version": "5.0"}
            }
        ]
        
        for product_data in mock_products:
            product = Product(**product_data)
            self.products[product.id] = product
        
        # Mock chat messages
        self.chat_messages["default"] = [
            ChatMessage(
                id=str(uuid.uuid4()),
                session_id="default",
                content="Hi there! I'm Cora, your personal shopping assistant. I'm here to help you discover the best deals, find exactly what you're looking for, and make your shopping experience smooth and enjoyable. Just tell me what you need—I've got you covered!",
                message_type="assistant",
                created_at=datetime.utcnow()
            )
        ]
    
    async def get_products(self, search_params: Optional[Dict[str, Any]] = None) -> List[Product]:
        """Get products with optional filtering"""
        products = list(self.products.values())
        
        if not search_params:
            return products
        
        # Apply filters
        if search_params.get("category") and search_params["category"] != "All":
            products = [p for p in products if p.category == search_params["category"]]
        
        if search_params.get("min_price"):
            products = [p for p in products if p.price >= search_params["min_price"]]
        
        if search_params.get("max_price"):
            products = [p for p in products if p.price <= search_params["max_price"]]
        
        if search_params.get("min_rating"):
            products = [p for p in products if p.rating >= search_params["min_rating"]]
        
        if search_params.get("in_stock_only"):
            products = [p for p in products if p.in_stock]
        
        if search_params.get("query"):
            query = search_params["query"].lower()
            products = [p for p in products if 
                       query in p.title.lower() or 
                       query in (p.description or "").lower() or 
                       query in p.category.lower()]
        
        # Apply sorting
        sort_by = search_params.get("sort_by", "name")
        sort_order = search_params.get("sort_order", "asc")
        
        if sort_by == "name":
            products.sort(key=lambda x: x.title, reverse=(sort_order == "desc"))
        elif sort_by == "price":
            products.sort(key=lambda x: x.price, reverse=(sort_order == "desc"))
        elif sort_by == "rating":
            products.sort(key=lambda x: x.rating, reverse=(sort_order == "desc"))
        
        return products
    
    async def get_product(self, product_id: str) -> Optional[Product]:
        """Get a single product by ID"""
        return self.products.get(product_id)
    
    async def create_product(self, product: ProductCreate) -> Product:
        """Create a new product"""
        new_product = Product(
            id=str(uuid.uuid4()),
            **product.dict()
        )
        self.products[new_product.id] = new_product
        return new_product
    
    async def update_product(self, product_id: str, product: ProductUpdate) -> Optional[Product]:
        """Update an existing product"""
        if product_id not in self.products:
            return None
        
        existing_product = self.products[product_id]
        update_data = product.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(existing_product, field, value)
        
        existing_product.updated_at = datetime.utcnow()
        return existing_product
    
    async def delete_product(self, product_id: str) -> bool:
        """Delete a product"""
        if product_id in self.products:
            del self.products[product_id]
            return True
        return False
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)
    
    async def create_user(self, user: UserCreate) -> User:
        """Create a new user"""
        new_user = User(
            id=str(uuid.uuid4()),
            email=user.email,
            name=user.name
        )
        self.users[new_user.id] = new_user
        return new_user
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def create_user_with_password(self, email: str, name: str, password: str, user_id: Optional[str] = None) -> User:
        """Create a new user with password (password is ignored in mock)"""
        new_user = User(
            id=user_id or str(uuid.uuid4()),
            email=email,
            name=name
        )
        self.users[new_user.id] = new_user
        return new_user
    
    async def update_user(self, user_id: str, user: UserUpdate) -> Optional[User]:
        """Update user"""
        if user_id not in self.users:
            return None
        
        existing_user = self.users[user_id]
        update_data = user.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(existing_user, field, value)
        
        existing_user.updated_at = datetime.utcnow()
        return existing_user
    
    async def get_chat_messages(self, session_id: str) -> List[ChatMessage]:
        """Get chat messages for a session"""
        return self.chat_messages.get(session_id, [])
    
    async def create_chat_message(self, message: ChatMessageCreate) -> ChatMessage:
        """Create a new chat message"""
        session_id = message.session_id or "default"
        
        new_message = ChatMessage(
            id=str(uuid.uuid4()),
            content=message.content,
            message_type=message.message_type or "user",
            metadata=message.metadata
        )
        
        if session_id not in self.chat_messages:
            self.chat_messages[session_id] = []
        
        self.chat_messages[session_id].append(new_message)
        return new_message
    
    async def get_cart(self, user_id: str) -> Optional[Cart]:
        """Get user's cart"""
        return self.carts.get(user_id)
    
    async def update_cart(self, user_id: str, cart: Cart) -> Cart:
        """Update user's cart"""
        self.carts[user_id] = cart
        return cart
    
    async def create_transaction(self, transaction: TransactionCreate, user_id: str) -> Transaction:
        """Create a new transaction"""
        new_transaction = Transaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            order_number=f"ORD-{uuid.uuid4().hex[:8].upper()}",
            items=transaction.items,
            shipping_address=transaction.shipping_address,
            payment_method=transaction.payment_method,
            payment_reference=transaction.payment_reference
        )
        
        # Calculate totals
        new_transaction.subtotal = sum(item.total_price for item in transaction.items)
        new_transaction.tax = new_transaction.subtotal * 0.08  # 8% tax
        new_transaction.shipping = 9.99 if new_transaction.subtotal < 50 else 0
        new_transaction.total = new_transaction.subtotal + new_transaction.tax + new_transaction.shipping
        
        self.transactions[new_transaction.id] = new_transaction
        return new_transaction

# Database service factory
def get_database_service() -> DatabaseService:
    """Get the appropriate database service based on configuration"""
    if has_cosmos_db_config():
        try:
            # Handle both relative and absolute imports
            try:
                from .cosmos_service import CosmosDatabaseService
            except ImportError:
                from cosmos_service import CosmosDatabaseService
            return CosmosDatabaseService()
        except Exception as e:
            print(f"Failed to initialize Cosmos DB service: {e}")
            raise RuntimeError(f"Cannot connect to Cosmos DB: {e}. Please check your COSMOS_DB_ENDPOINT configuration.")
    
    # No fallback - raise error if Cosmos DB config is missing
    raise RuntimeError("Cosmos DB is not configured. Please set COSMOS_DB_ENDPOINT environment variable.")

# Global database service instance - lazy initialization
db_service = None

def get_db_service():
    """Get the database service instance with lazy initialization"""
    global db_service
    if db_service is None:
        db_service = get_database_service()
    return db_service