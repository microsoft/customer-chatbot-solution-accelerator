import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"


# Base Models
class BaseEntity(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}

    def model_dump_json(self, **kwargs):
        """Custom JSON serialization for datetime objects"""
        data = self.model_dump(**kwargs)
        # Convert datetime objects to ISO format
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


# Product Models
class Product(BaseEntity):
    title: str
    price: float
    original_price: Optional[float] = None
    rating: float = Field(ge=0, le=5)
    review_count: int = Field(ge=0)
    image: str
    category: str
    in_stock: bool = True
    stock_quantity: int = Field(ge=0, default=0)
    description: Optional[str] = None
    tags: List[str] = []
    specifications: Dict[str, Any] = {}
    is_featured: bool = False


class ProductCreate(BaseModel):
    title: str
    price: float
    original_price: Optional[float] = None
    rating: float = Field(ge=0, le=5, default=0)
    review_count: int = Field(ge=0, default=0)
    image: str
    category: str
    in_stock: bool = True
    stock_quantity: int = Field(ge=0, default=0)
    description: Optional[str] = None
    tags: List[str] = []
    specifications: Dict[str, Any] = {}
    is_featured: bool = False


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    image: Optional[str] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None
    is_featured: Optional[bool] = None


# Customer Models
class Customer(BaseEntity):
    email: str
    name: str
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    preferences: Dict[str, Any] = {}
    default_shipping_address: Optional[Dict[str, Any]] = None
    last_login: Optional[datetime] = None


class CustomerCreate(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    default_shipping_address: Optional[Dict[str, Any]] = None


# Cart Models
class CartItem(BaseModel):
    product_id: str
    product_title: str
    product_price: float
    product_image: str
    quantity: int = Field(ge=1)
    added_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def total_price(self) -> float:
        return self.product_price * self.quantity


class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)


class UpdateCartItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=0)  # 0 means remove item


class Cart(BaseEntity):
    user_id: Optional[str] = None
    items: List[CartItem] = []
    total_items: int = 0
    total_price: float = 0.0


# Order Models
class OrderItem(BaseModel):
    product_id: str
    product_title: str
    quantity: int
    unit_price: float
    total_price: float


class ShippingAddress(BaseModel):
    name: str
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    phone: Optional[str] = None


class Order(BaseEntity):
    customer_id: str
    order_number: str
    status: OrderStatus = OrderStatus.PENDING
    items: List[OrderItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    shipping_cost: float = 0.0
    total: float = 0.0
    shipping_address: ShippingAddress
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderCreate(BaseModel):
    shipping_address: ShippingAddress
    payment_method: PaymentMethod
    payment_reference: Optional[str] = None


class OrderUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None


# API Response Models
class APIResponse(BaseModel):
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    error: Optional[str] = None


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Search and Filter Models
class ProductSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    min_rating: Optional[float] = None
    in_stock_only: bool = False
    sort_by: str = "name"
    sort_order: str = "asc"
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)


# Auth Models
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool
    is_guest: bool = False