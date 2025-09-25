import asyncio
import os
import json
import logging
from typing import List, Dict, Any, Optional

from azure.identity import AzureCliCredential, DefaultAzureCredential, get_bearer_token_provider

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.functions import kernel_function

from .config import settings, has_semantic_kernel_config
from .cosmos_service import get_cosmos_service

logger = logging.getLogger(__name__)

class OrderStatusPlugin:
    """Plugin for order status operations"""
    
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """Look up an order by id in Cosmos DB and summarize its status."""
        try:
            import asyncio
            cosmos_service = get_cosmos_service()
            
            # Run the async method
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_order_async(order_id))
                        order = future.result()
                else:
                    order = loop.run_until_complete(self._get_order_async(order_id))
            except RuntimeError:
                order = asyncio.run(self._get_order_async(order_id))
            
            if not order:
                return f"No order found with id {order_id}."

            # Convert to dict if it's a model instance
            if hasattr(order, 'model_dump'):
                order_dict = order.model_dump()
            else:
                order_dict = order

            status = order_dict.get("status") or order_dict.get("state") or "(unknown status)"
            total = order_dict.get("total") or order_dict.get("amount")
            created = order_dict.get("created_at") or order_dict.get("timestamp")
            
            summary_bits = [f"status={status}"]
            if total is not None:
                summary_bits.append(f"total={total}")
            if created:
                summary_bits.append(f"created={created}")
                
            return f"Order {order_id}: " + ", ".join(summary_bits)
        except Exception as ex:
            return f"Failed to query order {order_id}: {ex}"

    async def _get_order_async(self, order_id: str):
        """Async helper for getting order by ID"""
        cosmos_service = get_cosmos_service()
        # For now, return a mock order since we don't have orders in the DB
        # In a real implementation, you'd query the orders collection
        return None  # No orders implemented yet

    @kernel_function
    def list_recent_orders(self, customer_id: str, top: int = 5) -> str:
        """List recent orders for a customer (JSON array as string)."""
        try:
            import asyncio
            cosmos_service = get_cosmos_service()
            
            # Run the async method
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_orders_async(customer_id, top))
                        orders = future.result()
                else:
                    orders = loop.run_until_complete(self._get_orders_async(customer_id, top))
            except RuntimeError:
                orders = asyncio.run(self._get_orders_async(customer_id, top))
            
            if not orders:
                return json.dumps([])
            
            # Trim large docs
            trimmed = []
            for order in orders:
                if hasattr(order, 'model_dump'):
                    order_dict = order.model_dump()
                else:
                    order_dict = order
                    
                trimmed.append({
                    "id": order_dict.get("id"),
                    "status": order_dict.get("status") or order_dict.get("state"),
                    "total": order_dict.get("total") or order_dict.get("amount"),
                    "created_at": order_dict.get("created_at") or order_dict.get("timestamp"),
                })
            return json.dumps(trimmed)
        except Exception as ex:
            return json.dumps({"error": f"Failed to list orders: {ex}"})

    async def _get_orders_async(self, customer_id: str, top: int):
        """Async helper for getting orders by customer"""
        cosmos_service = get_cosmos_service()
        # For now, return empty list since we don't have orders in the DB
        # In a real implementation, you'd query the orders collection
        return []

