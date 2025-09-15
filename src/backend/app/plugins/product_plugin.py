from semantic_kernel.functions import kernel_function
from ..services import sql
import json

class ProductPlugin:
    @kernel_function(description="Lookup a product by SKU and return JSON")
    def get_by_sku(self, sku: str) -> str:
        p = sql.find_product_by_sku(sku)
        return json.dumps({} if not p else p)

    @kernel_function(description="Full-text search over products; returns JSON list")
    def search(self, query: str) -> str:
        items = sql.search_products(query)
        return json.dumps(items)
