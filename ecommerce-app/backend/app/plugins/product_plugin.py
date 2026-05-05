import asyncio
import concurrent.futures
import logging

from semantic_kernel.functions import kernel_function

from ..cosmos_service import get_cosmos_service

logger = logging.getLogger(__name__)


def run_async_sync(coro):
    """Helper to run async functions in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, need to use a different approach
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(coro)


class ProductPlugin:
    """Enhanced plugin for product search and lookup using Cosmos DB"""

    @kernel_function(
        description="Lookup a product by ID and return natural language description"
    )
    def get_by_id(self, product_id: str) -> str:
        """Get product by ID with natural language response"""
        try:
            cosmos_service = get_cosmos_service()
            product = run_async_sync(cosmos_service.get_product_by_sku(product_id))
            if not product:
                return f"I couldn't find a product with ID '{product_id}'. Could you check the ID or try searching for products instead?"

            # Format as natural language response using Product object attributes
            response = f"**{product.title}**"
            if product.price:
                response += f" - ${product.price}"
            if product.description:
                desc = product.description
                if len(desc) > 150:
                    desc = desc[:150] + "..."
                response += f"\n\n{desc}"
            if product.category:
                response += f"\n\nCategory: {product.category}"
            if product.in_stock:
                response += "\n\n✅ In stock"
            else:
                response += "\n\n❌ Currently out of stock"

            return response

        except Exception as e:
            logger.error(f"Error getting product by ID {product_id}: {e}")
            return "I'm having trouble looking up that product right now. Please try again or contact support."

    @kernel_function(
        description="Search products with hybrid AI Search + Cosmos DB for maximum speed and accuracy"
    )
    def search(self, query: str, limit: int = 5) -> str:
        """Hybrid product search with AI Search first, then Cosmos DB fallback"""
        try:
            cosmos_service = get_cosmos_service()

            # Use hybrid search for best performance and accuracy
            products = run_async_sync(
                cosmos_service.search_products_hybrid(query, limit)
            )

            if not products:
                # Provide helpful suggestions based on query
                suggestions = self._get_search_suggestions(query)
                return f"I couldn't find any products matching '{query}'. {suggestions}"

            # Format response naturally with AI Search insights
            response_parts = []

            if len(products) == 1:
                product = products[0]

                response_parts.append(
                    f"I found a perfect match for you: **{product.title}**"
                )
                if product.price:
                    response_parts.append(
                        f"This {product.category} is priced at ${product.price}"
                    )
                if product.description:
                    desc = product.description
                    if len(desc) > 150:
                        desc = desc[:150] + "..."
                    response_parts.append(f"{desc}")
                if product.in_stock:
                    response_parts.append("✅ Available in stock")
                else:
                    response_parts.append("❌ Currently out of stock")
            else:
                response_parts.append(
                    f"I found {len(products)} products that match your search:"
                )

                for i, product in enumerate(products[:3]):  # Show top 3
                    product_dict = (
                        product.model_dump()
                        if hasattr(product, "model_dump")
                        else product
                    )
                    title = product_dict.get("title", "Unknown Product")
                    price = product_dict.get("price", "N/A")
                    category = product_dict.get("category", "paint")

                    response_parts.append(f"{i+1}. **{title}** - ${price} ({category})")

                if len(products) > 3:
                    response_parts.append(
                        f"...and {len(products) - 3} more products available."
                    )

            # Add helpful follow-up
            response_parts.append(
                "\nWould you like to know more about any of these products or need help with something specific?"
            )

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error in hybrid product search with query '{query}': {e}")
            return "I'm having trouble searching products right now. Please try again or contact support for assistance."

    @kernel_function(description="Fast product search optimized for chat responses")
    def search_fast(self, query: str, limit: int = 3) -> str:
        """Ultra-fast product search using AI Search only"""
        try:
            cosmos_service = get_cosmos_service()

            # Use AI Search only for maximum speed
            products = run_async_sync(
                cosmos_service.search_products_ai_search(query, limit)
            )

            if not products:
                return f"I couldn't find any products matching '{query}'. Try different keywords or browse our categories."

            # Quick response format for speed
            if len(products) == 1:
                product = products[0]
                return f"**{product.title}** - ${product.price} ({product.category})"
            else:
                response_parts = [f"Found {len(products)} products:"]
                for i, product in enumerate(products[:3]):
                    product_dict = (
                        product.model_dump()
                        if hasattr(product, "model_dump")
                        else product
                    )
                    title = product_dict.get("title", "Unknown Product")
                    price = product_dict.get("price", "N/A")
                    response_parts.append(f"{i+1}. **{title}** - ${price}")
                return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error in fast product search: {e}")
            return "I'm having trouble searching products right now. Please try again."

    def _get_search_suggestions(self, query: str) -> str:
        """Provide helpful search suggestions based on the query"""
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["blue", "red", "green", "white", "black", "color"]
        ):
            return "Try searching for specific color names like 'Seafoam Light', 'Obsidian Pearl', or browse by color family."
        elif any(word in query_lower for word in ["paint", "coating", "finish"]):
            return "Try searching for specific paint types like 'interior paint', 'exterior paint', or 'primer'."
        elif any(
            word in query_lower for word in ["cheap", "expensive", "budget", "premium"]
        ):
            return "Try searching by price range or specific product categories."
        else:
            return "Try searching for specific product names, colors, or categories. You can also browse our full product catalog."

    @kernel_function(
        description="Get products by category with natural language responses"
    )
    def get_by_category(self, category: str, limit: int = 5) -> str:
        """Get products by category with natural language response"""
        try:
            cosmos_service = get_cosmos_service()
            products = run_async_sync(
                cosmos_service.get_products_by_category(category, limit)
            )

            if not products:
                return f"I couldn't find any products in the '{category}' category. Try browsing other categories or search for specific products."

            response_parts = [f"Here are our {category} products:"]

            for i, product in enumerate(products[:5]):
                product_dict = (
                    product.model_dump() if hasattr(product, "model_dump") else product
                )
                title = product_dict.get("title", "Unknown Product")
                price = product_dict.get("price", "N/A")

                response_parts.append(f"{i+1}. **{title}** - ${price}")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error getting products by category '{category}': {e}")
            return f"I'm having trouble browsing the {category} category right now. Please try again."

    @kernel_function(
        description="Get all available products with natural language response"
    )
    def get_all_products(self, limit: int = 10) -> str:
        """Get all products with natural language response"""
        try:
            cosmos_service = get_cosmos_service()
            products = run_async_sync(cosmos_service.get_products({"limit": limit}))

            if not products:
                return "I don't have any products available right now. Please contact support for assistance."

            response_parts = [
                f"We offer {len(products)} products across different categories:"
            ]

            # Group by category
            categories = {}
            for product in products:
                category = product.category if product.category else "Other"
                if category not in categories:
                    categories[category] = []
                categories[category].append(product)

            for category, cat_products in list(categories.items())[
                :3
            ]:  # Show top 3 categories
                response_parts.append(f"\n**{category}:**")
                for product in cat_products[:2]:  # Show top 2 per category
                    title = product.get("title", "Unknown Product")
                    price = product.get("price", "N/A")
                    response_parts.append(f"- {title} (${price})")

            if len(categories) > 3:
                response_parts.append(
                    f"\n...and {len(categories) - 3} more categories available."
                )

            response_parts.append(
                "\nWould you like to explore a specific category or search for something particular?"
            )

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error getting all products: {e}")
            return "I'm having trouble accessing our product catalog right now. Please try again or contact support."
