from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .config import has_cosmos_db_config
from .models import (
    Cart,
    Customer,
    CustomerCreate,
    CustomerUpdate,
    Order,
    OrderCreate,
    OrderStatus,
    Product,
    ProductCreate,
    ProductUpdate,
)


class EcommerceDatabaseService(ABC):
    """Abstract base class for e-commerce database operations"""

    # Product operations
    @abstractmethod
    async def get_products(
        self, search_params: Optional[Dict[str, Any]] = None
    ) -> List[Product]:
        pass

    @abstractmethod
    async def get_product(self, product_id: str) -> Optional[Product]:
        pass

    @abstractmethod
    async def create_product(self, product: ProductCreate) -> Product:
        pass

    @abstractmethod
    async def update_product(
        self, product_id: str, product: ProductUpdate
    ) -> Optional[Product]:
        pass

    @abstractmethod
    async def delete_product(self, product_id: str) -> bool:
        pass

    @abstractmethod
    async def get_product_categories(self) -> List[str]:
        pass

    @abstractmethod
    async def get_featured_products(self, limit: int = 10) -> List[Product]:
        pass

    @abstractmethod
    async def get_related_products(self, product_id: str, limit: int = 5) -> List[Product]:
        pass

    @abstractmethod
    async def restore_product_stock(self, product_id: str, quantity: int) -> bool:
        pass

    # Customer operations
    @abstractmethod
    async def get_customer(self, customer_id: str) -> Optional[Customer]:
        pass

    @abstractmethod
    async def create_customer(self, customer: CustomerCreate) -> Customer:
        pass

    @abstractmethod
    async def update_customer(
        self, customer_id: str, customer: CustomerUpdate
    ) -> Optional[Customer]:
        pass

    @abstractmethod
    async def get_customer_by_email(self, email: str) -> Optional[Customer]:
        pass

    @abstractmethod
    async def get_or_create_customer(
        self, user_id: str, email: str, name: str
    ) -> Customer:
        pass

    # Cart operations
    @abstractmethod
    async def get_cart(self, user_id: str) -> Optional[Cart]:
        pass

    @abstractmethod
    async def update_cart(self, user_id: str, cart: Cart) -> Cart:
        pass

    @abstractmethod
    async def clear_cart(self, user_id: str) -> bool:
        pass

    # Order operations
    @abstractmethod
    async def create_order(
        self, user_id: str, cart: Cart, shipping_address: Dict[str, Any], payment_method: str
    ) -> Order:
        pass

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        pass

    @abstractmethod
    async def get_customer_orders(
        self, customer_id: str, status: Optional[OrderStatus] = None, page: int = 1, page_size: int = 10
    ) -> List[Order]:
        pass

    @abstractmethod
    async def update_order_status(self, order_id: str, status: OrderStatus) -> Optional[Order]:
        pass


# Database service factory
def get_database_service() -> EcommerceDatabaseService:
    """Get the appropriate database service based on configuration"""
    if has_cosmos_db_config():
        try:
            # Handle both relative and absolute imports
            try:
                from .cosmos_service import EcommerceCosmosService
            except ImportError:
                from cosmos_service import EcommerceCosmosService
            return EcommerceCosmosService()
        except ImportError:
            print("⚠️ Cosmos DB dependencies not found, falling back to in-memory service")
            from .memory_service import EcommerceMemoryService
            return EcommerceMemoryService()
    else:
        print("📝 No Cosmos DB configuration found, using in-memory service")
        from .memory_service import EcommerceMemoryService
        return EcommerceMemoryService()


# Global database service instance
_db_service = None


def get_db_service() -> EcommerceDatabaseService:
    """Get the global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = get_database_service()
    return _db_service