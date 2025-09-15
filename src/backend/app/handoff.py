# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import json

from azure.identity import AzureCliCredential, DefaultAzureCredential

from semantic_kernel.agents import Agent, ChatCompletionAgent, HandoffOrchestration, OrchestrationHandoffs
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatMessageContent, FunctionCallContent, FunctionResultContent
from semantic_kernel.functions import kernel_function

"""
The following sample demonstrates how to create a handoff orchestration that represents
a customer support triage system. The orchestration consists of 4 agents, each specialized
in a different area of customer support: triage, refunds, order status, and order returns.

Depending on the customer's request, agents can hand off the conversation to the appropriate
agent.

Human in the loop is achieved via a callback function similar to the one used in group chat
orchestration. Except that in the handoff orchestration, all agents have access to the
human response function, whereas in the group chat orchestration, only the manager has access
to the human response function.

This sample demonstrates the basic steps of creating and starting a runtime, creating
a handoff orchestration, invoking the orchestration, and finally waiting for the results.
"""


class OrderStatusPlugin:
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """Look up an order by id in Cosmos DB and summarize its status.

        Falls back with a helpful message if Cosmos is not configured or order not found.
        """
        try:
            from .services import cosmos  # local import
        except Exception as ex:  # pragma: no cover
            return f"Order lookup unavailable (import error: {ex})."

        try:
            doc = cosmos.get_order_by_id(order_id)
        except Exception as ex:
            return f"Failed to query order {order_id}: {ex}"

        if not doc:
            return f"No order found with id {order_id}."

        status = doc.get("status") or doc.get("state") or "(unknown status)"
        total = doc.get("total") or doc.get("amount")
        created = doc.get("createdAt") or doc.get("timestamp")
        summary_bits = [f"status={status}"]
        if total is not None:
            summary_bits.append(f"total={total}")
        if created:
            summary_bits.append(f"created={created}")
        return f"Order {order_id}: " + ", ".join(summary_bits)

    @kernel_function
    def list_recent_orders(self, customer_id: str, top: int = 5) -> str:
        """List recent orders for a customer (JSON array as string)."""
        try:
            from .services import cosmos
        except Exception as ex:  # pragma: no cover
            return json.dumps({"error": f"Order listing unavailable (import error: {ex})"})
        try:
            items = cosmos.list_orders_for_customer(customer_id, top=top)
        except Exception as ex:
            return json.dumps({"error": f"Failed to list orders: {ex}"})
        # Trim large docs
        trimmed = []
        for d in items:
            trimmed.append({
                "id": d.get("id"),
                "status": d.get("status") or d.get("state"),
                "total": d.get("total") or d.get("amount"),
                "createdAt": d.get("createdAt") or d.get("timestamp"),
            })
        return json.dumps(trimmed)


