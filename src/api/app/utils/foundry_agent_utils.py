"""
Foundry agent utilities — call the multi-agent pipeline for grounded enterprise answers.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def call_foundry_agent(
    question: str,
    foundry_endpoint: str,
    chat_agent_name: str,
    product_agent_name: str,
    policy_agent_name: str,
    azure_client_id: Optional[str] = None,
) -> str:
    """
    Call the Foundry multi-agent pipeline (chat → product/policy agents → Azure AI Search).
    Returns the grounded text response.
    """
    try:
        from agent_framework_azure_ai import AzureAIProjectAgentProvider
        from azure.ai.projects.aio import AIProjectClient

        try:
            from ..utils.azure_credential_utils import get_azure_credential_async
        except ImportError:
            from app.utils.azure_credential_utils import get_azure_credential_async

        if not foundry_endpoint:
            return "Foundry endpoint not configured."

        if not all([chat_agent_name, product_agent_name, policy_agent_name]):
            return "Foundry agents not fully configured."

        credential = await get_azure_credential_async(client_id=azure_client_id)

        async with (
            credential,
            AIProjectClient(endpoint=foundry_endpoint, credential=credential) as project_client,
            AzureAIProjectAgentProvider(
                project_client=project_client,
                credential=credential,
            ) as provider,
        ):
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

            if result and hasattr(result, "text"):
                return result.text
            elif result:
                return str(result)
            else:
                return "No response from the agent."

    except Exception:
        logger.exception("Foundry agent call failed.")
        return "Error getting answer from Foundry agent."
