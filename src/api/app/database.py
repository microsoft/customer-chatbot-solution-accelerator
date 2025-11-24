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