class OrderRefundPlugin:
    @kernel_function
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process a refund for an order."""
        # Simulate processing a refund
        print(f"Processing refund for order {order_id} due to: {reason}")
        return f"Refund for order {order_id} has been processed successfully."


class OrderReturnPlugin:
    @kernel_function
    def process_return(self, order_id: str, reason: str) -> str:
        """Process a return for an order."""
        # Simulate processing a return
        print(f"Processing return for order {order_id} due to: {reason}")
        return f"Return for order {order_id} has been processed successfully."


class ProductLookupPlugin:
    """Lightweight wrapper around the existing SQL product service for demo agent usage."""

    @kernel_function
    def search_products(self, query: str, top: int = 5) -> str:
        try:
            from .services import sql
        except Exception as ex:  # pragma: no cover
            return json.dumps({"error": f"Product search unavailable (import error: {ex})"})
        try:
            items = sql.search_products(query, limit=top)
        except Exception as ex:
            return json.dumps({"error": f"Failed to search products: {ex}"})
        trimmed = [
            {
                "id": p.get("id"),
                "sku": p.get("sku"),
                "name": p.get("name"),
                "price": p.get("price"),
                "inventory": p.get("inventory"),
            }
            for p in items
        ]
        return json.dumps(trimmed)

    @kernel_function
    def get_by_sku(self, sku: str) -> str:
        try:
            from .services import sql
        except Exception as ex:  # pragma: no cover
            return json.dumps({"error": f"Product lookup unavailable (import error: {ex})"})
        try:
            prod = sql.find_product_by_sku(sku)
        except Exception as ex:
            return json.dumps({"error": f"Failed to lookup product: {ex}"})
        if not prod:
            return json.dumps({"message": f"No product found for SKU {sku}"})
        # Trim description length for brevity
        if prod.get("description") and len(prod["description"]) > 240:
            prod["description"] = prod["description"][:240] + "..."
        return json.dumps(prod)


def get_agents() -> tuple[list[Agent], OrchestrationHandoffs]:
    """Return a list of agents that will participate in the Handoff orchestration and the handoff relationships.

    Feel free to add or remove agents and handoff connections.
    """
    credential = DefaultAzureCredential()

    # Support either AZURE_OPENAI_API_KEY or legacy AZURE_OPENAI_KEY
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("AZURE_OPENAI_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")

    support_agent = ChatCompletionAgent(
        name="TriageAgent",
        description="A customer support agent that triages issues.",
        instructions="Handle customer requests.",
        service=AzureChatCompletion(
            credential=credential,
            deployment_name=deployment,
            base_url=endpoint,
            api_key=api_key,
        ),
    )

    refund_agent = ChatCompletionAgent(
        name="RefundAgent",
        description="A customer support agent that handles refunds.",
        instructions="Handle refund requests.",
        service=AzureChatCompletion(
            credential=credential,
            deployment_name=deployment,
            base_url=endpoint,
            api_key=api_key,
        ),
        plugins=[OrderRefundPlugin()],
    )

    order_status_agent = ChatCompletionAgent(
        name="OrderStatusAgent",
        description="A customer support agent that checks order status.",
        instructions="Handle order status requests.",
        service=AzureChatCompletion(
            credential=credential,
            deployment_name=deployment,
            base_url=endpoint,
            api_key=api_key,
        ),
        plugins=[OrderStatusPlugin()],
    )

    order_return_agent = ChatCompletionAgent(
        name="OrderReturnAgent",
        description="A customer support agent that handles order returns.",
        instructions="Handle order return requests.",
        service=AzureChatCompletion(
            credential=credential,
            deployment_name=deployment,
            base_url=endpoint,
            api_key=api_key,
        ),
        plugins=[OrderReturnPlugin()],
    )

    product_lookup_agent = ChatCompletionAgent(
        name="ProductLookupAgent",
        description="Helps users find products by name, description, or SKU.",
        instructions=(
            "When the user asks about products, pricing, availability, or specifies a SKU: "
            "Use get_by_sku if a SKU pattern is detected (alphanumeric token). Otherwise use search_products. "
            "Summarize results briefly and include a compact JSON array or object of the items used."
        ),
        service=AzureChatCompletion(
            credential=credential,
            deployment_name=deployment,
            base_url=endpoint,
            api_key=api_key,
        ),
        plugins=[ProductLookupPlugin()],
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
    )

    return [support_agent, refund_agent, order_status_agent, order_return_agent, product_lookup_agent], handoffs


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents.

    Please note that this function is called whenever the agent generates a response,
    including the internal processing messages (such as tool calls) that are not visible
    to other agents in the orchestration.
    """
    print(f"{message.name}: {message.content}")
    for item in message.items:
        if isinstance(item, FunctionCallContent):
            print(f"Calling '{item.name}' with arguments '{item.arguments}'")
        if isinstance(item, FunctionResultContent):
            print(f"Result from '{item.name}' is '{item.result}'")


def human_response_function() -> ChatMessageContent:
    """Observer function to print the messages from the agents."""
    user_input = input("User: ")
    return ChatMessageContent(role=AuthorRole.USER, content=user_input)


