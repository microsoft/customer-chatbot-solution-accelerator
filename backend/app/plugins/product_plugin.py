from semantic_kernel.functions import kernel_function
from ..cosmos_service import get_cosmos_service
import json
import logging

logger = logging.getLogger(__name__)

class ProductPlugin:
    """Plugin for product search and lookup using Cosmos DB"""
    
    @kernel_function(description="Lookup a product by SKU and return JSON")
    def get_by_sku(self, sku: str) -> str:
        """Get product by SKU"""
        try:
            cosmos_service = get_cosmos_service()
            product = cosmos_service.get_product_by_sku(sku)
            if not product:
                return json.dumps({"error": f"No product found with SKU: {sku}"})
            
            # Convert to dict if it's a model instance
            if hasattr(product, 'model_dump'):
                product_dict = product.model_dump()
            else:
                product_dict = product
                
            return json.dumps(product_dict)
        except Exception as e:
            logger.error(f"Error getting product by SKU {sku}: {e}")
            return json.dumps({"error": f"Failed to lookup product: {str(e)}"})

    @kernel_function(description="Full-text search over products; returns JSON list")
    def search(self, query: str, limit: int = 10) -> str:
        """Search products by query"""
        try:
            cosmos_service = get_cosmos_service()
            products = cosmos_service.search_products(query, limit=limit)
            if not products:
                return json.dumps([])
            
            # Convert to list of dicts
            products_list = []
            for product in products:
                if hasattr(product, 'model_dump'):
                    products_list.append(product.model_dump())
                else:
                    products_list.append(product)
                    
            return json.dumps(products_list)
        except Exception as e:
            logger.error(f"Error searching products with query '{query}': {e}")
            return json.dumps({"error": f"Failed to search products: {str(e)}"})

    @kernel_function(description="Get products by category; returns JSON list")
    def get_by_category(self, category: str, limit: int = 10) -> str:
        """Get products by category"""
        try:
            cosmos_service = get_cosmos_service()
            products = cosmos_service.get_products_by_category(category, limit=limit)
            if not products:
                return json.dumps([])
            
            # Convert to list of dicts
            products_list = []
            for product in products:
                if hasattr(product, 'model_dump'):
                    products_list.append(product.model_dump())
                else:
                    products_list.append(product)
                    
            return json.dumps(products_list)
        except Exception as e:
            logger.error(f"Error getting products by category '{category}': {e}")
            return json.dumps({"error": f"Failed to get products by category: {str(e)}"})
