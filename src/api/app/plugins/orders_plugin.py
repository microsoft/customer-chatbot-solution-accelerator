from semantic_kernel.functions import kernel_function
from cosmos_service import get_cosmos_service
import json
import logging
import asyncio
import concurrent.futures

logger = logging.getLogger(__name__)

def run_async_sync(coro):
    """Run an async coroutine synchronously, handling event loop conflicts"""
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, use a thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(coro)

class OrdersPlugin:
    """Plugin for order management using Cosmos DB"""
    
    @kernel_function(description="Get order by ID and return JSON")
    def get_order(self, order_id: str) -> str:
        """Get order by ID"""
        try:
            cosmos_service = get_cosmos_service()
            order = run_async_sync(cosmos_service.get_order_by_id(order_id))
            if not order:
                return json.dumps({"error": f"No order found with ID: {order_id}"})
            
            if hasattr(order, 'model_dump'):
                order_dict = order if isinstance(order, dict) else order.model_dump()
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
            orders = run_async_sync(cosmos_service.get_orders_by_customer(customer_id, limit=limit))
            if not orders:
                return json.dumps([])
            
            orders_list = []
            for order in orders:
                if hasattr(order, 'model_dump'):
                    orders_list.append(order if isinstance(order, dict) else order.model_dump())
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
            order = run_async_sync(cosmos_service.get_order_by_id(order_id))
            if not order:
                return json.dumps({"error": f"No order found with ID: {order_id}"})
            
            if hasattr(order, 'model_dump'):
                order_dict = order if isinstance(order, dict) else order.model_dump()
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
    
    @kernel_function(description="Get orders within return window for a customer; returns JSON list")
    def get_returnable_orders(self, customer_id: str) -> str:
        """Get orders that are still within the return window (30 days)"""
        try:
            cosmos_service = get_cosmos_service()
            orders = run_async_sync(cosmos_service.get_orders_in_date_range(customer_id, days=30))
            
            if not orders:
                return json.dumps([])
            
            returnable_orders = []
            for order in orders:
                order_dict = order if isinstance(order, dict) else (order.model_dump() if hasattr(order, 'model_dump') else order)
                returnable_orders.append(order_dict)
            
            return json.dumps(returnable_orders)
        except Exception as e:
            logger.error(f"Error getting returnable orders for customer {customer_id}: {e}")
            return json.dumps({"error": f"Failed to get returnable orders: {str(e)}"})
    
    @kernel_function(description="Get orders from the past N days for a customer; returns JSON list")
    def get_orders_by_date_range(self, customer_id: str, days: int = 180) -> str:
        """Get orders from the last N days (default 180 days / 6 months)"""
        try:
            cosmos_service = get_cosmos_service()
            orders = run_async_sync(cosmos_service.get_orders_in_date_range(customer_id, days=days))
            
            if not orders:
                return json.dumps([])
            
            orders_list = []
            for order in orders:
                order_dict = order if isinstance(order, dict) else (order.model_dump() if hasattr(order, 'model_dump') else order)
                orders_list.append(order_dict)
            
            return json.dumps(orders_list)
        except Exception as e:
            logger.error(f"Error getting orders by date range for customer {customer_id}: {e}")
            return json.dumps({"error": f"Failed to get orders by date range: {str(e)}"})
    
    @kernel_function(description="Check if a specific order is still returnable (within 30-day window)")
    def check_if_returnable(self, order_id: str) -> str:
        """Check if an order is still within the return window"""
        try:
            cosmos_service = get_cosmos_service()
            is_returnable = run_async_sync(cosmos_service.is_order_returnable(order_id, return_window_days=30))
            
            result = {
                "order_id": order_id,
                "is_returnable": is_returnable,
                "return_window_days": 30
            }
            
            return json.dumps(result)
        except Exception as e:
            logger.error(f"Error checking if order {order_id} is returnable: {e}")
            return json.dumps({"error": f"Failed to check if order is returnable: {str(e)}"})