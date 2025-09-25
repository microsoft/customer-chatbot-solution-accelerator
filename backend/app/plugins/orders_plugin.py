from semantic_kernel.functions import kernel_function
from ..cosmos_service import get_cosmos_service
import json
import logging

logger = logging.getLogger(__name__)

class OrdersPlugin:
    """Plugin for order management using Cosmos DB"""
    
    @kernel_function(description="Get order by ID and return JSON")
    def get_order(self, order_id: str) -> str:
        """Get order by ID"""
        try:
            cosmos_service = get_cosmos_service()
            order = cosmos_service.get_order_by_id(order_id)
            if not order:
                return json.dumps({"error": f"No order found with ID: {order_id}"})
            
            # Convert to dict if it's a model instance
            if hasattr(order, 'model_dump'):
                order_dict = order.model_dump()
            else:
                order_dict = order
                
            return json.dumps(order_dict)
        except Exception as e:
            logger.error(f"Error getting order {order_id}: {e}")
            return json.dumps({"error": f"Failed to get order: {str(e)}"})

    @kernel_function(description="List orders for a customer; returns JSON list")
    def list_orders(self, customer_id: str, limit: int = 10) -> str:
        """List orders for a customer"""
        try:
            cosmos_service = get_cosmos_service()
            orders = cosmos_service.get_orders_by_customer(customer_id, limit=limit)
            if not orders:
                return json.dumps([])
            
            # Convert to list of dicts
            orders_list = []
            for order in orders:
                if hasattr(order, 'model_dump'):
                    orders_list.append(order.model_dump())
                else:
                    orders_list.append(order)
                    
            return json.dumps(orders_list)
        except Exception as e:
            logger.error(f"Error listing orders for customer {customer_id}: {e}")
            return json.dumps({"error": f"Failed to list orders: {str(e)}"})

    @kernel_function(description="Get order status by ID")
    def get_order_status(self, order_id: str) -> str:
        """Get order status"""
        try:
            cosmos_service = get_cosmos_service()
            order = cosmos_service.get_order_by_id(order_id)
            if not order:
                return json.dumps({"error": f"No order found with ID: {order_id}"})
            
            # Extract status information
            if hasattr(order, 'model_dump'):
                order_dict = order.model_dump()
            else:
                order_dict = order
                
            status_info = {
                "order_id": order_id,
                "status": order_dict.get("status", "unknown"),
                "total": order_dict.get("total", 0),
                "created_at": order_dict.get("created_at", ""),
                "updated_at": order_dict.get("updated_at", "")
            }
            
            return json.dumps(status_info)
        except Exception as e:
            logger.error(f"Error getting order status {order_id}: {e}")
            return json.dumps({"error": f"Failed to get order status: {str(e)}"})

    @kernel_function(description="Process refund for an order")
    def process_refund(self, order_id: str, reason: str) -> str:
        """Process refund for an order"""
        try:
            # This would typically update the order status in the database
            # For now, we'll simulate the process
            logger.info(f"Processing refund for order {order_id} due to: {reason}")
            
            # In a real implementation, you would:
            # 1. Validate the order exists and is eligible for refund
            # 2. Update the order status
            # 3. Process the actual refund through payment provider
            # 4. Send confirmation to customer
            
            result = {
                "order_id": order_id,
                "refund_status": "processed",
                "reason": reason,
                "message": f"Refund for order {order_id} has been processed successfully"
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error processing refund for order {order_id}: {e}")
            return json.dumps({"error": f"Failed to process refund: {str(e)}"})

    @kernel_function(description="Process return for an order")
    def process_return(self, order_id: str, reason: str) -> str:
        """Process return for an order"""
        try:
            # This would typically update the order status in the database
            # For now, we'll simulate the process
            logger.info(f"Processing return for order {order_id} due to: {reason}")
            
            # In a real implementation, you would:
            # 1. Validate the order exists and is eligible for return
            # 2. Update the order status
            # 3. Generate return label
            # 4. Send confirmation to customer
            
            result = {
                "order_id": order_id,
                "return_status": "processed",
                "reason": reason,
                "message": f"Return for order {order_id} has been processed successfully"
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error processing return for order {order_id}: {e}")
            return json.dumps({"error": f"Failed to process return: {str(e)}"})
