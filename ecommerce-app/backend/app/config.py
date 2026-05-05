from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

# Get the absolute path to the .env file
_current_dir = Path(__file__).parent  # This is the app directory
_env_file_path = _current_dir.parent / ".env"  # Go up one level to backend/.env


class Settings(BaseSettings):
    # Application
    app_name: str = "E-commerce API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS - Use string type to avoid JSON parsing issues
    allowed_origins_str: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins(self) -> List[str]:
        """Parse allowed origins from comma-separated string"""
        return [
            origin.strip()
            for origin in self.allowed_origins_str.split(",")
            if origin.strip()
        ]

    # Azure Cosmos DB
    cosmos_db_endpoint: Optional[str] = None
    cosmos_db_database_name: str = "ecommerce_db"
    cosmos_db_containers: dict = {
        "products": "products",
        "users": "users",
        "carts": "carts",
        "orders": "orders",
        "customers": "customers",
    }

    # Azure Search (for product search)
    azure_search_endpoint: Optional[str] = None
    azure_search_product_index: str = "products"

    # Microsoft Entra ID
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds

    # External Service Integration
    chat_api_url: Optional[str] = None  # URL to chat application API
    payment_gateway_url: Optional[str] = None

    class Config:
        env_file = str(_env_file_path)  # Use absolute path to .env file
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables


# Global settings instance
settings = Settings()


# Check if we have Cosmos DB configuration
def has_cosmos_db_config() -> bool:
    return settings.cosmos_db_endpoint is not None


# Check if we have Azure Search configuration
def has_search_config() -> bool:
    return settings.azure_search_endpoint is not None