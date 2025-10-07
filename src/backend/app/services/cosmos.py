from azure.cosmos import CosmosClient
from ..config import settings

from functools import lru_cache
from ..config import settings

@lru_cache(maxsize=1)
def _container():
    from azure.identity import DefaultAzureCredential
    from azure.cosmos import CosmosClient
    if not settings.cosmos_endpoint:
        raise RuntimeError("Missing COSMOS_ENDPOINT in .env")
    cred = DefaultAzureCredential()
    client = CosmosClient(settings.cosmos_endpoint, credential=settings.cosmos_key)
    db = client.get_database_client(settings.cosmos_db)
    return db.get_container_client(settings.cosmos_container)

def get_order_by_id(order_id: str):
        items = list(_container().query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": order_id}],
            enable_cross_partition_query=True,
        ))
        return items[0] if items else None

def list_orders_for_customer(customer_id: str, top: int = 10):
        items = list(_container().query_items(
            query="SELECT * FROM c WHERE c.customerId = @customerId ORDER BY c.createdAt DESC",
            parameters=[{"name": "@customerId", "value": customer_id}],
            enable_cross_partition_query=True,
            max_item_count=top,
        ))
        return items

def search_orders(order_id: str = None, product_id: str = None, description: str = None, top: int = 10):
    clauses = []
    params = []
    if order_id:
        clauses.append("c.id = @orderId")
        params.append({"name": "@orderId", "value": order_id})
    if product_id:
        clauses.append("c.order.productId = @productId")
        params.append({"name": "@productId", "value": product_id})
    if description:
        clauses.append("CONTAINS(c.order.description, @desc)")
        params.append({"name": "@desc", "value": description})
    if not clauses:
        raise ValueError("At least one search field must be provided.")
    where = " AND ".join(clauses)
    query = f"SELECT * FROM c WHERE {where} ORDER BY c.createdAt DESC"
    items = list(_container().query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True,
        max_item_count=top,
    ))
    return items