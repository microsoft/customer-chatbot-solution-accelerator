from __future__ import annotations
import os
import json
from typing import List, Dict, Any

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)
from semantic_kernel.agents import ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatHistory, AuthorRole
from semantic_kernel.contents import ChatMessageContent

from .plugins.product_plugin import ProductPlugin
from .plugins.reference_plugin import ReferencePlugin
from .plugins.orders_plugin import OrdersPlugin
from .config import settings

def build_kernel() -> Kernel:
    kernel = Kernel()

    # Prefer Azure OpenAI if configured; else OpenAI
    if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment:
        kernel.add_service(
            AzureChatCompletion(
                deployment_name=settings.azure_openai_deployment,
                endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
            )
        )
    elif settings.openai_api_key and settings.openai_model:
        kernel.add_service(OpenAIChatCompletion(model_id=settings.openai_model, api_key=settings.openai_api_key))
    else:
        raise RuntimeError("No LLM configured. Set Azure OpenAI or OpenAI environment variables.")

    # Register domain plugins
    kernel.add_plugin(ProductPlugin(), plugin_name="product")
    kernel.add_plugin(ReferencePlugin(), plugin_name="reference")
    kernel.add_plugin(OrdersPlugin(), plugin_name="orders")
    return kernel

def create_agents(kernel: Kernel):
    product_lookup = ChatCompletionAgent(
        name="product_lookup",
        kernel=kernel,
        instructions=(
            "You are a product expert. Use the ProductPlugin functions to answer.\n"
            "If the user provides a SKU, call product.get_by_sku. Otherwise, call product.search with their query.\n"
            "Always return helpful prose followed by a compact JSON code block of the items you used."
        ),
    )

    reference_doc = ChatCompletionAgent(
        name="reference-doc",
        kernel=kernel,
        instructions=(
            "You answer policy and reference questions using ReferencePlugin.\n"
            "Call reference.lookup with the user's question, then summarize clearly."
        ),
    )

    customer_orders = ChatCompletionAgent(
        name="customer_orders",
        kernel=kernel,
        instructions=(
            "You help customers with orders.\n"
            "If they give an order id, call orders.get_order. If they identify a customerId, call orders.list_orders.\n"
            "Do not fabricate order details. If none found, say so and provide next steps."
        ),
    )

    router = ChatCompletionAgent(
        name="router",
        kernel=kernel,
        instructions=(
            "You are a routing assistant. For EVERY user message, pick EXACTLY ONE of these and hand off by name:\n"
            "- product_lookup: products, SKUs, availability, price\n"
            "- reference_doc: policies, returns, shipping, FAQs\n"
            "- customer_orders: order status, order history, tracking\n"
            "NEVER ask questions yourself. If unclear, choose the most likely target and hand off immediately."
            # "You are a routing assistant. Decide which specialist should handle the user's message and hand off.\n"
            # "If the message is about products, SKUs, availability, or price: hand off to product_lookup.\n"
            # "If the message is about policies, returns, shipping, or FAQs: hand off to reference_doc.\n"
            # "If the message is about a customer's orders or order status: hand off to customer_orders.\n"
            # "If unclear, ask a brief clarifying question, then hand off."
        ),
    )

    return router, product_lookup, reference_doc, customer_orders

# def create_handoff_orchestration(kernel: Kernel) -> HandoffOrchestration:
#     router, product_lookup, reference_doc, customer_orders = create_agents(kernel)

#     # Declare allowed handoffs
#     handoffs = OrchestrationHandoffs()
#     handoffs.add("router", "product_lookup")
#     handoffs.add("router", "reference_doc")
#     handoffs.add("router", "customer_orders")

#     runtime = InProcessRuntime()
#     orchestration = HandoffOrchestration(
#         agents=[router, product_lookup, reference_doc, customer_orders],
#         handoffs=handoffs,
#         runtime=runtime,
#     )
#     return orchestration

def create_handoff_orchestration(kernel: Kernel) -> tuple[HandoffOrchestration, InProcessRuntime]:
    router, product_lookup, reference_doc, customer_orders = create_agents(kernel)

    # Hand-off rules by agent *names*
    handoffs = (
        OrchestrationHandoffs()
        .add(source_agent=router.name, target_agent=product_lookup.name)
        .add(source_agent=router.name, target_agent=reference_doc.name)
        .add(source_agent=router.name, target_agent=customer_orders.name)
    )

    print("Agents loaded:", [a.name for a in [router, product_lookup, reference_doc, customer_orders]])

    # Optional: capture agent messages
    def agent_response_callback(msg: ChatMessageContent) -> None:
        # you could log/collect msg here
        print(f"[{msg.role}] {msg.content}")
        print(msg.model_dump_json())
        return

    orchestration = HandoffOrchestration(
        members=[router, product_lookup, reference_doc, customer_orders],
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        # human_response_function=...  # only needed if you want interactive prompts
    )

    runtime = InProcessRuntime()
    runtime.start()
    return orchestration, runtime


# Fallback classifier if HandoffOrchestration not available
async def classify_intent(kernel: Kernel, user_text: str) -> str:
    system = (
        "You are an intent classifier for an e-commerce assistant. Output only one word: "
        "product, reference, or orders.\n"
        "product: product search, SKU, availability, price\n"
        "reference: returns, shipping, policy, warranty, FAQ\n"
        "orders: order status, past purchases, order id, tracking\n"
    )
    history = ChatHistory()
    history.add_system_message(system)
    history.add_user_message(user_text)

    service = kernel.get_service(type=AzureChatCompletion) or kernel.get_service(type=OpenAIChatCompletion)
    result = await service.complete_chat_async(history)
    label = result.content.strip().lower()
    return label if label in {"product", "reference", "orders"} else "product"

async def run_simple_router(kernel: Kernel, user_text: str) -> str:
    intent = await classify_intent(kernel, user_text)
    if intent == "product":
        items = kernel.plugins["product"].search(user_text)
        return f"Product results: {items}"
    if intent == "reference":
        hits = kernel.plugins["reference"].lookup(user_text)
        return f"Reference info: {hits}"
    if intent == "orders":
        return json.dumps({"message": "Please provide your order id or customerId to look up orders."})
    return "I'm not sure yet—are you asking about products, policies, or an order?"

class Orchestrator:
    def __init__(self) -> None:
        self.kernel = build_kernel()
        self.use_simple = os.getenv("USE_SIMPLE_ROUTER", "false").lower() == "true"
        self._orchestration = None
        self._runtime = None
        if not self.use_simple:
            self._orchestration, self._runtime = create_handoff_orchestration(self.kernel)

    async def respond(self, user_text: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        if self.use_simple:
            text = await run_simple_router(self.kernel, user_text)
            return {"text": text}

        # New invoke pattern
        result = await self._orchestration.invoke(task=user_text, runtime=self._runtime)
        value = await result.get()
        return {"text": value if isinstance(value, str) else str(value)}
