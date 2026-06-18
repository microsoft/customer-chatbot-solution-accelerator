import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_current_dir = Path(__file__).resolve().parent
_backend_dir = _current_dir.parent
_env_file_path = _backend_dir / ".env"
_ecommerce_dir = _backend_dir.parent
_repo_root_env = _ecommerce_dir.parent / ".env"

for _p in (_repo_root_env, _ecommerce_dir / ".env"):
    if _p.is_file():
        load_dotenv(_p, override=False)
if _env_file_path.is_file():
    load_dotenv(_env_file_path, override=True)


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
        raw = os.environ.get("ALLOWED_ORIGINS_STR")
        if raw is None or not str(raw).strip():
            raw = self.allowed_origins_str
        parts = [
            o.strip()
            for o in str(raw).split(",")
            if o.strip() and o.strip() != "*"
        ]
        return parts or ["http://localhost:5173", "http://localhost:3000"]

    # Azure Cosmos DB
    cosmos_db_endpoint: Optional[str] = None
    cosmos_db_database_name: str = "ecommerce_db"
    cosmos_db_containers: dict = {
        "products": "products",
        "users": "users",
        "carts": "carts",
        "chat_sessions": "chat_sessions",
        "transactions": "transactions",
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
    chat_api_url: Optional[str] = None
    payment_gateway_url: Optional[str] = None
    deployment_scenario: str = "ecommerce"

    class Config:
        env_file = str(_env_file_path)  # Use absolute path to .env file
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables


# Global settings instance
settings = Settings()


# Check if we have Cosmos DB configuration
def has_cosmos_db_config() -> bool:
    v = settings.cosmos_db_endpoint
    return v is not None and str(v).strip() != ""


# Check if we have Azure Search configuration
def has_search_config() -> bool:
    return settings.azure_search_endpoint is not None