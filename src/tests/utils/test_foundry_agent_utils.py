"""
Tests for app.utils.foundry_agent_utils — call_foundry_agent function.
"""
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _function_call_result(name, arguments):
    """Build a run-result whose message contains a single function_call content."""
    content = SimpleNamespace(type="function_call", name=name, arguments=arguments)
    message = SimpleNamespace(contents=[content])
    return SimpleNamespace(messages=[message], text="")


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
    """Returns error when required chat agent name is missing."""
    from app.utils.foundry_agent_utils import call_foundry_agent

    result = await call_foundry_agent(
        question="What colors?",
        foundry_endpoint="https://foundry.test",
        chat_agent_name="",
        product_agent_name="product",
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

    mock_parent_framework = MagicMock()
    mock_parent_framework.__path__ = []

    with patch.dict(sys.modules, {
        "agent_framework": mock_parent_framework,
        "agent_framework.azure": mock_framework,
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

    mock_parent_framework = MagicMock()
    mock_parent_framework.__path__ = []

    with patch.dict(sys.modules, {
        "agent_framework": mock_parent_framework,
        "agent_framework.azure": mock_framework,
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

    mock_parent_framework = MagicMock()
    mock_parent_framework.__path__ = []

    with patch.dict(sys.modules, {
        "agent_framework": mock_parent_framework,
        "agent_framework.azure": mock_framework,
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

    mock_parent_framework = MagicMock()
    mock_parent_framework.__path__ = []

    with patch.dict(sys.modules, {
        "agent_framework": mock_parent_framework,
        "agent_framework.azure": mock_framework,
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


# ---------------------------------------------------------------------------
# Routing-path helpers (used when agent_framework.azure provider is unavailable)
# ---------------------------------------------------------------------------


def test_strip_citations_removes_markers():
    """Azure AI Search citation markers are stripped and spacing tidied."""
    from app.utils.foundry_agent_utils import _strip_citations

    text = "Warranty is 2 years\u30104:0\u2020source\u3011 for all paints\u30102:1\u2020source\u3011."
    assert _strip_citations(text) == "Warranty is 2 years for all paints."


def test_strip_citations_tidies_space_before_punctuation():
    """A marker sitting before punctuation does not leave a dangling space."""
    from app.utils.foundry_agent_utils import _strip_citations

    assert _strip_citations("Price is great \u30100:0\u2020source\u3011!") == "Price is great!"


def test_strip_citations_passthrough_and_empty():
    """Text without markers is returned unchanged; falsy input is preserved."""
    from app.utils.foundry_agent_utils import _strip_citations

    assert _strip_citations("No citations here.") == "No citations here."
    assert _strip_citations("") == ""


def test_result_text_extracts_and_strips():
    """_result_text reads .text and applies citation stripping."""
    from app.utils.foundry_agent_utils import _result_text

    result = SimpleNamespace(text="Hello\u30101:0\u2020source\u3011")
    assert _result_text(result) == "Hello"
    assert _result_text(None) == ""


def test_extract_subagent_call_parses_name_and_task():
    """A product/policy function_call yields its tool name and task argument."""
    from app.utils.foundry_agent_utils import _extract_subagent_call

    result = _function_call_result("product_agent", '{"task": "find blue paint"}')
    assert _extract_subagent_call(result) == ("product_agent", "find blue paint")


def test_extract_subagent_call_query_fallback_and_bad_json():
    """Falls back to 'query' arg and tolerates malformed argument JSON."""
    from app.utils.foundry_agent_utils import _extract_subagent_call

    assert _extract_subagent_call(
        _function_call_result("policy_agent", '{"query": "returns"}')
    ) == ("policy_agent", "returns")
    assert _extract_subagent_call(
        _function_call_result("policy_agent", "not-json")
    ) == ("policy_agent", "")


def test_extract_subagent_call_none_when_no_match():
    """Returns None for unrecognised tools or when there is no function_call."""
    from app.utils.foundry_agent_utils import _extract_subagent_call

    assert _extract_subagent_call(_function_call_result("other_tool", "{}")) is None
    assert _extract_subagent_call(SimpleNamespace(messages=[])) is None


def _foundry_agent_factory(run_results):
    """Build a FoundryAgent mock whose async-context run() returns queued results."""
    calls = []

    def _make(*_args, **kwargs):
        agent = AsyncMock()
        agent.__aenter__ = AsyncMock(return_value=agent)
        agent.__aexit__ = AsyncMock(return_value=False)
        agent.run = AsyncMock(return_value=run_results[len(calls)])
        calls.append(kwargs.get("agent_name"))
        return agent

    return MagicMock(side_effect=_make), calls


@pytest.mark.asyncio
async def test_run_foundry_chat_with_routing_executes_subagent():
    """When the chat agent routes to product_agent, the sub-agent text is returned (stripped)."""
    from app.utils import foundry_agent_utils

    chat_result = _function_call_result("product_agent", '{"task": "blue paint"}')
    sub_result = SimpleNamespace(text="Cloud Drift, $59.5\u30104:0\u2020source\u3011")
    factory, calls = _foundry_agent_factory([chat_result, sub_result])

    mock_foundry_module = MagicMock()
    mock_foundry_module.FoundryAgent = factory

    with patch.dict(sys.modules, {"agent_framework.foundry": mock_foundry_module}):
        result = await foundry_agent_utils._run_foundry_chat_with_routing(
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat-agent",
            product_agent_name="product-agent",
            policy_agent_name="policy-agent",
            question="show me blue paint",
            credential=AsyncMock(),
        )

    assert result == "Cloud Drift, $59.5"
    assert calls == ["chat-agent", "product-agent"]


@pytest.mark.asyncio
async def test_run_foundry_chat_with_routing_no_call_returns_chat_text():
    """When the chat agent emits no sub-agent call, its own text is returned."""
    from app.utils import foundry_agent_utils

    chat_result = SimpleNamespace(messages=[], text="Hello, how can I help?")
    factory, calls = _foundry_agent_factory([chat_result])

    mock_foundry_module = MagicMock()
    mock_foundry_module.FoundryAgent = factory

    with patch.dict(sys.modules, {"agent_framework.foundry": mock_foundry_module}):
        result = await foundry_agent_utils._run_foundry_chat_with_routing(
            foundry_endpoint="https://foundry.test",
            chat_agent_name="chat-agent",
            product_agent_name="product-agent",
            policy_agent_name="policy-agent",
            question="hi",
            credential=AsyncMock(),
        )

    assert result == "Hello, how can I help?"
    assert calls == ["chat-agent"]
