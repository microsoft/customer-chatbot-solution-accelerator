"""Tests for app.config module"""
from unittest.mock import patch


class TestConfigFunctions:
    """Test configuration check functions"""

    def test_has_cosmos_db_config_true(self):
        """Test has_cosmos_db_config returns True when endpoint is configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.cosmos_db_endpoint = "https://test.documents.azure.com:443/"
            # Need to reimport to use the patched settings
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_cosmos_db_config()
                assert result is True

    def test_has_cosmos_db_config_false(self):
        """Test has_cosmos_db_config returns False when endpoint is not configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.cosmos_db_endpoint = None
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_cosmos_db_config()
                assert result is False

    def test_has_entra_id_config_true(self):
        """Test has_entra_id_config returns True when all Entra ID settings are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_client_id = "test-client-id"
            mock_settings.azure_client_secret = "test-client-secret"
            mock_settings.azure_tenant_id = "test-tenant-id"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_entra_id_config()
                assert result is True

    def test_has_entra_id_config_false_missing_client_id(self):
        """Test has_entra_id_config returns False when client_id is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_client_id = None
            mock_settings.azure_client_secret = "test-client-secret"
            mock_settings.azure_tenant_id = "test-tenant-id"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_entra_id_config()
                assert result is False

    def test_has_entra_id_config_false_missing_secret(self):
        """Test has_entra_id_config returns False when client_secret is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_client_id = "test-client-id"
            mock_settings.azure_client_secret = None
            mock_settings.azure_tenant_id = "test-tenant-id"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_entra_id_config()
                assert result is False

    def test_has_entra_id_config_false_missing_tenant(self):
        """Test has_entra_id_config returns False when tenant_id is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_client_id = "test-client-id"
            mock_settings.azure_client_secret = "test-client-secret"
            mock_settings.azure_tenant_id = None
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_entra_id_config()
                assert result is False

    def test_has_azure_search_config_true(self):
        """Test has_azure_search_config returns True when endpoint is configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_search_endpoint = "https://test.search.windows.net"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_azure_search_config()
                assert result is True

    def test_has_azure_search_config_false(self):
        """Test has_azure_search_config returns False when endpoint is not configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_search_endpoint = None
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_azure_search_config()
                assert result is False

    def test_has_azure_search_endpoint_true(self):
        """Test has_azure_search_endpoint returns True when endpoint is configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_search_endpoint = "https://test.search.windows.net"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_azure_search_endpoint()
                assert result is True

    def test_has_azure_search_endpoint_false(self):
        """Test has_azure_search_endpoint returns False when endpoint is not configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_search_endpoint = None
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_azure_search_endpoint()
                assert result is False

    def test_has_foundry_config_true_with_chat_agent(self):
        """Test has_foundry_config returns True when endpoint and chat agent are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_foundry_endpoint = "https://test.api.azureml.ms"
            mock_settings.foundry_chat_agent = "chat-agent-id"
            mock_settings.foundry_product_agent = ""
            mock_settings.foundry_policy_agent = ""
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_foundry_config()
                assert result is True

    def test_has_foundry_config_true_with_product_agent(self):
        """Test has_foundry_config returns True when endpoint and product agent are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_foundry_endpoint = "https://test.api.azureml.ms"
            mock_settings.foundry_chat_agent = ""
            mock_settings.foundry_product_agent = "product-agent-id"
            mock_settings.foundry_policy_agent = ""
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_foundry_config()
                assert result is True

    def test_has_foundry_config_true_with_policy_agent(self):
        """Test has_foundry_config returns True when endpoint and policy agent are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_foundry_endpoint = "https://test.api.azureml.ms"
            mock_settings.foundry_chat_agent = ""
            mock_settings.foundry_product_agent = ""
            mock_settings.foundry_policy_agent = "policy-agent-id"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_foundry_config()
                assert result is True

    def test_has_foundry_config_false_no_endpoint(self):
        """Test has_foundry_config returns False when endpoint is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_foundry_endpoint = None
            mock_settings.foundry_chat_agent = "chat-agent-id"
            mock_settings.foundry_product_agent = ""
            mock_settings.foundry_policy_agent = ""
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_foundry_config()
                assert result is False

    def test_has_foundry_config_false_no_agents(self):
        """Test has_foundry_config returns False when no agents are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_foundry_endpoint = "https://test.api.azureml.ms"
            mock_settings.foundry_chat_agent = ""
            mock_settings.foundry_product_agent = ""
            mock_settings.foundry_policy_agent = ""
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_foundry_config()
                assert result is False

    def test_has_openai_config_true(self):
        """Test has_openai_config returns True when both endpoint and api_key are configured"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
            mock_settings.azure_openai_api_key = "test-api-key"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_openai_config()
                assert result is True

    def test_has_openai_config_false_no_endpoint(self):
        """Test has_openai_config returns False when endpoint is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_openai_endpoint = None
            mock_settings.azure_openai_api_key = "test-api-key"
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_openai_config()
                assert result is False

    def test_has_openai_config_false_no_api_key(self):
        """Test has_openai_config returns False when api_key is missing"""
        with patch("app.config.settings") as mock_settings:
            mock_settings.azure_openai_endpoint = "https://test.openai.azure.com"
            mock_settings.azure_openai_api_key = None
            import app.config
            with patch.object(app.config, "settings", mock_settings):
                result = app.config.has_openai_config()
                assert result is False


class TestSettingsProperties:
    """Test Settings class properties"""

    def test_allowed_origins_parses_comma_separated_string(self):
        """Test allowed_origins property parses comma-separated origins"""
        from app.config import Settings

        settings = Settings(allowed_origins_str="http://localhost:5173,http://localhost:3000")
        origins = settings.allowed_origins

        assert len(origins) == 2
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins

    def test_allowed_origins_handles_whitespace(self):
        """Test allowed_origins property strips whitespace"""
        from app.config import Settings

        settings = Settings(allowed_origins_str="  http://localhost:5173  ,  http://localhost:3000  ")
        origins = settings.allowed_origins

        assert len(origins) == 2
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins

    def test_allowed_origins_handles_empty_entries(self):
        """Test allowed_origins property filters empty entries"""
        from app.config import Settings

        settings = Settings(allowed_origins_str="http://localhost:5173,,http://localhost:3000,")
        origins = settings.allowed_origins

        assert len(origins) == 2
        assert "http://localhost:5173" in origins
        assert "http://localhost:3000" in origins

    def test_allowed_origins_single_origin(self):
        """Test allowed_origins property with single origin"""
        from app.config import Settings

        settings = Settings(allowed_origins_str="http://localhost:5173")
        origins = settings.allowed_origins

        assert len(origins) == 1
        assert "http://localhost:5173" in origins
