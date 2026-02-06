from __future__ import annotations

from typing import Any, Optional

from azure.ai.projects.aio import AIProjectClient

from .config import settings
from .utils.azure_credential_utils import get_azure_credential_async

_async_cred: Optional[Any] = None
_async_client: Optional[AIProjectClient] = None


async def init_foundry_client(endpoint: Optional[str] = None) -> None:
    global _async_cred, _async_client
    if _async_client is not None:
        return

    endpoint = endpoint or settings.azure_foundry_endpoint
    if not endpoint:
        raise RuntimeError(
            "settings.azure_foundry_endpoint is empty. "
            "Set AZURE_FOUNDRY_ENDPOINT to your Azure AI Foundry Project endpoint."
        )

    client_id = str(settings.azure_client_id) if settings.azure_client_id else None
    _async_cred = await get_azure_credential_async(client_id=client_id)
    _async_client = AIProjectClient(endpoint=endpoint, credential=_async_cred)  # type: ignore


def get_foundry_client() -> AIProjectClient:
    if _async_client is None:
        raise RuntimeError(
            "Foundry client not initialized. Call init_foundry_client() at startup."
        )
    return _async_client


async def shutdown_foundry_client() -> None:
    global _async_client, _async_cred
    if _async_client is not None:
        try:
            await _async_client.close()
        finally:
            _async_client = None
    if _async_cred is not None:
        try:
            await _async_cred.close()
        finally:
            _async_cred = None
