from pydantic import BaseModel
from typing import List, Optional, Literal, Any, Dict

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None

class ChatResponse(BaseModel):
    text: str

class Product(BaseModel):
    id: int
    sku: str
    name: str
    description: str
    price: float
    image_url: str | None = None
    inventory: int

class ProductListResponse(BaseModel):
    items: List[Dict[str, Any]]
