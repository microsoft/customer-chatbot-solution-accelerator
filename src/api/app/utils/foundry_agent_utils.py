"""
Foundry agent utilities — call the multi-agent pipeline for grounded enterprise answers.
"""
import json
import logging
import re
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Sub-agent tools baked into the chat agent definition.
_SUBAGENT_TOOL_NAMES = {"product_agent", "policy_agent"}

# Azure AI Search citation annotations, e.g. "【4:0†source】".
_CITATION_RE = re.compile(r"\u3010[^\u3011]*?\u2020[^\u3011]*?\u3011")


def _strip_citations(text: str) -> str:
    """Remove Azure AI Search citation markers and tidy leftover spacing."""
    if not text:
        return text
    cleaned = _CITATION_RE.sub("", text)
    cleaned = re.sub(r"[ \t]+([.,;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def _get_agent_provider_class():
    """Resolve provider class across Agent Framework package transitions."""
    try:
        from agent_framework.azure import AzureAIProjectAgentProvider

        return AzureAIProjectAgentProvider
    except ImportError:
        return None


def _result_text(result: Any) -> str:
    """Extract plain text from an Agent Framework run result."""
    if result is None:
        return ""
    text = getattr(result, "text", None)
    if not text:
        text = str(result)
    return _strip_citations(text)


def _extract_subagent_call(result: Any) -> Optional[Tuple[str, str]]:
    """Return (sub_agent_tool_name, task) if the chat agent emitted a sub-agent call, else None."""
    messages = getattr(result, "messages", None) or []
    for message in messages:
        for content in getattr(message, "contents", None) or []:
            if getattr(content, "type", None) != "function_call":
                continue
            name = getattr(content, "name", None)
            if name not in _SUBAGENT_TOOL_NAMES:
                continue
            task = ""
            raw_args = getattr(content, "arguments", None)
            if raw_args:
                try:
                    parsed = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    if isinstance(parsed, dict):
                        task = parsed.get("task") or parsed.get("query") or ""
                except (ValueError, TypeError):
                    task = ""
            return name, task
    return None


async def _run_foundry_chat_with_routing(
    foundry_endpoint: str,
    chat_agent_name: str,
    product_agent_name: str,
    policy_agent_name: str,
    question: str,
    credential: Any,
) -> str:
    """Run the chat agent, then execute the grounded sub-agent it routes to (if any)."""
    from agent_framework.foundry import FoundryAgent

    tool_to_agent_name = {
        "product_agent": product_agent_name,
        "policy_agent": policy_agent_name,
    }

    async with FoundryAgent(
        project_endpoint=foundry_endpoint,
        agent_name=chat_agent_name,
        credential=credential,
    ) as chat_agent:
        result = await chat_agent.run(question)

    call = _extract_subagent_call(result)
    if call is None:
        return _result_text(result)

    tool_name, task = call
    target_agent_name = tool_to_agent_name.get(tool_name)
    if not target_agent_name:
        return _result_text(result)

    async with FoundryAgent(
        project_endpoint=foundry_endpoint,
        agent_name=target_agent_name,
        credential=credential,
    ) as sub_agent:
        sub_result = await sub_agent.run(task or question)

    return _result_text(sub_result)


async def call_foundry_agent(
    question: str,
    foundry_endpoint: str,
    chat_agent_name: str,
    product_agent_name: str,
    policy_agent_name: str,
    azure_client_id: Optional[str] = None,
) -> str:
    """
    Call the Foundry agent pipeline for grounded enterprise answers.

    When AzureAIProjectAgentProvider is available, uses the full multi-agent pipeline
    (chat → product/policy agents → Azure AI Search). Otherwise, falls back to a single
    FoundryAgent call using only the chat agent (without product/policy sub-agents).

    Returns the grounded text response.
    """
    try:
        from azure.ai.projects.aio import AIProjectClient

        try:
            from ..utils.azure_credential_utils import get_azure_credential_async
        except ImportError:
            from app.utils.azure_credential_utils import get_azure_credential_async

        if not foundry_endpoint:
            return "Foundry endpoint not configured."

        agent_provider_class = _get_agent_provider_class()

        required_agents = [(chat_agent_name, "foundry_chat_agent")]
        if agent_provider_class is not None:
            required_agents.extend(
                [
                    (product_agent_name, "foundry_product_agent"),
                    (policy_agent_name, "foundry_policy_agent"),
                ]
            )

        if not all(agent_name for agent_name, _ in required_agents):
            return "Foundry agents not fully configured."

        credential = await get_azure_credential_async(client_id=azure_client_id)

        async with (
            credential,
            AIProjectClient(endpoint=foundry_endpoint, credential=credential) as project_client,
        ):
            if agent_provider_class is not None:
                async with agent_provider_class(
                    project_client=project_client,
                    credential=credential,
                ) as provider:
                    product_agent = await provider.get_agent(name=product_agent_name)
                    policy_agent = await provider.get_agent(name=policy_agent_name)

                    retrieved_agent = await provider.get_agent(
                        name=chat_agent_name,
                        tools=[
                            product_agent.as_tool(name="product_agent"),
                            policy_agent.as_tool(name="policy_agent"),
                        ],
                    )

                    result = await retrieved_agent.run(question)
            else:
                grounded_text = await _run_foundry_chat_with_routing(
                    foundry_endpoint=foundry_endpoint,
                    chat_agent_name=chat_agent_name,
                    product_agent_name=product_agent_name,
                    policy_agent_name=policy_agent_name,
                    question=question,
                    credential=credential,
                )
                return grounded_text or "No response from the agent."

            if result and hasattr(result, "text"):
                return result.text
            elif result:
                return str(result)
            else:
                return "No response from the agent."

    except Exception:
        logger.exception("Foundry agent call failed.")
        return "Error getting answer from Foundry agent."
