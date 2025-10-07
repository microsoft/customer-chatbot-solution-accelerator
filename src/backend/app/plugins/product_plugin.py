import json
from semantic_kernel.functions import kernel_function
from ..services import sql
class ProductPlugin:
    @kernel_function(description="Search for products by name or description.")
    def search_products(self, query: str, top: int = 5) -> str:
        try:
            print('Searching products for query:', query)
            # from app.services import sql
            print("query" , query)
            items = sql.search_products(query, limit=top)
        except Exception as ex:
            return json.dumps({"error": f"Product search failed: {ex}"})
        trimmed = [{
            "id": p.get("id"), "sku": p.get("sku"), "name": p.get("name"),
            "description": p.get("description"), "price": p.get("price"), "inventory": p.get("inventory"),
        } for p in items]
        return json.dumps(trimmed)
    @kernel_function(description="Get a single product by SKU.")
    def get_by_sku(self, sku: str) -> str:
        try:
            from app.services import sql
            prod = sql.find_product_by_sku(sku)
        except Exception as ex:
            return json.dumps({"error": f"Product lookup failed: {ex}"})
        if not prod:
            return json.dumps({"message": f"No product found for SKU {sku}"})
        if prod.get("description") and len(prod["description"]) > 240:
            prod["description"] = prod["description"][:240] + "..."
        return json.dumps(prod)
