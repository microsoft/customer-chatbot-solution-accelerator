from pydantic import BaseModel
import os

from pathlib import Path
from dotenv import load_dotenv

# Look for .env in backend/ first, then in repo root
HERE = Path(__file__).resolve().parent
for candidate in (HERE.parent / ".env", HERE.parent.parent / ".env"):
    if candidate.exists():
        load_dotenv(candidate, override=True)
        break

class Settings(BaseModel):
    # LLMs
    azure_openai_endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_deployment: str | None = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    azure_openai_api_key_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str | None = os.getenv("OPENAI_MODEL")

    # Data services
    sql_conn_str: str = os.getenv("SQL_CONNECTION_STRING", "")
    search_endpoint: str = os.getenv("AZURE_SEARCH_ENDPOINT", "")
    search_api_key: str = os.getenv("AZURE_SEARCH_API_KEY", "")
    search_index: str = os.getenv("AZURE_SEARCH_INDEX", "reference-docs")

    cosmos_endpoint: str = os.getenv("COSMOS_ENDPOINT", "")
    cosmos_key: str = os.getenv("COSMOS_KEY", "")
    cosmos_db: str = os.getenv("COSMOS_DB", "shop")
    cosmos_container: str = os.getenv("COSMOS_CONTAINER", "orders")
    cosmos_pk: str = os.getenv("COSMOS_PARTITION_KEY", "/customerId")

    # AI Foundry Agents
    foundry_product_agent_id : str = os.getenv("FOUNDRY_PRODUCT_AGENT_ID", "")
    foundry_order_agent_id : str = os.getenv("FOUNDRY_ORDER_AGENT_ID", "")
    foundry_customer_agent_id : str = os.getenv("FOUNDRY_CUSTOMER_AGENT_ID", "")
    foundry_knowledge_agent_id : str = os.getenv("FOUNDRY_KNOWLEDGE_AGENT_ID", "")
    foundry_orchestrator_agent_id : str = os.getenv("FOUNDRY_ORCHESTRATOR_AGENT_ID", "")


    # AI Foundry
    azure_foundry_endpoint: str | None = os.getenv("AZURE_FOUNDRY_ENDPOINT")


    # App
    app_host: str = os.getenv("APP_HOST", "0.0.0.0")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")

settings = Settings()