async def main():
    """Main function to run the agents."""
    # 1. Create a handoff orchestration with multiple agents
    agents, handoffs = get_agents()
    handoff_orchestration = HandoffOrchestration(
        members=agents,
        handoffs=handoffs,
        agent_response_callback=agent_response_callback,
        human_response_function=human_response_function,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await handoff_orchestration.invoke(
        task="Greet the customer who is reaching out for support.",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(value)

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()

    """
    Sample output:
    TriageAgent: Hello! Thank you for reaching out for support. How can I assist you today?
    User: I'd like to track the status of my order
    TriageAgent:
    Calling 'Handoff-transfer_to_OrderStatusAgent' with arguments '{}'
    TriageAgent:
    Result from 'Handoff-transfer_to_OrderStatusAgent' is 'None'
    OrderStatusAgent: Could you please provide me with your order ID so I can check the status for you?
    User: My order ID is 123
    OrderStatusAgent:
    Calling 'OrderStatusPlugin-check_order_status' with arguments '{"order_id":"123"}'
    OrderStatusAgent:
    Result from 'OrderStatusPlugin-check_order_status' is 'Order 123 is shipped and will arrive in 2-3 days.'
    OrderStatusAgent: Your order with ID 123 has been shipped and is expected to arrive in 2-3 days. If you have any
        more questions, feel free to ask!
    User: I want to return another order of mine
    OrderStatusAgent: I can help you with that. Could you please provide me with the order ID of the order you want
        to return?
    User: Order ID 321
    OrderStatusAgent:
    Calling 'Handoff-transfer_to_TriageAgent' with arguments '{}'
    OrderStatusAgent:
    Result from 'Handoff-transfer_to_TriageAgent' is 'None'
    TriageAgent:
    Calling 'Handoff-transfer_to_OrderReturnAgent' with arguments '{}'
    TriageAgent:
    Result from 'Handoff-transfer_to_OrderReturnAgent' is 'None'
    OrderReturnAgent: Could you please provide me with the reason for the return for order ID 321?
    User: Broken item
    Processing return for order 321 due to: Broken item
    OrderReturnAgent:
    Calling 'OrderReturnPlugin-process_return' with arguments '{"order_id":"321","reason":"Broken item"}'
    OrderReturnAgent:
    Result from 'OrderReturnPlugin-process_return' is 'Return for order 321 has been processed successfully.'
    OrderReturnAgent: The return for order ID 321 has been processed successfully due to a broken item. If you need
        further assistance or have any other questions, feel free to let me know!
    User: No, bye
    Task is completed with summary: Processed the return request for order ID 321 due to a broken item.
    OrderReturnAgent:
    Calling 'Handoff-complete_task' with arguments '{"task_summary":"Processed the return request for order ID 321
        due to a broken item."}'
    OrderReturnAgent:
    Result from 'Handoff-complete_task' is 'None'
    """


if __name__ == "__main__":
    asyncio.run(main())


# --- API-friendly wrapper ---
class HandoffChatOrchestrator:
    """Wrapper that mirrors the interface of the existing `Orchestrator` (from agents.py)
    so it can be plugged into the FastAPI `/chat` endpoint.

    Usage:
        from .handoff import HandoffChatOrchestrator
        orch = HandoffChatOrchestrator()
        await orch.respond("hello")
    """

    def __init__(self) -> None:
        agents, handoffs = get_agents()
        self._runtime = InProcessRuntime()
        self._runtime.start()
        self._orchestration = HandoffOrchestration(
            members=agents,
            handoffs=handoffs,
            agent_response_callback=agent_response_callback,
        )

    async def respond(self, user_text: str, history: list[dict] | None = None) -> dict:
        # history is currently ignored in this simple demo; could be threaded by injecting prior messages
        result = await self._orchestration.invoke(task=user_text, runtime=self._runtime)
        value = await result.get()
        text = value if isinstance(value, str) else str(value)
        return {"text": text}

    async def shutdown(self):  # optional cleanup hook
        await self._runtime.stop_when_idle()