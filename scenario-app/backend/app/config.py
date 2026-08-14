import asyncio
import logging
import os
from pathlib import Path
from typing import List, Optional

from cachetools import TTLCache
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

_current_dir = Path(__file__).resolve().parent
_backend_dir = _current_dir.parent
_env_file_path = _backend_dir / ".env"
_scenario_app_dir = _backend_dir.parent
_repo_root_env = _scenario_app_dir.parent / ".env"

for _p in (_repo_root_env, _scenario_app_dir / ".env"):
    if _p.is_file():
        load_dotenv(_p, override=False)
if _env_file_path.is_file():
    load_dotenv(_env_file_path, override=True)


class Settings(BaseSettings):
    # Application
    app_name: str = "Scenario API"
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


settings = Settings()

_config_logger = logging.getLogger(__name__)


class ExpCache(TTLCache):
    """Extended TTLCache that deletes Azure AI Foundry conversations when items expire or are evicted."""

    def __init__(self, maxsize: int, ttl: float):
        super().__init__(maxsize=maxsize, ttl=ttl)
        self._foundry_endpoint: str = ""
        self._azure_client_id: Optional[str] = None

    def configure(self, foundry_endpoint: str, azure_client_id: Optional[str] = None) -> None:
        self._foundry_endpoint = foundry_endpoint
        self._azure_client_id = azure_client_id

    def expire(self, time=None):
        """Remove expired items and delete associated Foundry conversations."""
        items = super().expire(time)
        for key, conv_id in items:
            try:
                asyncio.create_task(self._delete_conversation_async(conv_id))
                _config_logger.info("Scheduled conversation deletion: %s", conv_id)
            except RuntimeError:
                pass  # No running event loop
            except Exception as e:
                _config_logger.error("Failed to schedule deletion for key %s: %s", key, e)
        return items

    def popitem(self):
        """Remove LRU item and delete associated Foundry conversation."""
        key, conv_id = super().popitem()
        try:
            asyncio.create_task(self._delete_conversation_async(conv_id))
            _config_logger.info("Scheduled conversation deletion (LRU evict): %s", conv_id)
        except RuntimeError:
            pass  # No running event loop
        except Exception as e:
            _config_logger.error("Failed to schedule deletion for key %s (LRU evict): %s", key, e)
        return key, conv_id

    async def _delete_conversation_async(self, conv_id: str) -> None:
        """Asynchronously delete a Foundry conversation with proper resource cleanup."""
        credential = None
        try:
            if not conv_id or not self._foundry_endpoint:
                return
            # Response IDs (resp_xxx) are managed by the API — skip deletion
            if conv_id.startswith("resp_"):
                _config_logger.info("Skipping deletion for response ID: %s", conv_id)
                return

            from azure.ai.projects.aio import AIProjectClient

            try:
                from .utils.azure_credential_utils import get_azure_credential_async
            except ImportError:
                from app.utils.azure_credential_utils import get_azure_credential_async

            credential = await get_azure_credential_async(client_id=self._azure_client_id)
            async with AIProjectClient(
                endpoint=self._foundry_endpoint, credential=credential
            ) as project_client:
                openai_client = project_client.get_openai_client()
                try:
                    await openai_client.conversations.delete(conversation_id=conv_id)
                    _config_logger.info("Conversation deleted successfully: %s", conv_id)
                finally:
                    await openai_client.close()
        except Exception as e:
            _config_logger.error("Failed to delete conversation %s: %s", conv_id, e)
        finally:
            if credential is not None:
                await credential.close()


# Shared cache mapping session_id -> Azure AI conversation_id (conv_xxx)
# Used by both text chat (chat.py) and voice (foundry_agent_utils.py)
conversation_cache: ExpCache = ExpCache(maxsize=1000, ttl=3600.0)


# Check if we have Azure Cosmos DB configuration
def has_cosmos_db_config() -> bool:
    v = settings.cosmos_db_endpoint
    return v is not None and str(v).strip() != ""


# Check if we have Azure Search configuration
def has_search_config() -> bool:
    return settings.azure_search_endpoint is not None
