from semantic_kernel.functions import kernel_function
from ..services import cosmos
import json

class OrdersPlugin:
    @kernel_function(description="Fetch an order by order id; returns JSON")
    def get_order(self, order_id: str) -> str:
        item = cosmos.get_order_by_id(order_id)
        return json.dumps(item or {})

    @kernel_function(description="List recent orders for a customer by customerId; returns JSON list")
    def list_orders(self, customer_id: str) -> str:
        return json.dumps(cosmos.list_orders_for_customer(customer_id))
