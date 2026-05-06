"""
Tests for app.utils.foundry_agent_utils — call_foundry_agent function.
"""
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_foundry_agent_empty_endpoint():
    """Returns error message when foundry_endpoint is empty."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    result = await call_foundry_agent(
        question="What colors?",
        foundry_endpoint="",
        chat_agent_name="chat",
        product_agent_name="product",
        policy_agent_name="policy",
    )
    assert "not configured" in result.lower()


@pytest.mark.asyncio
async def test_foundry_agent_missing_agent_names():
    """Returns error when any agent name is missing."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    result = await call_foundry_agent(
        question="What colors?",
        foundry_endpoint="https://foundry.test",
        chat_agent_name="chat",
        product_agent_name="",
        policy_agent_name="policy",
    )
    assert "not fully configured" in result.lower()


@pytest.mark.asyncio
async def test_foundry_agent_missing_all_agent_names():
    """Returns error when all agent names are empty."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    result = await call_foundry_agent(
        question="test",
        foundry_endpoint="https://foundry.test",
        chat_agent_name="",
        product_agent_name="",
        policy_agent_name="",
    )
    assert "not fully configured" in result.lower()


@pytest.mark.asyncio
async def test_foundry_agent_success_with_text():
    """Successful call returns agent text response."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    mock_credential = AsyncMock()
    mock_credential.__aenter__ = AsyncMock(return_value=mock_credential)
    mock_credential.__aexit__ = AsyncMock(return_value=False)

    mock_result = MagicMock()
    mock_result.text = "Here are the paint colors available."

    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)
    mock_agent.as_tool = MagicMock(return_value=MagicMock())

    mock_provider = AsyncMock()
    mock_provider.get_agent = AsyncMock(return_value=mock_agent)
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)

    mock_project_client = AsyncMock()
    mock_project_client.__aenter__ = AsyncMock(return_value=mock_project_client)
    mock_project_client.__aexit__ = AsyncMock(return_value=False)

    # These are imported lazily inside call_foundry_agent — inject via sys.modules
    mock_framework = MagicMock()
    mock_framework.AzureAIProjectAgentProvider = MagicMock(return_value=mock_provider)
    mock_ai_projects = MagicMock()
    mock_ai_projects.AIProjectClient = MagicMock(return_value=mock_project_client)

    with patch.dict(sys.modules, {
        "agent_framework_azure_ai": mock_framework,
        "azure.ai.projects.aio": mock_ai_projects,
    }), patch("app.utils.azure_credential_utils.get_azure_credential_async", new_callable=AsyncMock) as mock_get_cred:
        mock_get_cred.return_value = mock_credential

        result = await call_foundry_agent(
            question="What paint colors?",
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat-agent",
            product_agent_name="product-agent",
            policy_agent_name="policy-agent",
            azure_client_id="test-id",
        )

    assert result == "Here are the paint colors available."


@pytest.mark.asyncio
async def test_foundry_agent_success_str_result():
    """When result has no .text attribute, returns str(result)."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    mock_credential = AsyncMock()
    mock_credential.__aenter__ = AsyncMock(return_value=mock_credential)
    mock_credential.__aexit__ = AsyncMock(return_value=False)

    mock_result = "Plain string result"

    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=mock_result)
    mock_agent.as_tool = MagicMock(return_value=MagicMock())

    mock_provider = AsyncMock()
    mock_provider.get_agent = AsyncMock(return_value=mock_agent)
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)

    mock_project_client = AsyncMock()
    mock_project_client.__aenter__ = AsyncMock(return_value=mock_project_client)
    mock_project_client.__aexit__ = AsyncMock(return_value=False)

    mock_framework = MagicMock()
    mock_framework.AzureAIProjectAgentProvider = MagicMock(return_value=mock_provider)
    mock_ai_projects = MagicMock()
    mock_ai_projects.AIProjectClient = MagicMock(return_value=mock_project_client)

    with patch.dict(sys.modules, {
        "agent_framework_azure_ai": mock_framework,
        "azure.ai.projects.aio": mock_ai_projects,
    }), patch("app.utils.azure_credential_utils.get_azure_credential_async", new_callable=AsyncMock) as mock_get_cred:
        mock_get_cred.return_value = mock_credential

        result = await call_foundry_agent(
            question="test",
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat",
            product_agent_name="product",
            policy_agent_name="policy",
        )

    assert result == "Plain string result"


@pytest.mark.asyncio
async def test_foundry_agent_none_result():
    """When agent returns None, returns 'No response' message."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    mock_credential = AsyncMock()
    mock_credential.__aenter__ = AsyncMock(return_value=mock_credential)
    mock_credential.__aexit__ = AsyncMock(return_value=False)

    mock_agent = AsyncMock()
    mock_agent.run = AsyncMock(return_value=None)
    mock_agent.as_tool = MagicMock(return_value=MagicMock())

    mock_provider = AsyncMock()
    mock_provider.get_agent = AsyncMock(return_value=mock_agent)
    mock_provider.__aenter__ = AsyncMock(return_value=mock_provider)
    mock_provider.__aexit__ = AsyncMock(return_value=False)

    mock_project_client = AsyncMock()
    mock_project_client.__aenter__ = AsyncMock(return_value=mock_project_client)
    mock_project_client.__aexit__ = AsyncMock(return_value=False)

    mock_framework = MagicMock()
    mock_framework.AzureAIProjectAgentProvider = MagicMock(return_value=mock_provider)
    mock_ai_projects = MagicMock()
    mock_ai_projects.AIProjectClient = MagicMock(return_value=mock_project_client)

    with patch.dict(sys.modules, {
        "agent_framework_azure_ai": mock_framework,
        "azure.ai.projects.aio": mock_ai_projects,
    }), patch("app.utils.azure_credential_utils.get_azure_credential_async", new_callable=AsyncMock) as mock_get_cred:
        mock_get_cred.return_value = mock_credential

        result = await call_foundry_agent(
            question="test",
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat",
            product_agent_name="product",
            policy_agent_name="policy",
        )

    assert "no response" in result.lower()


@pytest.mark.asyncio
async def test_foundry_agent_exception():
    """When an exception occurs during the call, returns error message."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    mock_credential = AsyncMock()
    mock_credential.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
    mock_credential.__aexit__ = AsyncMock(return_value=False)

    mock_framework = MagicMock()
    mock_ai_projects = MagicMock()

    with patch.dict(sys.modules, {
        "agent_framework_azure_ai": mock_framework,
        "azure.ai.projects.aio": mock_ai_projects,
    }), patch("app.utils.azure_credential_utils.get_azure_credential_async", new_callable=AsyncMock) as mock_get_cred:
        mock_get_cred.return_value = mock_credential

        result = await call_foundry_agent(
            question="test",
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat",
            product_agent_name="product",
            policy_agent_name="policy",
        )

    assert "error" in result.lower()
