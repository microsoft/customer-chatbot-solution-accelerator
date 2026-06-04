"""
Foundry agent utilities — call the multi-agent pipeline for grounded enterprise answers.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _get_agent_provider_class():
    """Resolve provider class across Agent Framework package transitions."""
    try:
        from agent_framework.azure import AzureAIProjectAgentProvider

        return AzureAIProjectAgentProvider
    except ImportError:
        return None


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
                from agent_framework.foundry import FoundryAgent

                async with FoundryAgent(
                    project_endpoint=foundry_endpoint,
                    agent_name=chat_agent_name,
                    credential=credential,
                ) as chat_agent:
                    result = await chat_agent.run(question)

            if result and hasattr(result, "text"):
                return result.text
            elif result:
                return str(result)
            else:
                return "No response from the agent."

    except Exception:
        logger.exception("Foundry agent call failed.")
        return "Error getting answer from Foundry agent."
