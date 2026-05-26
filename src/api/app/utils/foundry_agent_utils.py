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
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    model_deployment_name: Optional[str] = None,
) -> str:
    """
    Call the Foundry multi-agent pipeline (chat → product/policy agents → Azure AI Search).
    Returns the grounded text response.

    When the underlying SDK reports token usage, emits LLM_Token_Usage_Summary,
    LLM_Agent_Token_Usage and LLM_Model_Token_Usage events to Application
    Insights for dashboarding (see infra/dashboards/token-usage-queries.kql).
    """
    try:
        from agent_framework_azure_ai import AzureAIProjectAgentProvider
        from azure.ai.projects.aio import AIProjectClient

        try:
            from ..config import settings as _settings
            from ..telemetry import token_emitter
            from ..utils.azure_credential_utils import get_azure_credential_async
            from ..utils.llm_token_telemetry import TokenUsageScope, detect_invoked_tools
        except ImportError:
            from app.config import settings as _settings
            from app.telemetry import token_emitter
            from app.utils.azure_credential_utils import get_azure_credential_async
            from app.utils.llm_token_telemetry import TokenUsageScope, detect_invoked_tools

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

            model_name = model_deployment_name or getattr(
                _settings, "azure_openai_deployment_name", ""
            )

            # Run the agent inside a TokenUsageScope so usage is extracted and
            # emitted on scope exit (best-effort; never breaks the response).
            with TokenUsageScope(
                token_emitter,
                agent_name=chat_agent_name,
                model_deployment_name=model_name,
                user_id=user_id,
                session_id=session_id,
            ) as scope:
                result = await retrieved_agent.run(question)
                scope.add(result)

                # Attribute usage to sub-agents that were actually invoked by
                # inspecting function_call items in the result messages.
                invoked = detect_invoked_tools(result)
                if "product_agent" in invoked:
                    scope.additional_agents[product_agent_name] = model_name
                if "policy_agent" in invoked:
                    scope.additional_agents[policy_agent_name] = model_name

            if result and hasattr(result, "text"):
                return result.text
            elif result:
                return str(result)
            else:
                return "No response from the agent."

    except Exception:
        logger.exception("Foundry agent call failed.")
        return "Error getting answer from Foundry agent."
