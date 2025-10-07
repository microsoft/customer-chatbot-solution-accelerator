import json
from semantic_kernel.functions import kernel_function
class OrdersPlugin:
    @kernel_function(description="Search orders by order id, product id, or text.")
    def search_orders(self, order_id: str = None, product_id: str = None, description: str = None, top: int = 5) -> str:
        """Search orders by order ID, product ID, or description (JSON array as string)."""
        try:
            from ..services import cosmos
        except Exception as ex:
            return json.dumps({"error": f"Order search unavailable (import error: {ex})"})
        try:
            items = cosmos.search_orders(order_id=order_id, product_id=product_id, description=description, top=top)
        except Exception as ex:
            return json.dumps({"error": f"Failed to search orders: {ex}"})
        def _map(doc: dict) -> dict:
            order_obj = doc.get("order") or {}
            return {
                "id": doc.get("id"),
                "customerId": doc.get("customerId") or order_obj.get("customerId"),
                "productId": doc.get("productId") or doc.get("productid") or order_obj.get("productId"),
                "price": doc.get("price") or order_obj.get("price") or doc.get("total") or order_obj.get("total"),
                "quantity": doc.get("quantity") or order_obj.get("quantity"),
                "status": doc.get("status") or doc.get("state") or order_obj.get("status"),
                "description": doc.get("description") or order_obj.get("description"),
                "createdAt": doc.get("createdAt") or doc.get("timestamp") or order_obj.get("createdAt"),
            }
        mapped = [_map(d) for d in items]
        if not mapped:
            return "No matching orders found.\n[]"
        lines = []
        for m in mapped:
            bits = [f"status={m.get('status')}"]
            if m.get('productId') is not None:
                bits.append(f"product={m.get('productId')}")
            if m.get('quantity') is not None:
                bits.append(f"qty={m.get('quantity')}")
            if m.get('price') is not None:
                bits.append(f"price={m.get('price')}")
            lines.append(f"Order {m.get('id')}: " + ", ".join(bits))
        return "\n".join(lines) + "\n" + json.dumps(mapped)
    @kernel_function
    def check_order_status(self, order_id: str) -> str:
        """Look up an order by id in Cosmos DB and return plain text summary PLUS JSON.
        Format:
        Order <id>: status=<status>, product=<productId>, qty=<quantity>, price=<price>
        <JSON object>
        If not found returns a JSON object with message only."""
        try:
            from ..services import cosmos  # local import
        except Exception as ex:
            return json.dumps({"error": f"Order lookup unavailable (import error: {ex})"})

        try:
            doc = cosmos.get_order_by_id(order_id)
        except Exception as ex:
            return json.dumps({"error": f"Failed to query order {order_id}: {ex}"})

        if not doc:
            return json.dumps({"message": f"No order found for id {order_id}"})

        order_obj = doc.get("order") or {}
        mapped = {
            "id": doc.get("id"),
            "customerId": doc.get("customerId") or order_obj.get("customerId"),
            "productId": doc.get("productId") or doc.get("productid") or order_obj.get("productId"),
            "price": doc.get("price") or order_obj.get("price") or doc.get("total") or order_obj.get("total"),
            "quantity": doc.get("quantity") or order_obj.get("quantity"),
            "status": doc.get("status") or doc.get("state") or order_obj.get("status"),
            "description": doc.get("description") or order_obj.get("description"),
            "createdAt": doc.get("createdAt") or doc.get("timestamp") or order_obj.get("createdAt"),
        }
        summary_bits = [
            f"status={mapped.get('status')}",
        ]
        if mapped.get('productId') is not None:
            summary_bits.append(f"product={mapped.get('productId')}")
        if mapped.get('quantity') is not None:
            summary_bits.append(f"qty={mapped.get('quantity')}")
        if mapped.get('price') is not None:
            summary_bits.append(f"price={mapped.get('price')}")
        summary_line = f"Order {mapped.get('id')}: " + ", ".join(summary_bits)
        return summary_line + "\n" + json.dumps(mapped)
    @kernel_function
    def list_recent_orders(self, customer_id: str, top: int = 5) -> str:
        """List recent orders for a customer (JSON array as string)."""
        try:
            from ..services import cosmos
        except Exception as ex:  # pragma: no cover
            return json.dumps({"error": f"Order listing unavailable (import error: {ex})"})
        try:
            items = cosmos.list_orders_for_customer(customer_id, top=top)
        except Exception as ex:
            return json.dumps({"error": f"Failed to list orders: {ex}"})
        def _map(doc: dict) -> dict:
            order_obj = doc.get("order") or {}
            return {
                "id": doc.get("id"),
                "customerId": doc.get("customerId") or order_obj.get("customerId"),
                "productId": doc.get("productId") or doc.get("productid") or order_obj.get("productId"),
                "price": doc.get("price") or order_obj.get("price") or doc.get("total") or order_obj.get("total"),
                "quantity": doc.get("quantity") or order_obj.get("quantity"),
                "status": doc.get("status") or doc.get("state") or order_obj.get("status"),
                "description": doc.get("description") or order_obj.get("description"),
                "createdAt": doc.get("createdAt") or doc.get("timestamp") or order_obj.get("createdAt"),
            }
        mapped = [_map(d) for d in items]
        if not mapped:
            return f"No recent orders found for customer {customer_id}.\n[]"
        lines = []
        for m in mapped:
            bits = [f"status={m.get('status')}"]
            if m.get('productId') is not None:
                bits.append(f"product={m.get('productId')}")
            if m.get('quantity') is not None:
                bits.append(f"qty={m.get('quantity')}")
            if m.get('price') is not None:
                bits.append(f"price={m.get('price')}")
            lines.append(f"Order {m.get('id')}: " + ", ".join(bits))
        return "\n".join(lines) + "\n" + json.dumps(mapped)