class OrderRefundPlugin:
    """Plugin for order refund operations"""
    
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process a refund for an order."""
        logger.info(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."

class OrderReturnPlugin:
    """Plugin for order return operations"""
    
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """Process a return for an order."""
        logger.info(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."

class ProductLookupPlugin:
    """Plugin for product lookup operations"""
    
    @kernel_function
    def search_products(self, query: str, top: int = 5) -> str:
        """Search products by query"""
        try:
            import asyncio
            cosmos_service = get_cosmos_service()
            
            # Run the async method in a new event loop or get the current one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context, need to use a different approach
                    # Create a task and run it
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._search_products_async(query, top))
                        products = future.result()
                else:
                    products = loop.run_until_complete(self._search_products_async(query, top))
            except RuntimeError:
                # No event loop, create one
                products = asyncio.run(self._search_products_async(query, top))
            
            if not products:
                return json.dumps([])
            
            trimmed = []
            for product in products:
                if hasattr(product, 'model_dump'):
                    product_dict = product.model_dump()
                else:
                    product_dict = product
                    
                trimmed.append({
                    "id": product_dict.get("id"),
                    "sku": product_dict.get("sku"),
                    "title": product_dict.get("title") or product_dict.get("name"),
                    "description": product_dict.get("description"),
                    "price": product_dict.get("price"),
                    "inventory": product_dict.get("inventory"),
                })
            return json.dumps(trimmed)
        except Exception as ex:
            return json.dumps({"error": f"Failed to search products: {ex}"})

    async def _search_products_async(self, query: str, top: int) -> List:
        """Async helper for searching products"""
        cosmos_service = get_cosmos_service()
        # For now, get all products and filter them
        # In a real implementation, you'd want to implement proper search
        all_products = await cosmos_service.get_products()
        
        if not all_products:
            return []
        
        # Simple text search in title and description
        query_lower = query.lower()
        filtered = []
        for product in all_products:
            product_dict = product.model_dump() if hasattr(product, 'model_dump') else product
            title = (product_dict.get("title") or product_dict.get("name") or "").lower()
            description = (product_dict.get("description") or "").lower()
            
            if query_lower in title or query_lower in description:
                filtered.append(product)
                if len(filtered) >= top:
                    break
        
        # If no exact matches, return all products for the agent to explain what's available
        if not filtered and all_products:
            return all_products[:top]
        
        return filtered

    @kernel_function
    def get_by_sku(self, sku: str) -> str:
        """Get product by SKU"""
        try:
            import asyncio
            cosmos_service = get_cosmos_service()
            
            # Run the async method
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, self._get_by_sku_async(sku))
                        product = future.result()
                else:
                    product = loop.run_until_complete(self._get_by_sku_async(sku))
            except RuntimeError:
                product = asyncio.run(self._get_by_sku_async(sku))
            
            if not product:
                return json.dumps({"message": f"No product found for SKU {sku}"})
            
            if hasattr(product, 'model_dump'):
                product_dict = product.model_dump()
            else:
                product_dict = product
                
            # Trim description length for brevity
            if product_dict.get("description") and len(product_dict["description"]) > 240:
                product_dict["description"] = product_dict["description"][:240] + "..."
            return json.dumps(product_dict)
        except Exception as ex:
            return json.dumps({"error": f"Failed to lookup product: {ex}"})

    async def _get_by_sku_async(self, sku: str):
        """Async helper for getting product by SKU"""
        cosmos_service = get_cosmos_service()
        all_products = await cosmos_service.get_products()
        
        if not all_products:
            return None
        
        # Find product by SKU
        for product in all_products:
            product_dict = product.model_dump() if hasattr(product, 'model_dump') else product
            if product_dict.get("sku") == sku:
                return product
        
        return None

class ReferenceLookupPlugin:
    """Plugin to query Azure Search for reference, return, and support info."""
    
    def __init__(self):
        self.search_client = None
        self.is_configured = settings.azure_search_endpoint and settings.azure_search_api_key
        
        if self.is_configured:
            try:
                from azure.search.documents import SearchClient
                from azure.core.credentials import AzureKeyCredential
                
                credential = AzureKeyCredential(settings.azure_search_api_key)
                self.search_client = SearchClient(
                    endpoint=settings.azure_search_endpoint,
                    index_name=settings.azure_search_index,
                    credential=credential
                )
            except Exception as e:
                logger.error(f"Failed to initialize Azure Search client: {e}")
                self.is_configured = False

    @kernel_function
    def lookup_reference(self, query: str, top: int = 3) -> str:
        """Lookup reference information"""
        if not self.is_configured or not self.search_client:
            return json.dumps({"error": "Reference search not available"})
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                include_total_count=True
            )
            
            hits = []
            for result in results:
                hit = {
                    "title": result.get("title", ""),
                    "content": result.get("content", ""),
                    "url": result.get("url", ""),
                    "score": result.get("@search.score", 0)
                }
                hits.append(hit)
            
            return json.dumps(hits)
        except Exception as ex:
            return json.dumps({"error": f"Failed to search reference info: {ex}"})

class HandoffOrchestrator:
    """Main orchestrator for handoff-based chat"""
    
    def __init__(self):
        self.is_configured = has_semantic_kernel_config()
        self._runtime = None
        self._orchestration = None
        self._initialized = False
        
        if self.is_configured:
            logger.info("Handoff orchestrator created, will initialize on first use")

    async def _ensure_initialized(self):
        """Ensure the orchestration is initialized"""
        if self._initialized:
            return
            
        if not self.is_configured:
            return
            
        try:
            await self._setup_orchestration()
            self._initialized = True
            logger.info("Handoff orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize handoff orchestrator: {e}")
            self.is_configured = False

    async def _setup_orchestration(self):
        """Setup the handoff orchestration"""
        agents, handoffs = self._get_agents()
        self._runtime = InProcessRuntime()
        
        # Start the runtime - this might be synchronous
        try:
            start_result = self._runtime.start()
            if start_result and hasattr(start_result, '__await__'):
                await start_result
        except Exception as e:
            logger.error(f"Failed to start runtime: {e}")
            raise

        self._assistant_messages: List[str] = []
        self._last_agent: str | None = None

        def _capture_callback(message: ChatMessageContent) -> None:
            self._agent_response_callback(message)
            if message.content and message.role == AuthorRole.ASSISTANT:
                self._assistant_messages.append(message.content)
                self._last_agent = message.name

        self._orchestration = HandoffOrchestration(
            members=agents,
            handoffs=handoffs,
            agent_response_callback=_capture_callback,
        )

    def _get_agents(self) -> tuple[List[Agent], OrchestrationHandoffs]:
        """Get agents and handoff relationships"""
        # Use Azure OpenAI configuration
        api_key = settings.azure_openai_api_key
        endpoint = settings.azure_openai_endpoint
        deployment = settings.azure_openai_deployment_name
        api_version = settings.azure_openai_api_version

        support_agent = ChatCompletionAgent(
            name="TriageAgent",
            description="A customer support agent that triages issues.",
            instructions="Handle customer requests and route them to appropriate specialists.",
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
        )

        refund_agent = ChatCompletionAgent(
            name="RefundAgent",
            description="A customer support agent that handles refunds.",
            instructions="Handle refund requests using the OrderRefundPlugin.",
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
            plugins=[OrderRefundPlugin()],
        )

        order_status_agent = ChatCompletionAgent(
            name="OrderStatusAgent",
            description="A customer support agent that checks order status.",
            instructions="Handle order status requests using the OrderStatusPlugin.",
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
            plugins=[OrderStatusPlugin()],
        )

        order_return_agent = ChatCompletionAgent(
            name="OrderReturnAgent",
            description="A customer support agent that handles order returns.",
            instructions="Handle order return requests using the OrderReturnPlugin.",
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
            plugins=[OrderReturnPlugin()],
        )

        product_lookup_agent = ChatCompletionAgent(
            name="ProductLookupAgent",
            description="Helps users find products by name, description, or SKU.",
            instructions=(
                "You are a helpful product search assistant. When users ask about products: "
                "1. Use get_by_sku if they provide a specific SKU (alphanumeric code). "
                "2. Use search_products for general product searches. "
                "3. Always provide a helpful response explaining what you found. "
                "4. If no products match their search, explain what products are available instead. "
                "5. Be friendly and helpful in your responses. "
                "6. Never just return raw JSON - always provide context and explanation."
            ),
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
            plugins=[ProductLookupPlugin()],
        )

        reference_lookup_agent = ChatCompletionAgent(
            name="ReferenceLookupAgent",
            description="Answers questions about returns, policies, and support using Azure Search.",
            instructions=(
                "For any question about returns, policies, customer support, or reference info, ALWAYS call lookup_reference with the user's query. "
                "Respond ONLY with the compact JSON array of results. Do NOT include any summary, explanation, or extra text—just the JSON. "
                "If no results are found, return an empty JSON array []."
            ),
            service=AzureChatCompletion(
                deployment_name=deployment,
                endpoint=endpoint,
                api_key=api_key,
                api_version=api_version,
            ),
            plugins=[ReferenceLookupPlugin()],
        )

        # Define the handoff relationships between agents
        handoffs = (
            OrchestrationHandoffs()
            .add_many(
                source_agent=support_agent.name,
                target_agents={
                    refund_agent.name: "Refund related issues",
                    order_status_agent.name: "Order status or tracking questions",
                    order_return_agent.name: "Order return related issues",
                    product_lookup_agent.name: "Product search, SKU, availability, price",
                    reference_lookup_agent.name: "Returns, policies, support, reference info",
                },
            )
            .add(
                source_agent=refund_agent.name,
                target_agent=support_agent.name,
                description="Back to triage if not refund related",
            )
            .add(
                source_agent=order_status_agent.name,
                target_agent=support_agent.name,
                description="Back to triage if not status related",
            )
            .add(
                source_agent=order_return_agent.name,
                target_agent=support_agent.name,
                description="Back to triage if not return related",
            )
            .add(
                source_agent=product_lookup_agent.name,
                target_agent=support_agent.name,
                description="Back to triage if not product related",
            )
            .add(
                source_agent=reference_lookup_agent.name,
                target_agent=support_agent.name,
                description="Back to triage if not reference related",
            )
        )

        return [support_agent, refund_agent, order_status_agent, order_return_agent, product_lookup_agent, reference_lookup_agent], handoffs

    def _agent_response_callback(self, message: ChatMessageContent) -> None:
        """Observer function to print the messages from the agents."""
        logger.debug(f"{message.name}: {message.content}")
        for item in message.items:
            if isinstance(item, FunctionCallContent):
                logger.debug(f"Calling '{item.name}' with arguments '{item.arguments}'")
            if isinstance(item, FunctionResultContent):
                logger.debug(f"Result from '{item.name}' is '{item.result}'")

    async def respond(self, user_text: str, history: List[Dict[str, str]] | None = None) -> Dict[str, Any]:
        """Generate response using handoff orchestration"""
        if not self.is_configured:
            return {"error": "Handoff orchestrator not configured"}

        try:
            # Ensure initialization
            await self._ensure_initialized()
            
            if not self._orchestration or not self._runtime:
                return {"error": "Handoff orchestrator failed to initialize"}

            # Reset assistant messages for this conversation
            self._assistant_messages = []
            
            # Invoke the orchestration
            result = await self._orchestration.invoke(task=user_text, runtime=self._runtime)
            value = await result.get()
            
            # Get the last message or the result
            last_msg = self._assistant_messages[-1] if self._assistant_messages else (value if isinstance(value, str) else str(value))
            awaiting_user = False
            
            # Check if the last message ends with a question
            if self._assistant_messages and last_msg.strip().endswith("?"):
                awaiting_user = True
                
            return {
                "messages": self._assistant_messages if self._assistant_messages else [last_msg],
                "awaiting_user": awaiting_user,
                "text": last_msg  # For backward compatibility
            }
        except Exception as e:
            logger.error(f"Error in handoff orchestrator response: {e}")
            return {"error": f"Failed to generate response: {str(e)}"}

    async def shutdown(self):
        """Shutdown the orchestrator"""
        if self._runtime and self._initialized:
            await self._runtime.stop_when_idle()
            self._initialized = False

# Global orchestrator instance - lazy initialization
handoff_orchestrator = None

def get_handoff_orchestrator():
    """Get the handoff orchestrator instance with lazy initialization"""
    global handoff_orchestrator
    if handoff_orchestrator is None:
        handoff_orchestrator = HandoffOrchestrator()
    return handoff_orchestrator
