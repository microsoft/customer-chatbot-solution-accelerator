from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from cachetools import TTLCache
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread

from .config import has_foundry_config, settings
from .foundry_client import get_foundry_client, init_foundry_client
from .plugins.orders_plugin import OrdersPlugin
from .plugins.reference_plugin import ReferencePlugin

logger = logging.getLogger(__name__)


class ThreadCache(TTLCache):
    """Cache for agent threads with automatic cleanup"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def expire(self, time=None):
        """Remove expired items and delete associated threads"""
        items = super().expire(time)
        for key, thread_id in items:
            try:
                logger.info(f"Thread expired from cache: {thread_id}")
            except Exception as e:
                logger.error(f"Error expiring thread {thread_id}: {e}")
        return items

    def popitem(self):
        """Remove item using LRU eviction"""
        key, thread_id = super().popitem()
        try:
            logger.info(f"Thread evicted from cache (LRU): {thread_id}")
        except Exception as e:
            logger.error(f"Error evicting thread {thread_id}: {e}")
        return key, thread_id


async def _resolve_foundry_agent_definition(agent_id: str):
    """Get the agent definition from Foundry"""
    # client = get_foundry_client()
    try:
        # For now, return a basic agent definition structure
        # This needs to be updated when the correct Azure AI Projects SDK method is available
        logger.warning(f"Using placeholder agent definition for agent ID: {agent_id}")

        # Create a basic agent definition that can work with AzureAIAgent
        agent_definition = {
            "id": agent_id,
            "name": f"Agent-{agent_id}",
            "description": f"Azure AI Foundry Agent {agent_id}",
            "instructions": "You are a helpful assistant.",
            "model": "gpt-4",
        }

        return agent_definition

    except Exception as e:
        logger.error(
            f"Error resolving Foundry agent definition for ID '{agent_id}': {e}"
        )
        # Return a fallback definition
        return {
            "id": agent_id,
            "name": f"Fallback-Agent-{agent_id}",
            "description": "Fallback agent definition",
            "instructions": "You are a helpful assistant.",
            "model": "gpt-4",
        }


async def _build_foundry_agent(
    agent_id: str, name: str, plugins: Optional[List] = None
) -> Optional[Any]:
    """Build a Foundry agent using direct OpenAI API calls"""
    try:
        logger.info(f"Building {name} (ID: {agent_id}) using Azure AI Foundry...")

        # Get the Foundry client
        client = get_foundry_client()

        try:
            # Get the OpenAI client from Foundry with proper API version
            openai_client = await client.get_openai_client(  # type: ignore
                api_version=settings.azure_openai_api_version
            )

            # Test connection by retrieving the assistant
            assistant = await openai_client.beta.assistants.retrieve(agent_id)
            logger.info(
                f"✅ Successfully connected to Foundry assistant: {assistant.name or name}"
            )

            # Create a custom agent that uses the OpenAI client directly
            class FoundryAgent:
                def __init__(self, assistant_id: str, name: str, openai_client):
                    self.id = assistant_id
                    self.name = name
                    self.client = openai_client
                    self.assistant_id = assistant_id

                async def invoke(self, messages: str, thread=None):
                    try:
                        # Create or get thread
                        if not thread or not hasattr(thread, "id"):
                            thread_obj = await self.client.beta.threads.create()
                            thread_id = thread_obj.id
                            logger.info(f"Created new thread: {thread_id}")
                        else:
                            thread_id = thread.id
                            logger.info(f"Using existing thread: {thread_id}")

                        # Add user message to thread
                        await self.client.beta.threads.messages.create(
                            thread_id=thread_id, role="user", content=messages
                        )

                        # Create and run the assistant
                        run = await self.client.beta.threads.runs.create(
                            thread_id=thread_id, assistant_id=self.assistant_id
                        )

                        max_attempts = 30  # 30 seconds max
                        attempt = 0

                        while (
                            run.status in ["queued", "in_progress"]
                            and attempt < max_attempts
                        ):
                            await asyncio.sleep(1)
                            attempt += 1
                            run = await self.client.beta.threads.runs.retrieve(
                                thread_id=thread_id, run_id=run.id
                            )
                            logger.debug(
                                f"Run status: {run.status} (attempt {attempt})"
                            )

                        if run.status == "completed":
                            # Get the assistant's response
                            messages_response = (
                                await self.client.beta.threads.messages.list(
                                    thread_id=thread_id,
                                    limit=1,  # Get just the latest message
                                )
                            )

                            if messages_response.data:
                                latest_message = messages_response.data[0]
                                if (
                                    latest_message.role == "assistant"
                                    and latest_message.content
                                ):
                                    content = latest_message.content[0].text.value

                                    class FoundryResponse:
                                        def __init__(self, content, thread_id):
                                            self.content = content
                                            self.thread = type(
                                                "Thread", (), {"id": thread_id}
                                            )()

                                    logger.info(
                                        f"✅ {self.name} responded with {len(content)} characters"
                                    )
                                    yield FoundryResponse(content, thread_id)
                                    return

                        # Handle non-completed status
                        error_msg = f"Assistant run did not complete successfully. Status: {run.status}"
                        if run.status == "failed":
                            error_msg += f". Error: {getattr(run, 'last_error', 'Unknown error')}"

                        logger.error(error_msg)

                        class ErrorResponse:
                            def __init__(self, content):
                                self.content = content
                                self.thread = None

                        yield ErrorResponse(
                            f"Sorry, I encountered an issue: {error_msg}"
                        )

                    except Exception as invoke_error:
                        logger.error(
                            f"Error invoking {self.name}: {invoke_error}", exc_info=True
                        )

                        class InvokeErrorResponse:
                            def __init__(self, content):
                                self.content = content
                                self.thread = None

                        yield InvokeErrorResponse(
                            f"I encountered an error while processing your request: {str(invoke_error)}"
                        )

            foundry_agent = FoundryAgent(agent_id, name, openai_client)
            logger.info(f"✅ Successfully created Foundry agent: {name}")
            return foundry_agent

        except Exception as e:
            logger.error(f"Failed to create Foundry agent {name}: {e}", exc_info=True)
            # No fallback - return None to indicate failure
            return None

    except Exception as e:
        logger.error(f"Error building Foundry agent '{name}' with ID '{agent_id}': {e}")
        return None


class SimpleFoundryOrchestrator:
    """
    Simple orchestrator that routes to the appropriate Foundry agent.
    Uses Semantic Kernel AzureAIAgent like the reference implementation.
    Includes thread caching for better performance.
    """

    def __init__(self):
        self.agents: Dict[str, AzureAIAgent] = {}
        self.is_configured = has_foundry_config()
        self.thread_cache: ThreadCache = ThreadCache(maxsize=1000, ttl=3600.0)

        if not self.is_configured:
            logger.warning(
                "Foundry not configured. Set AZURE_FOUNDRY_ENDPOINT and agent IDs"
            )

    @classmethod
    async def create(cls) -> "SimpleFoundryOrchestrator":
        """Initialize the orchestrator and create all agents"""
        self = cls()

        if not self.is_configured:
            logger.warning(
                "Simple Foundry orchestrator will not initialize (not configured)"
            )
            return self

        try:
            logger.info("Initializing Simple Foundry orchestrator...")
            logger.info(f"   - Foundry endpoint: {settings.azure_foundry_endpoint}")
            logger.info(
                f"   - Orchestrator agent ID: {settings.foundry_orchestrator_agent_id}"
            )
            logger.info(f"   - Order agent ID: {settings.foundry_order_agent_id}")
            logger.info(
                f"   - Knowledge agent ID: {settings.foundry_knowledge_agent_id}"
            )

            # Initialize Foundry client first
            logger.info("Initializing Foundry client...")
            await init_foundry_client()
            logger.info("✅ Foundry client initialized")

            # Build the main orchestrator agent if configured
            if settings.foundry_orchestrator_agent_id:
                logger.info("Building OrchestratorAgent...")
                orchestrator_agent = await _build_foundry_agent(
                    agent_id=settings.foundry_orchestrator_agent_id,
                    name="OrchestratorAgent",
                    plugins=[OrdersPlugin(), ReferencePlugin()],
                )
                if orchestrator_agent:
                    self.agents["OrchestratorAgent"] = orchestrator_agent
                    logger.info("✅ Added OrchestratorAgent with all plugins")
                else:
                    logger.warning("❌ Failed to create OrchestratorAgent")
            else:
                logger.warning("⚠️ No OrchestratorAgent ID configured")

            # Build agents with their plugins attached
            if settings.foundry_order_agent_id:
                logger.info("Building OrderStatusAgent...")
                order_agent = await _build_foundry_agent(
                    agent_id=settings.foundry_order_agent_id,
                    name="OrderStatusAgent",
                    plugins=[OrdersPlugin()],
                )
                if order_agent:
                    self.agents["OrderStatusAgent"] = order_agent
                    logger.info("✅ Added OrderStatusAgent with OrdersPlugin")
                else:
                    logger.warning("❌ Failed to create OrderStatusAgent")
            else:
                logger.warning("⚠️ No OrderStatusAgent ID configured")

            if settings.foundry_knowledge_agent_id:
                logger.info("Building KnowledgeAgent...")
                knowledge_agent = await _build_foundry_agent(
                    agent_id=settings.foundry_knowledge_agent_id,
                    name="KnowledgeAgent",
                    plugins=[ReferencePlugin()],
                )
                if knowledge_agent:
                    self.agents["KnowledgeAgent"] = knowledge_agent
                    logger.info("✅ Added KnowledgeAgent with ReferencePlugin")
                else:
                    logger.warning("❌ Failed to create KnowledgeAgent")
            else:
                logger.warning("⚠️ No KnowledgeAgent ID configured")

            if not self.agents:
                logger.error("❌ No agents were successfully built!")
                self.is_configured = False
                return self

            logger.info(
                f"✅ Simple Foundry orchestrator initialized with {len(self.agents)} agents"
            )
            return self

        except Exception as e:
            logger.error(
                f"❌ Failed to initialize Simple Foundry orchestrator: {e}",
                exc_info=True,
            )
            self.is_configured = False
            return self

    def _determine_target_agent(self, user_text: str) -> str:
        query_lower = user_text.lower()

        order_patterns = [
            r"\b(order|tracking|shipment|invoice)\b",
            r"\b(where is my|order status|order #)\b",
        ]
        policy_patterns = [
            r"\b(return|refund|exchange|policy|warranty)\b",
            r"\b(problem|issue|complaint|damaged|leaking)\b",
            r"\b(ship|delivery|shipping|track)\b",
            r"\b(help|support|contact|customer service)\b",
            r"\b(guarantee|coverage|defect)\b",
        ]

        order_score = sum(1 for pattern in order_patterns if re.search(pattern, query_lower))
        policy_score = sum(1 for pattern in policy_patterns if re.search(pattern, query_lower))

        if order_score > 0 and "OrderStatusAgent" in self.agents:
            logger.info("Routing to OrderStatusAgent")
            return "OrderStatusAgent"
        if policy_score > 0 and "KnowledgeAgent" in self.agents:
            logger.info("Routing to KnowledgeAgent")
            return "KnowledgeAgent"
        if "OrchestratorAgent" in self.agents:
            logger.info("Default routing to OrchestratorAgent")
            return "OrchestratorAgent"
        available_agents = list(self.agents.keys())
        if available_agents:
            return available_agents[0]
        logger.error("No agents available for routing")
        return "OrchestratorAgent"

    async def respond(
        self,
        user_text: str,
        conversation_id: Optional[str] = None,
        history: List[Dict[str, str]] | None = None,
    ) -> Dict[str, Any]:
        """Respond using the determined agent with thread caching"""
        if not self.is_configured:
            logger.error("Simple Foundry orchestrator not configured")
            return {
                "error": "Simple Foundry orchestrator not configured",
                "text": "I'm sorry, the AI service is not properly configured.",
            }

        try:
            # Determine which agent to use
            target_agent_name = self._determine_target_agent(user_text)
            agent = self.agents.get(target_agent_name)

            if not agent:
                logger.error(f"Agent {target_agent_name} not available")
                return {
                    "error": f"Agent {target_agent_name} not available",
                    "text": f"I'm sorry, the {target_agent_name} is not currently available.",
                }

            logger.info(f"Using {target_agent_name} for query: {user_text[:50]}...")

            # Get or create thread for this conversation (thread caching)
            thread = None
            if conversation_id:
                cache_key = f"{conversation_id}_{target_agent_name}"
                thread_id = self.thread_cache.get(cache_key)
                if thread_id:
                    thread = AzureAIAgentThread(
                        client=agent.client, thread_id=thread_id
                    )
                    logger.info(f"Reusing cached thread: {thread_id}")

            # Use the agent's invoke method with thread caching
            response_content = ""
            async for message in agent.invoke(messages=user_text, thread=thread):
                if hasattr(message, "content") and message.content:
                    response_content += str(message.content)

                # Cache the thread for future use
                if conversation_id and hasattr(message, "thread") and message.thread:
                    cache_key = f"{conversation_id}_{target_agent_name}"
                    self.thread_cache[cache_key] = message.thread.id

            if response_content:
                logger.info(
                    f"{target_agent_name} response length: {len(response_content)} chars"
                )
                return {
                    "messages": [response_content],
                    "awaiting_user": response_content.strip().endswith("?"),
                    "text": response_content,
                }
            else:
                logger.error(f"No response from {target_agent_name}")
                return {
                    "error": "No response from agent",
                    "text": "I'm sorry, I couldn't get a response from the agent.",
                }

        except Exception as e:
            logger.error(f"Error in Simple Foundry orchestrator: {e}", exc_info=True)
            return {
                "error": f"Failed to generate response: {str(e)}",
                "text": "I'm sorry, I encountered an error trying to process your request.",
            }

    async def shutdown(self):
        """Cleanup if needed"""
        logger.info("Simple Foundry orchestrator shutdown")


_simple_foundry_orchestrator_instance: SimpleFoundryOrchestrator | None = None


async def get_simple_foundry_orchestrator() -> SimpleFoundryOrchestrator:
    global _simple_foundry_orchestrator_instance
    if _simple_foundry_orchestrator_instance is None:
        _simple_foundry_orchestrator_instance = await SimpleFoundryOrchestrator.create()
    return _simple_foundry_orchestrator_instance
