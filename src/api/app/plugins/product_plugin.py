from semantic_kernel.functions import kernel_function
from ..cosmos_service import get_cosmos_service
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

class ProductPlugin:
    """Plugin for product search and lookup using Cosmos DB"""
    
    @kernel_function(description="Lookup a product by ID and return JSON")
    def get_by_id(self, product_id: str) -> str:
        """Get product by ID"""
        try:
            cosmos_service = get_cosmos_service()
            product = run_async_sync(cosmos_service.get_product_by_sku(product_id))
            if not product:
                return json.dumps({"error": f"No product found with ID: {product_id}"})
            
            if hasattr(product, 'model_dump'):
                product_dict = product.model_dump()
            else:
                product_dict = product
            
            # Convert datetime objects to ISO format strings
            for key, value in product_dict.items():
                if hasattr(value, 'isoformat'):
                    product_dict[key] = value.isoformat()
                
            return json.dumps(product_dict)
        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            return json.dumps({"error": f"Failed to lookup product: {str(e)}"})

    @kernel_function(description="Full-text search over products; returns JSON list")
    def search(self, query: str, limit: int = 10) -> str:
        """Search products by query"""
        try:
            cosmos_service = get_cosmos_service()
            products = run_async_sync(cosmos_service.search_products(query, limit=limit))
            if not products:
                return json.dumps([])
            
            products_list = []
            for product in products:
                if hasattr(product, 'model_dump'):
                    product_dict = product.model_dump()
                else:
                    product_dict = product
                
                # Convert datetime objects to ISO format strings
                for key, value in product_dict.items():
                    if hasattr(value, 'isoformat'):
                        product_dict[key] = value.isoformat()
                
                products_list.append(product_dict)
                
            return json.dumps(products_list)
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {e}")
            return json.dumps({"error": f"Failed to search products: {str(e)}"})

    @kernel_function(description="Get products by category; returns JSON list")
    def get_by_category(self, category: str, limit: int = 10) -> str:
        """Get products by category"""
        try:
            cosmos_service = get_cosmos_service()
            products = run_async_sync(cosmos_service.get_products_by_category(category, limit=limit))
            if not products:
                return json.dumps([])
            
            products_list = []
            for product in products:
                if hasattr(product, 'model_dump'):
                    product_dict = product.model_dump()
                else:
                    product_dict = product
                
                # Convert datetime objects to ISO format strings
                for key, value in product_dict.items():
                    if hasattr(value, 'isoformat'):
                        product_dict[key] = value.isoformat()
                
                products_list.append(product_dict)
                    
            return json.dumps(products_list)
        except Exception as e:
            logger.error(f"Error getting products by category '{category}': {e}")
            return json.dumps({"error": f"Failed to get products by category: {str(e)}"})

    @kernel_function(description="Search products by query; returns JSON list")
    def search_products(self, query: str, limit: int = 10) -> str:
        """Search products by query - alias for search method"""
        return self.search(query, limit)
