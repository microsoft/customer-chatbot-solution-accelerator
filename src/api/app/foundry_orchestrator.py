from __future__ import annotations
import logging
from typing import List, Dict, Any, Optional, Tuple
from azure.core.exceptions import ResourceNotFoundError
from semantic_kernel.agents import (
    Agent,
    HandoffOrchestration,
    OrchestrationHandoffs,
    AzureAIAgent,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import (
    AuthorRole,
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
)
from .config import settings, has_foundry_config
from .foundry_client import get_foundry_client
from .plugins.product_plugin import ProductPlugin
from .plugins.orders_plugin import OrdersPlugin
from .plugins.reference_plugin import ReferencePlugin

logger = logging.getLogger(__name__)

async def _resolve_foundry_agent_definition(agent_id: Optional[str], name_fallback: Optional[str] = None):
    client = get_foundry_client()
    definition = None
    
    if agent_id:
        try:
            definition = await client.agents.get_agent(agent_id)
            logger.info(f"Found agent by ID: {agent_id}")
        except ResourceNotFoundError:
            if not name_fallback:
                raise
            logger.warning(f"Agent ID {agent_id} not found, trying fallback name: {name_fallback}")
    
    if definition is None and name_fallback:
        async for a in client.agents.list_agents():
            if a.name == name_fallback:
                definition = a
                logger.info(f"Found agent by name: {name_fallback} (ID: {a.id})")
                break
        
        if definition is None:
            available = []
            async for a in client.agents.list_agents():
                available.append(f"{a.name} ({a.id})")
            raise ResourceNotFoundError(
                f"Foundry agent not found. Tried id={agent_id!r} and name={name_fallback!r}. "
                f"Available agents: {', '.join(available) or '(none)'}"
            )
    
    if definition is None:
        raise ValueError("No Foundry agent id provided and no name fallback set.")
    
    return definition

async def _build_foundry_agent(
    *,
    agent_id: str,
    name: str,
    plugins: Optional[List[object]] = None,
    name_fallback: Optional[str] = None,
) -> AzureAIAgent:
    definition = await _resolve_foundry_agent_definition(agent_id, name_fallback)
    client = get_foundry_client()
    
    agent = AzureAIAgent(
        client=client,
        definition=definition,
        name=name,
        plugins=plugins or []
    )
    
    logger.info(f"Built Foundry agent: {name} with {len(plugins or [])} plugins")
    return agent

async def get_foundry_agents() -> Tuple[List[Agent], OrchestrationHandoffs]:
    logger.info("Building Foundry agents...")
    
    orchestrator_id = settings.foundry_orchestrator_agent_id
    if not orchestrator_id:
        raise ValueError(
            "FOUNDRY_ORCHESTRATOR_AGENT_ID must be set. "
            "Run setup_foundry_agents.py to create agents."
        )
    
    orchestrator = await _build_foundry_agent(
        agent_id=orchestrator_id,
        name="OrchestratorAgent"
    )
    
    agents: Dict[str, Agent] = {"OrchestratorAgent": orchestrator}
    
    if settings.foundry_product_agent_id:
        product_agent = await _build_foundry_agent(
            agent_id=settings.foundry_product_agent_id,
            name="ProductLookupAgent",
            plugins=[ProductPlugin()],
        )
        agents[product_agent.name] = product_agent
        logger.info("Added ProductLookupAgent with ProductPlugin")
    
    if settings.foundry_order_agent_id:
        order_agent = await _build_foundry_agent(
            agent_id=settings.foundry_order_agent_id,
            name="OrderStatusAgent",
            plugins=[OrdersPlugin()],
        )
        agents[order_agent.name] = order_agent
        logger.info("Added OrderStatusAgent with OrdersPlugin")
    
    if settings.foundry_knowledge_agent_id:
        knowledge_agent = await _build_foundry_agent(
            agent_id=settings.foundry_knowledge_agent_id,
            name="KnowledgeAgent",
            plugins=[ReferencePlugin()],
        )
        agents[knowledge_agent.name] = knowledge_agent
        logger.info("Added KnowledgeAgent with ReferencePlugin")
    
    members = list(agents.values())
    logger.info(f"Total agents: {len(members)}")
    
    targets = {}
    for name, agent in agents.items():
        if name == orchestrator.name:
            continue
        if name == "ProductLookupAgent":
            targets[name] = "Product search, SKU lookup, availability, pricing"
        elif name == "OrderStatusAgent":
            targets[name] = "Order status, order history, tracking"
        elif name == "KnowledgeAgent":
            targets[name] = "Policies, returns, shipping, FAQs, warranties"
        else:
            targets[name] = name
    
    handoffs = OrchestrationHandoffs()
    if targets:
        # Use add_many but with explicit routing instructions
        handoffs = handoffs.add_many(
            source_agent=orchestrator.name,
            target_agents=targets
        )
        logger.info(f"Added handoffs from orchestrator to {len(targets)} specialists")
        
        # Add return handoffs
        for tgt in targets:
            handoffs = handoffs.add(
                source_agent=tgt,
                target_agent=orchestrator.name,
                description="Return to orchestrator"
            )
        logger.info(f"Added return handoffs from specialists to orchestrator")
    
    return members, handoffs

def agent_response_callback(message: ChatMessageContent) -> None:
    name = message.name or "Agent"
    txt = (message.content or "").strip()
    
    if txt:
        logger.info(f"[{name}] {txt[:200]}{'...' if len(txt) > 200 else ''}")
    
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            logger.info(f"  🔧 Tool Call: {item.name}({item.arguments})")
        if isinstance(item, FunctionResultContent):
            result_str = str(item.result) or ""
            if len(result_str) > 400:
                result_str = result_str[:400] + "... [truncated]"
            logger.info(f"  📦 Tool Result from {item.name}: {result_str}")

class FoundryOrchestrator:
    def __init__(self):
        self._runtime: InProcessRuntime | None = None
        self._assistant_messages: list[str] = []
        self._last_agent: str | None = None
        self.handoff_orchestration: HandoffOrchestration | None = None
        self.is_configured = has_foundry_config()
        
        if not self.is_configured:
            logger.warning("Foundry not configured. Set AZURE_FOUNDRY_ENDPOINT and FOUNDRY_ORCHESTRATOR_AGENT_ID")
    
    @classmethod
    async def create(cls) -> "FoundryOrchestrator":
        self = cls()
        
        if not self.is_configured:
            logger.warning("Foundry orchestrator will not initialize (not configured)")
            return self
        
        try:
            logger.info("Initializing Foundry orchestrator...")
            members, handoffs = await get_foundry_agents()
            
            self._runtime = InProcessRuntime()
            self._runtime.start()
            logger.info("Runtime started")
            
            def _capture(message: ChatMessageContent) -> None:
                agent_response_callback(message)
                if message.content and message.role == AuthorRole.ASSISTANT:
                    self._assistant_messages.append(message.content)
                    self._last_agent = message.name
            
            self.handoff_orchestration = HandoffOrchestration(
                members=members,
                handoffs=handoffs,
                agent_response_callback=_capture
            )
            
            logger.info("✅ Foundry orchestrator initialized successfully")
            return self
            
        except Exception as e:
            logger.error(f"Failed to initialize Foundry orchestrator: {e}", exc_info=True)
            self.is_configured = False
            return self
    
    async def respond(self, user_text: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        if not self.is_configured or not self._runtime or not self.handoff_orchestration:
            return {
                "error": "Foundry orchestrator not configured",
                "text": "I'm sorry, the AI service is not properly configured."
            }
        
        try:
            self._assistant_messages = []
            
            if self._last_agent and self._last_agent != "OrchestratorAgent":
                user_text = f"[Follow-up for {self._last_agent}] {user_text}"
                logger.debug(f"Added follow-up context for {self._last_agent}")
            
            logger.info(f"Processing request: {user_text[:100]}...")
            
            result = await self.handoff_orchestration.invoke(
                task=user_text,
                runtime=self._runtime
            )
            value = await result.get()
            
            last_msg = (
                self._assistant_messages[-1]
                if self._assistant_messages
                else (value if isinstance(value, str) else str(value))
            )
            
            awaiting_user = bool(last_msg and last_msg.strip().endswith("?"))
            
            logger.info(f"Response generated: {len(last_msg)} chars, awaiting_user={awaiting_user}")
            
            return {
                "text": last_msg,
                "messages": self._assistant_messages or ([last_msg] if last_msg else []),
                "awaiting_user": awaiting_user,
            }
            
        except Exception as e:
            logger.error(f"Error in Foundry orchestrator respond: {e}", exc_info=True)
            return {
                "error": str(e),
                "text": "I'm sorry, I encountered an error processing your request."
            }
    
    async def shutdown(self):
        if self._runtime:
            logger.info("Shutting down Foundry orchestrator runtime...")
            await self._runtime.stop_when_idle()
            logger.info("Runtime stopped")

_foundry_orchestrator_instance: FoundryOrchestrator | None = None

async def get_foundry_orchestrator() -> FoundryOrchestrator:
    global _foundry_orchestrator_instance
    if _foundry_orchestrator_instance is None:
        _foundry_orchestrator_instance = await FoundryOrchestrator.create()
    return _foundry_orchestrator_instance

