from unittest.mock import AsyncMock, patch

import app.foundry_client as fc
import pytest
from app.foundry_client import (get_foundry_client, init_foundry_client,
                                shutdown_foundry_client)

# ============================================================================
# Tests for init_foundry_client
# ============================================================================


@pytest.mark.asyncio
@patch("app.foundry_client.settings")
@patch("app.foundry_client.DefaultAzureCredential")
@patch("app.foundry_client.AIProjectClient")
async def test_init_foundry_client_success(
    mock_ai_client, mock_credential, mock_settings
):
    """Test successful initialization of Foundry client"""

    fc._async_cred = None
    fc._async_client = None

    # Mock settings
    mock_settings.azure_foundry_endpoint = "https://test-foundry.azure.com"

    # Mock credential and client
    mock_cred_instance = AsyncMock()
    mock_credential.return_value = mock_cred_instance

    mock_client_instance = AsyncMock()
    mock_ai_client.return_value = mock_client_instance

    # Initialize
    await init_foundry_client()

    # Verify
    mock_credential.assert_called_once()
    mock_ai_client.assert_called_once_with(
        endpoint="https://test-foundry.azure.com", credential=mock_cred_instance
    )
    assert fc._async_cred == mock_cred_instance
    assert fc._async_client == mock_client_instance


@pytest.mark.asyncio
@patch("app.foundry_client.settings")
@patch("app.foundry_client.DefaultAzureCredential")
@patch("app.foundry_client.AIProjectClient")
async def test_init_foundry_client_custom_endpoint(
    mock_ai_client, mock_credential, mock_settings
):
    """Test initialization with custom endpoint parameter"""

    fc._async_cred = None
    fc._async_client = None

    # Mock settings
    mock_settings.azure_foundry_endpoint = "https://default-foundry.azure.com"

    # Mock credential and client
    mock_cred_instance = AsyncMock()
    mock_credential.return_value = mock_cred_instance

    mock_client_instance = AsyncMock()
    mock_ai_client.return_value = mock_client_instance

    # Initialize with custom endpoint
    custom_endpoint = "https://custom-foundry.azure.com"
    await init_foundry_client(endpoint=custom_endpoint)

    # Verify custom endpoint was used
    mock_ai_client.assert_called_once_with(
        endpoint=custom_endpoint, credential=mock_cred_instance
    )


@pytest.mark.asyncio
@patch("app.foundry_client.settings")
async def test_init_foundry_client_no_endpoint(mock_settings):
    """Test initialization fails when endpoint is missing"""

    fc._async_cred = None
    fc._async_client = None

    # Mock settings with empty endpoint
    mock_settings.azure_foundry_endpoint = None

    # Verify exception is raised
    with pytest.raises(RuntimeError) as exc_info:
        await init_foundry_client()

    assert "azure_foundry_endpoint is empty" in str(exc_info.value)
    assert "AZURE_FOUNDRY_ENDPOINT" in str(exc_info.value)


@pytest.mark.asyncio
@patch("app.foundry_client.settings")
@patch("app.foundry_client.DefaultAzureCredential")
@patch("app.foundry_client.AIProjectClient")
async def test_init_foundry_client_already_initialized(
    mock_ai_client, mock_credential, mock_settings
):
    """Test initialization is skipped when client already exists"""

    existing_client = AsyncMock()
    fc._async_client = existing_client

    # Mock settings
    mock_settings.azure_foundry_endpoint = "https://test-foundry.azure.com"

    # Initialize again
    await init_foundry_client()

    # Verify no new client was created
    mock_credential.assert_not_called()
    mock_ai_client.assert_not_called()
    assert fc._async_client == existing_client


# ============================================================================
# Tests for get_foundry_client
# ============================================================================


def test_get_foundry_client_success():
    """Test successful retrieval of initialized client"""

    mock_client = AsyncMock()
    fc._async_client = mock_client

    # Get client
    result = get_foundry_client()

    # Verify
    assert result == mock_client


def test_get_foundry_client_not_initialized():
    """Test getting client when not initialized raises error"""

    fc._async_client = None

    # Verify exception is raised
    with pytest.raises(RuntimeError) as exc_info:
        get_foundry_client()

    assert "not initialized" in str(exc_info.value)
    assert "init_foundry_client()" in str(exc_info.value)


# ============================================================================
# Tests for shutdown_foundry_client
# ============================================================================


@pytest.mark.asyncio
async def test_shutdown_foundry_client_both_exist():
    """Test shutdown when both client and credential exist"""

    mock_client = AsyncMock()
    mock_cred = AsyncMock()
    fc._async_client = mock_client
    fc._async_cred = mock_cred

    # Shutdown
    await shutdown_foundry_client()

    # Verify close was called
    mock_client.close.assert_called_once()
    mock_cred.close.assert_called_once()

    # Verify globals are reset
    assert fc._async_client is None
    assert fc._async_cred is None


@pytest.mark.asyncio
async def test_shutdown_foundry_client_already_shutdown():
    """Test shutdown when both are already None"""

    fc._async_client = None
    fc._async_cred = None

    # Shutdown (should not raise error)
    await shutdown_foundry_client()

    # Verify still None
    assert fc._async_client is None
    assert fc._async_cred is None
