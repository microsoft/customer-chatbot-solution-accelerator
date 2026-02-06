import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    SUPPORT = "support"


class OrderStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class ChatMessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


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
    description: Optional[str] = None
    tags: List[str] = []
    specifications: Dict[str, Any] = {}


class ProductCreate(BaseModel):
    title: str
    price: float
    original_price: Optional[float] = None
    rating: float = Field(ge=0, le=5, default=0)
    review_count: int = Field(ge=0, default=0)
    image: str
    category: str
    in_stock: bool = True
    description: Optional[str] = None
    tags: List[str] = []
    specifications: Dict[str, Any] = {}


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    image: Optional[str] = None
    category: Optional[str] = None
    in_stock: Optional[bool] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    specifications: Optional[Dict[str, Any]] = None


# User Models
class User(BaseEntity):
    email: str
    name: str  # For display purposes
    role: UserRole = UserRole.CUSTOMER
    is_active: bool = True
    preferences: Dict[str, Any] = {}
    last_login: Optional[datetime] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class UserCreate(BaseModel):
    email: str
    name: str
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


# Auth Models
class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    is_active: bool


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Chat Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    message_type: ChatMessageType
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class ChatSession(BaseEntity):
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    is_active: bool = True
    context: Dict[str, Any] = {}
    messages: List[ChatMessage] = []
    message_count: int = 0
    last_message_at: Optional[datetime] = None


class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[str] = None
    message_type: Optional[ChatMessageType] = None
    metadata: Dict[str, Any] = {}


class ChatSessionCreate(BaseModel):
    user_id: Optional[str] = None
    session_name: Optional[str] = None
    context: Dict[str, Any] = {}


class ChatSessionUpdate(BaseModel):
    session_name: Optional[str] = None
    is_active: Optional[bool] = None
    context: Optional[Dict[str, Any]] = None


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


class Cart(BaseEntity):
    user_id: Optional[str] = None
    items: List[CartItem] = []
    total_items: int = 0
    total_price: float = 0.0


# Transaction Models
class TransactionItem(BaseModel):
    product_id: str
    product_title: str
    quantity: int
    unit_price: float
    total_price: float


class Transaction(BaseEntity):
    user_id: str
    order_number: str
    status: OrderStatus = OrderStatus.PENDING
    items: List[TransactionItem] = []
    subtotal: float = 0.0
    tax: float = 0.0
    shipping: float = 0.0
    total: float = 0.0
    shipping_address: Dict[str, Any] = {}
    payment_method: str = ""
    payment_reference: Optional[str] = None


class TransactionCreate(BaseModel):
    items: List[TransactionItem]
    shipping_address: Dict[str, Any]
    payment_method: str
    payment_reference: Optional[str] = None


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


class ChatSearch(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    message_type: Optional[ChatMessageType] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
