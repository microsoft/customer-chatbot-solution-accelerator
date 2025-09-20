from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "E-commerce Chat API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: list = ["http://localhost:5173", "http://localhost:3000"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse ALLOWED_ORIGINS from environment if provided
        if os.getenv("ALLOWED_ORIGINS"):
            self.allowed_origins = [origin.strip() for origin in os.getenv("ALLOWED_ORIGINS").split(",")]
    
    # Azure Cosmos DB
    cosmos_db_endpoint: Optional[str] = None
    cosmos_db_key: Optional[str] = None
    cosmos_db_database_name: str = "ecommerce_db"
    cosmos_db_containers: dict = {
        "products": "products",
        "users": "users", 
        "chat_sessions": "chat_sessions",
        "carts": "carts",
        "transactions": "transactions"
    }
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = "https://testmodle.openai.azure.com/"
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2025-01-01-preview"
    azure_openai_deployment_name: str = "gpt-4o-mini"
    
    # Azure Key Vault
    azure_key_vault_url: Optional[str] = None
    
    # Microsoft Entra ID
    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Check if we have Cosmos DB configuration
def has_cosmos_db_config() -> bool:
    return settings.cosmos_db_endpoint is not None and settings.cosmos_db_key is not None

# Check if we have Azure OpenAI configuration
def has_openai_config() -> bool:
    return settings.azure_openai_endpoint is not None and settings.azure_openai_api_key is not None

# Check if we have Entra ID configuration
def has_entra_id_config() -> bool:
    return all([
        settings.azure_client_id,
        settings.azure_client_secret,
        settings.azure_tenant_id
    ])