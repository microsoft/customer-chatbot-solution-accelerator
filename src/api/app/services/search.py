from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ..config import settings, has_azure_search_config
import logging

logger = logging.getLogger(__name__)

_client = None

def get_search_client():
    """Get Azure Search client with lazy initialization"""
    global _client
    if _client is None and has_azure_search_config():
        try:
            _client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_index,
                credential=AzureKeyCredential(settings.azure_search_api_key),
            )
            logger.info("Azure Search client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Search client: {e}")
            _client = None
    return _client

def search_reference(query: str, top: int = 5):
    """Search reference documents"""
    client = get_search_client()
    if not client:
        logger.warning("Azure Search not configured, returning empty results")
        return []
    
    try:
        results = client.search(search_text=query, top=top, query_type="simple")
        hits = []
        for r in results:
            hits.append({
                "id": r.get("id"),
                "title": r.get("title"),
                "content": r.get("content"),
                "score": getattr(r, "@search.score", None),
            })
        return hits
    except Exception as e:
        logger.error(f"Error searching reference documents: {e}")
        return []









