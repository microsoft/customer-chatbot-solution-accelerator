from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

# Get the absolute path to the .env file
_current_dir = Path(__file__).parent  # This is the app directory
_env_file_path = _current_dir.parent / ".env"  # Go up one level to src/api/.env

class Settings(BaseSettings):
    # Application
    app_name: str = "E-commerce Chat API"
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
        return [origin.strip() for origin in self.allowed_origins_str.split(",") if origin.strip()]
    
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
    
    # Semantic Kernel
    use_semantic_kernel: bool = True
    semantic_kernel_plugins: List[str] = ["product", "reference", "orders"]
    handoff_orchestration_enabled: bool = True
    use_simple_router: bool = False  # Set to True to use simple router instead of handoff orchestration
    
    # Azure Search (for reference plugin)
    azure_search_endpoint: Optional[str] = None
    azure_search_api_key: Optional[str] = None
    azure_search_index: str = "reference-docs"
    azure_search_product_index: str = "products"
    
    # Azure AI Foundry
    azure_foundry_endpoint: Optional[str] = None
    foundry_orchestrator_agent_id: str = ""
    foundry_product_agent_id: str = ""
    foundry_order_agent_id: str = ""
    foundry_customer_agent_id: str = ""
    foundry_knowledge_agent_id: str = ""
    
    # Additional custom agent IDs
    foundry_chat_agent_id: str = ""
    foundry_custom_product_agent_id: str = ""
    foundry_policy_agent_id: str = ""
    
    # Feature Flags
    use_foundry_agents: bool = False
    
    class Config:
        env_file = str(_env_file_path)  # Use absolute path to .env file
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables

# Global settings instance
settings = Settings()

# Check if we have Cosmos DB configuration
def has_cosmos_db_config() -> bool:
    return settings.cosmos_db_endpoint is not None #and settings.cosmos_db_key is not None

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

# Check if we have Azure Search configuration (AAD authentication)
def has_azure_search_config() -> bool:
    return settings.azure_search_endpoint is not None

# Legacy function for backwards compatibility (now only checks endpoint)
def has_azure_search_endpoint() -> bool:
    return settings.azure_search_endpoint is not None

# Check if semantic kernel is properly configured
def has_semantic_kernel_config() -> bool:
    return has_openai_config() and settings.use_semantic_kernel

# Check if Azure AI Foundry is configured
def has_foundry_config() -> bool:
    return (
        settings.azure_foundry_endpoint is not None 
        and (
            settings.foundry_orchestrator_agent_id != "" or
            settings.foundry_product_agent_id != "" or
            settings.foundry_order_agent_id != "" or
            settings.foundry_knowledge_agent_id != ""
        )
    )