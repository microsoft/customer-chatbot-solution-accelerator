from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential
from ..config import settings, has_cosmos_db_config
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def _get_container():
    """Get Cosmos DB container with lazy initialization"""
    if not has_cosmos_db_config():
        logger.warning("Cosmos DB not configured")
        return None
    
    try:
        # Use DefaultAzureCredential for authentication
        cred = DefaultAzureCredential(exclude_cli_credential=True)
        client = CosmosClient(settings.cosmos_db_endpoint, credential=cred)
        db = client.get_database_client(settings.cosmos_db_database_name)
        container = db.get_container_client(settings.cosmos_db_containers.get("orders", "orders"))
        logger.info("Cosmos DB container initialized successfully")
        return container
    except Exception as e:
        logger.error(f"Failed to initialize Cosmos DB container: {e}")
        return None

def get_order_by_id(order_id: str):
    """Get order by ID from Cosmos DB"""
    container = _get_container()
    if not container:
        logger.warning("Cosmos DB not available")
        return None
    
    try:
        items = list(container.query_items(
            query="SELECT * FROM c WHERE c.id = @id",
            parameters=[{"name": "@id", "value": order_id}],
            enable_cross_partition_query=True,
        ))
        return items[0] if items else None
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {e}")
        return None

def list_orders_for_customer(customer_id: str, top: int = 10):
    """List orders for a customer from Cosmos DB"""
    container = _get_container()
    if not container:
        logger.warning("Cosmos DB not available")
        return []
    
    try:
        items = list(container.query_items(
            query="SELECT * FROM c WHERE c.customerId = @customerId ORDER BY c.createdAt DESC",
            parameters=[{"name": "@customerId", "value": customer_id}],
            enable_cross_partition_query=True,
            max_item_count=top,
        ))
        return items
    except Exception as e:
        logger.error(f"Error listing orders for customer {customer_id}: {e}")
        return []






