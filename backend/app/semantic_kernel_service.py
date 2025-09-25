from __future__ import annotations
import os
import json
import logging
from typing import List, Dict, Any, Optional

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import (
    AzureChatCompletion,
    OpenAIChatCompletion,
)
from semantic_kernel.agents import ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import ChatHistory, AuthorRole
from semantic_kernel.contents import ChatMessageContent

from .config import settings, has_semantic_kernel_config
from .plugins.product_plugin import ProductPlugin
from .plugins.reference_plugin import ReferencePlugin
from .plugins.orders_plugin import OrdersPlugin

logger = logging.getLogger(__name__)

class SemanticKernelService:
    """Service for managing semantic kernel and agent orchestration"""
    
    def __init__(self):
        self.kernel = None
        self.orchestration = None
        self.runtime = None
        self.is_configured = has_semantic_kernel_config()
        self.use_simple = settings.use_simple_router
        
        if self.is_configured:
            try:
                self.kernel = self._build_kernel()
                if not self.use_simple:
                    self.orchestration, self.runtime = self._create_handoff_orchestration()
                logger.info("Semantic Kernel service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Semantic Kernel service: {e}")
                self.is_configured = False

    def _build_kernel(self) -> Kernel:
        """Build and configure the semantic kernel"""
        kernel = Kernel()

        # Configure Azure OpenAI service
        if settings.azure_openai_endpoint and settings.azure_openai_api_key and settings.azure_openai_deployment_name:
            kernel.add_service(
                AzureChatCompletion(
                    deployment_name=settings.azure_openai_deployment_name,
                    endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                )
            )
        elif settings.azure_openai_api_key and settings.azure_openai_deployment_name:
            # Fallback to OpenAI if configured
            kernel.add_service(OpenAIChatCompletion(
                model_id=settings.azure_openai_deployment_name, 
                api_key=settings.azure_openai_api_key
            ))
        else:
            raise RuntimeError("No LLM configured. Set Azure OpenAI environment variables.")

        # Register plugins
        if "product" in settings.semantic_kernel_plugins:
            kernel.add_plugin(ProductPlugin(), plugin_name="product")
        
        if "reference" in settings.semantic_kernel_plugins:
            kernel.add_plugin(ReferencePlugin(), plugin_name="reference")
        
        if "orders" in settings.semantic_kernel_plugins:
            kernel.add_plugin(OrdersPlugin(), plugin_name="orders")

        return kernel

    def _create_agents(self):
        """Create specialized agents"""
        product_lookup = ChatCompletionAgent(
            name="product_lookup",
            kernel=self.kernel,
            instructions=(
                "You are a product expert. Use the ProductPlugin functions to answer.\n"
                "If the user provides a SKU, call product.get_by_sku. Otherwise, call product.search with their query.\n"
                "Always return helpful prose followed by a compact JSON code block of the items you used."
            ),
        )

        reference_doc = ChatCompletionAgent(
            name="reference_doc",
            kernel=self.kernel,
            instructions=(
                "You answer policy and reference questions using ReferencePlugin.\n"
                "Call reference.lookup with the user's question, then summarize clearly."
            ),
        )

        customer_orders = ChatCompletionAgent(
            name="customer_orders",
            kernel=self.kernel,
            instructions=(
                "You help customers with orders.\n"
                "If they give an order id, call orders.get_order. If they identify a customerId, call orders.list_orders.\n"
                "Do not fabricate order details. If none found, say so and provide next steps."
            ),
        )

        router = ChatCompletionAgent(
            name="router",
            kernel=self.kernel,
            instructions=(
                "You are a routing assistant. For EVERY user message, pick EXACTLY ONE of these and hand off by name:\n"
                "- product_lookup: products, SKUs, availability, price\n"
                "- reference_doc: policies, returns, shipping, FAQs\n"
                "- customer_orders: order status, order history, tracking\n"
                "NEVER ask questions yourself. If unclear, choose the most likely target and hand off immediately."
            ),
        )

        return router, product_lookup, reference_doc, customer_orders

    def _create_handoff_orchestration(self) -> tuple[HandoffOrchestration, InProcessRuntime]:
        """Create handoff orchestration"""
        router, product_lookup, reference_doc, customer_orders = self._create_agents()

        # Hand-off rules by agent *names*
        handoffs = (
            OrchestrationHandoffs()
            .add(source_agent=router.name, target_agent=product_lookup.name)
            .add(source_agent=router.name, target_agent=reference_doc.name)
            .add(source_agent=router.name, target_agent=customer_orders.name)
        )

        logger.info("Agents loaded:", [a.name for a in [router, product_lookup, reference_doc, customer_orders]])

        # Optional: capture agent messages
        def agent_response_callback(msg: ChatMessageContent) -> None:
            logger.debug(f"[{msg.role}] {msg.content}")
            return

        orchestration = HandoffOrchestration(
            members=[router, product_lookup, reference_doc, customer_orders],
            handoffs=handoffs,
            agent_response_callback=agent_response_callback,
        )

        runtime = InProcessRuntime()
        runtime.start()
        return orchestration, runtime

    async def classify_intent(self, user_text: str) -> str:
        """Fallback classifier if HandoffOrchestration not available"""
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

        service = self.kernel.get_service(type=AzureChatCompletion) or self.kernel.get_service(type=OpenAIChatCompletion)
        result = await service.complete_chat_async(history)
        label = result.content.strip().lower()
        return label if label in {"product", "reference", "orders"} else "product"

    async def run_simple_router(self, user_text: str) -> str:
        """Run simple router without handoff orchestration"""
        intent = await self.classify_intent(user_text)
        
        if intent == "product":
            items = self.kernel.plugins["product"].search(user_text)
            return f"Product results: {items}"
        if intent == "reference":
            hits = self.kernel.plugins["reference"].lookup(user_text)
            return f"Reference info: {hits}"
        if intent == "orders":
            return json.dumps({"message": "Please provide your order id or customerId to look up orders."})
        
        return "I'm not sure yet—are you asking about products, policies, or an order?"

    async def respond(self, user_text: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        """Generate response using semantic kernel"""
        if not self.is_configured or not self.kernel:
            return {"error": "Semantic Kernel not configured"}

        try:
            if self.use_simple:
                text = await self.run_simple_router(user_text)
                return {"text": text}

            # Use handoff orchestration
            if self.orchestration and self.runtime:
                result = await self.orchestration.invoke(task=user_text, runtime=self.runtime)
                value = await result.get()
                return {"text": value if isinstance(value, str) else str(value)}
            else:
                # Fallback to simple router
                text = await self.run_simple_router(user_text)
                return {"text": text}

        except Exception as e:
            logger.error(f"Error in semantic kernel response: {e}")
            return {"error": f"Failed to generate response: {str(e)}"}

    async def shutdown(self):
        """Shutdown the service"""
        if self.runtime:
            await self.runtime.stop_when_idle()

# Global service instance - lazy initialization
semantic_kernel_service = None

def get_semantic_kernel_service():
    """Get the semantic kernel service instance with lazy initialization"""
    global semantic_kernel_service
    if semantic_kernel_service is None:
        semantic_kernel_service = SemanticKernelService()
    return semantic_kernel_service
