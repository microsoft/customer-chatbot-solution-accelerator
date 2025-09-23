from typing import List, Tuple, Optional, Dict

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

from .config import settings
from .foundry_client import get_foundry_client
from .plugins.product_plugin import ProductPlugin
from .plugins.orders_plugin import OrdersPlugin
# Knowledge agent uses Azure Search configured in Foundry, so no ReferencePlugin here


# ---------- Foundry helpers ----------
async def _resolve_foundry_agent_definition(agent_id: Optional[str], name_fallback: Optional[str] = None):
    """
    Resolve an agent definition from Azure AI Foundry by id, with optional name fallback.
    """
    client = get_foundry_client()
    definition = None

    if agent_id:
        try:
            definition = await client.agents.get_agent(agent_id)
        except ResourceNotFoundError:
            if not name_fallback:
                raise

    if definition is None and name_fallback:
        async for a in client.agents.list_agents():
            if a.name == name_fallback:
                definition = a
                break
        if definition is None:
            available = []
            async for a in client.agents.list_agents():
                available.append(f"{a.name} ({a.id})")
            raise ResourceNotFoundError(
                f"Foundry agent not found. Tried id={agent_id!r} and name={name_fallback!r}. "
                f"Project has: {', '.join(available) or '(no agents)'}"
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
    """
    Generic builder for an AzureAIAgent backed by a Foundry agent.
    No instruction overrides here; the Foundry portal prompt is source of truth.
    """
    definition = await _resolve_foundry_agent_definition(agent_id, name_fallback)
    client = get_foundry_client()
    return AzureAIAgent(client=client, definition=definition, name=name, plugins=plugins or [])


# ---------- BUILD AGENTS (Foundry-only) ----------
async def get_agents() -> Tuple[List[Agent], OrchestrationHandoffs]:
    """
    Build Foundry-backed agents.
    Requires FOUNDRY_ORCHESTRATOR_AGENT_ID. Other agent IDs are optional.
    """
    # ORCHESTRATOR (required)
    orchestrator_agent_id = settings.foundry_orchestrator_agent_id # getattr(settings, "foundry_orchestrator_agent_id", "")
    if not orchestrator_agent_id:
        raise ValueError(
            "FOUNDRY_ORCHESTRATOR_AGENT_ID must be set when using Foundry-only agents."
        )
    orchestrator = await _build_foundry_agent(agent_id=orchestrator_agent_id, name="OrchestratorAgent")

    # PRODUCT (optional; attaches ProductPlugin)
    agents: Dict[str, Agent] = {"OrchestratorAgent": orchestrator}
    if getattr(settings, "foundry_product_agent_id", ""):
        product_lookup = await _build_foundry_agent(
            agent_id=settings.foundry_product_agent_id,
            name="ProductLookupAgent",
            plugins=[ProductPlugin()],
        )
        # product_lookup.description = "Finds products, prices, availability (uses ProductPlugin tools)."
        agents[product_lookup.name] = product_lookup

    # ORDER STATUS (optional; attaches OrdersPlugin)
    if getattr(settings, "foundry_order_agent_id", ""):
        order_status = await _build_foundry_agent(
            agent_id=settings.foundry_order_agent_id,
            name="OrderStatusAgent",
            plugins=[OrdersPlugin()],
        )
        # order_status.description = "Checks order status/history (uses OrdersPlugin tools)."
        agents[order_status.name] = order_status

    # KNOWLEDGE (optional; no plugins so Foundry’s Azure Search takes over)
    if getattr(settings, "foundry_knowledge_agent_id", ""):
        knowledge_agent = await _build_foundry_agent(
            agent_id=settings.foundry_knowledge_agent_id,
            name="KnowledgeAgent",
            plugins=None,
        )
        # knowledge_agent.description = "Answers policy/FAQ/knowledge-base questions (Foundry Search-backed)."
        agents[knowledge_agent.name] = knowledge_agent

    members = list(agents.values())

    # Handoffs: route from orchestrator → all other agents that exist
    targets = {a.name: label for a, label in []}
    targets = {}
    for name, agent in agents.items():
        if name == orchestrator.name:
            continue
        # Keep the labels short & clear
        if name == "ProductLookupAgent":
            targets[name] = "Product search / SKU / availability"
        elif name == "OrderStatusAgent":
            targets[name] = "Order status / history"
        elif name == "KnowledgeAgent":
            targets[name] = "Policies / FAQ / knowledge"
        else:
            targets[name] = name  # generic label

    handoffs = OrchestrationHandoffs()
    if targets:
        handoffs = handoffs.add_many(source_agent=orchestrator.name, target_agents=targets)
        # Return to orchestrator from each specialist
        for tgt in targets:
            handoffs = handoffs.add(source_agent=tgt, target_agent=orchestrator.name, description="Back to orchestrator")

    return members, handoffs


# ---------- Logging callback ----------
def agent_response_callback(message: ChatMessageContent) -> None:
    """Log model output and tool usage so you can verify plugins are invoked."""
    name = message.name or "Agent"
    txt = (message.content or "").strip()
    if txt:
        print(f"[{name}] {txt}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"  -> TOOL CALL: {item.name}({item.arguments})")
        if isinstance(item, FunctionResultContent):
            snippet = (str(item.result) or "")
            if len(snippet) > 400:
                snippet = snippet[:400] + "... [truncated]"
            print(f"  <- TOOL RESULT from {item.name}: {snippet}")


# ---------- Orchestrator ----------
class HandoffChatOrchestrator:
    """
    Builds only AzureAIAgent instances.
    """

    def __init__(self):
        self._runtime: InProcessRuntime | None = None
        self._assistant_messages: list[str] = []
        self._last_agent: str | None = None
        self.handoff_orchestration: HandoffOrchestration | None = None

    @classmethod
    async def create(cls) -> "HandoffChatOrchestrator":
        self = cls()
        members, handoffs = await get_agents()

        self._runtime = InProcessRuntime()
        self._runtime.start()

        def _capture(message: ChatMessageContent) -> None:
            agent_response_callback(message)
            if message.content and message.role == AuthorRole.ASSISTANT:
                self._assistant_messages.append(message.content)
                self._last_agent = message.name

        self.handoff_orchestration = HandoffOrchestration(
            members=members, handoffs=handoffs, agent_response_callback=_capture
        )
        return self

    async def respond(self, user_text: str) -> dict:
        assert self._runtime and self.handoff_orchestration

        self._assistant_messages = []

        # If previous turn came from a specialist, lightly hint follow-up routing
        if self._last_agent and self._last_agent != "OrchestratorAgent":
            user_text = f"[Follow-up for {self._last_agent}] {user_text}"

        result = await self.handoff_orchestration.invoke(task=user_text, runtime=self._runtime)
        value = await result.get()

        last_msg = (
            self._assistant_messages[-1]
            if self._assistant_messages
            else (value if isinstance(value, str) else "")
        )
        awaiting_user = bool(last_msg and last_msg.strip().endswith("?"))

        return {
            "messages": self._assistant_messages or ([last_msg] if last_msg else []),
            "awaiting_user": awaiting_user,
        }

    async def shutdown(self):
        if self._runtime:
            await self._runtime.stop_when_idle()