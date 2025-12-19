import os
from unittest.mock import Mock, patch

import pytest
from app.utils.azure_credential_utils import (
    get_azure_credential,
    get_azure_credential_async,
)


class TestAzureCredentialUtils:
    """Test Azure credential utility functions"""

    @patch("app.utils.azure_credential_utils.DefaultAzureCredential")
    @patch.dict(os.environ, {"APP_ENV": "dev"})
    def test_get_azure_credential_dev_environment(self, mock_default_cred):
        """Test get_azure_credential in dev environment"""
        mock_cred_instance = Mock()
        mock_default_cred.return_value = mock_cred_instance

        result = get_azure_credential()

        mock_default_cred.assert_called_once()
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.DefaultAzureCredential")
    @patch.dict(os.environ, {"APP_ENV": "DEV"})
    def test_get_azure_credential_dev_case_insensitive(self, mock_default_cred):
        """Test get_azure_credential with uppercase DEV"""
        mock_cred_instance = Mock()
        mock_default_cred.return_value = mock_cred_instance

        result = get_azure_credential()

        mock_default_cred.assert_called_once()
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.ManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "prod"})
    def test_get_azure_credential_prod_environment(self, mock_managed_cred):
        """Test get_azure_credential in prod environment"""
        mock_cred_instance = Mock()
        mock_managed_cred.return_value = mock_cred_instance

        result = get_azure_credential()

        mock_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.ManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "staging"})
    def test_get_azure_credential_non_dev_environment(self, mock_managed_cred):
        """Test get_azure_credential in non-dev environment"""
        mock_cred_instance = Mock()
        mock_managed_cred.return_value = mock_cred_instance

        result = get_azure_credential()

        mock_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.ManagedIdentityCredential")
    @patch.dict(os.environ, {}, clear=True)
    def test_get_azure_credential_no_env_defaults_to_prod(self, mock_managed_cred):
        """Test get_azure_credential with no APP_ENV set (defaults to prod)"""
        mock_cred_instance = Mock()
        mock_managed_cred.return_value = mock_cred_instance

        result = get_azure_credential()

        mock_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.ManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "prod"})
    def test_get_azure_credential_with_client_id(self, mock_managed_cred):
        """Test get_azure_credential with client_id parameter"""
        mock_cred_instance = Mock()
        mock_managed_cred.return_value = mock_cred_instance
        test_client_id = "test-client-id-123"

        result = get_azure_credential(client_id=test_client_id)

        mock_managed_cred.assert_called_once_with(client_id=test_client_id)
        assert result == mock_cred_instance

    @patch("app.utils.azure_credential_utils.DefaultAzureCredential")
    @patch.dict(os.environ, {"APP_ENV": "dev"})
    def test_get_azure_credential_dev_with_client_id_ignored(self, mock_default_cred):
        """Test get_azure_credential in dev - client_id is ignored"""
        mock_cred_instance = Mock()
        mock_default_cred.return_value = mock_cred_instance

        result = get_azure_credential(client_id="ignored-in-dev")

        mock_default_cred.assert_called_once()
        assert result == mock_cred_instance


class TestAzureCredentialUtilsAsync:
    """Test async Azure credential utility functions"""

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioDefaultAzureCredential")
    @patch.dict(os.environ, {"APP_ENV": "dev"})
    async def test_get_azure_credential_async_dev_environment(
        self, mock_aio_default_cred
    ):
        """Test get_azure_credential_async in dev environment"""
        mock_cred_instance = Mock()
        mock_aio_default_cred.return_value = mock_cred_instance

        result = await get_azure_credential_async()

        mock_aio_default_cred.assert_called_once()
        assert result == mock_cred_instance

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "Development"})
    async def test_get_azure_credential_async_non_dev_environment(
        self, mock_aio_managed_cred
    ):
        """Test get_azure_credential_async with non-dev environment"""
        mock_cred_instance = Mock()
        mock_aio_managed_cred.return_value = mock_cred_instance

        result = await get_azure_credential_async()

        mock_aio_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "production"})
    async def test_get_azure_credential_async_prod_environment(
        self, mock_aio_managed_cred
    ):
        """Test get_azure_credential_async in prod environment"""
        mock_cred_instance = Mock()
        mock_aio_managed_cred.return_value = mock_cred_instance

        result = await get_azure_credential_async()

        mock_aio_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioManagedIdentityCredential")
    @patch.dict(os.environ, {}, clear=True)
    async def test_get_azure_credential_async_no_env_defaults_to_prod(
        self, mock_aio_managed_cred
    ):
        """Test get_azure_credential_async with no APP_ENV set"""
        mock_cred_instance = Mock()
        mock_aio_managed_cred.return_value = mock_cred_instance

        result = await get_azure_credential_async()

        mock_aio_managed_cred.assert_called_once_with(client_id=None)
        assert result == mock_cred_instance

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioManagedIdentityCredential")
    @patch.dict(os.environ, {"APP_ENV": "prod"})
    async def test_get_azure_credential_async_with_client_id(
        self, mock_aio_managed_cred
    ):
        """Test get_azure_credential_async with client_id parameter"""
        mock_cred_instance = Mock()
        mock_aio_managed_cred.return_value = mock_cred_instance
        test_client_id = "async-client-id-456"

        result = await get_azure_credential_async(client_id=test_client_id)

        mock_aio_managed_cred.assert_called_once_with(client_id=test_client_id)
        assert result == mock_cred_instance

    @pytest.mark.asyncio
    @patch("app.utils.azure_credential_utils.AioDefaultAzureCredential")
    @patch.dict(os.environ, {"APP_ENV": "dev"})
    async def test_get_azure_credential_async_dev_client_id_ignored(
        self, mock_aio_default_cred
    ):
        """Test get_azure_credential_async in dev - client_id ignored"""
        mock_cred_instance = Mock()
        mock_aio_default_cred.return_value = mock_cred_instance

        result = await get_azure_credential_async(client_id="ignored-in-dev")

        mock_aio_default_cred.assert_called_once()
        assert result == mock_cred_instance


def test_environment_variable_edge_cases():
    """Test edge cases with environment variable handling"""

    # Test empty string
    with patch.dict(os.environ, {"APP_ENV": ""}):
        with patch(
            "app.utils.azure_credential_utils.ManagedIdentityCredential"
        ) as mock_managed:
            mock_managed.return_value = Mock()
            get_azure_credential()
            mock_managed.assert_called_once_with(client_id=None)

    # Test whitespace - this will actually use ManagedIdentityCredential since '  dev  '.lower() != 'dev'
    with patch.dict(os.environ, {"APP_ENV": "  dev  "}):
        with patch(
            "app.utils.azure_credential_utils.ManagedIdentityCredential"
        ) as mock_managed:
            mock_managed.return_value = Mock()
            get_azure_credential()
            # Whitespace should not be stripped, so this goes to prod path
            mock_managed.assert_called_once_with(client_id=None)
