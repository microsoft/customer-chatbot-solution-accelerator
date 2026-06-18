import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings

_current_dir = Path(__file__).parent
_env_file_path = _current_dir.parent / ".env"


class Settings(BaseSettings):
    app_name: str = "Customer Chat API"
    app_version: str = "1.0.0"
    debug: bool = False

    host: str = "0.0.0.0"
    port: int = 8000

    allowed_origins_str: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,"
        "http://localhost:3001,http://127.0.0.1:3001"
    )

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
        return parts or [
            o.strip()
            for o in self.allowed_origins_str.split(",")
            if o.strip()
        ]

    cosmos_db_endpoint: Optional[str] = None
    cosmos_db_database_name: str = "ecommerce_db"
    cosmos_db_containers: dict = {
        "products": "products",
        "users": "users",
        "chat_sessions": "chat_sessions",
        "carts": "carts",
        "transactions": "transactions",
    }

    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2025-01-01-preview"
    azure_openai_deployment_name: str = "gpt-4o-mini"

    azure_key_vault_url: Optional[str] = None

    azure_client_id: Optional[str] = None
    azure_client_secret: Optional[str] = None
    azure_tenant_id: Optional[str] = None

    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    azure_search_endpoint: Optional[str] = None
    azure_search_index: str = "reference-docs"
    azure_search_product_index: str = "products"

    azure_foundry_endpoint: Optional[str] = None
    foundry_chat_agent: str = ""
    foundry_product_agent: str = ""
    foundry_policy_agent: str = ""

    foundry_orchestrator_agent_id: str = ""
    foundry_product_agent_id: str = ""
    foundry_order_agent_id: str = ""
    foundry_knowledge_agent_id: str = ""

    azure_voicelive_endpoint: Optional[str] = None
    azure_voicelive_api_key: Optional[str] = None
    azure_voicelive_agent_name: str = ""
    azure_voicelive_project: str = ""
    voicelive_mode: str = "model"
    voicelive_model: str = "gpt-realtime-mini"
    voicelive_voice: str = "en-US-Ava:DragonHDLatestNeural"
    voicelive_transcribe_model: str = "gpt-4o-transcribe"
    voicelive_instructions: str = "You are a helpful AI assistant."
    voicelive_vad_threshold: float = 0.5
    voicelive_vad_silence_ms: int = 1200
    voicelive_vad_prefix_padding_ms: int = 300
    use_foundry_agents: bool = False

    deployment_scenario: str = "ecommerce"
    chat_welcome_title: str = ""
    chat_welcome_subtitle: str = ""
    azure_search_catalog_index: str = "products_index"
    azure_search_policies_index: str = "policies_index"

    class Config:
        env_file = str(_env_file_path)
        case_sensitive = False
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    return settings


def has_cosmos_db_config() -> bool:
    return settings.cosmos_db_endpoint is not None


def has_openai_config() -> bool:
    return (
        settings.azure_openai_endpoint is not None
        and settings.azure_openai_api_key is not None
    )


def has_entra_id_config() -> bool:
    return all(
        [
            settings.azure_client_id,
            settings.azure_client_secret,
            settings.azure_tenant_id,
        ]
    )


def has_azure_search_config() -> bool:
    return settings.azure_search_endpoint is not None


def has_azure_search_endpoint() -> bool:
    return settings.azure_search_endpoint is not None


def has_foundry_config() -> bool:
    return settings.azure_foundry_endpoint is not None and (
        settings.foundry_chat_agent != "" and settings.foundry_policy_agent != ""
    )
