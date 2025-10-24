from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from config import settings, has_azure_search_config
import logging

logger = logging.getLogger(__name__)

_client = None
_product_client = None

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

def get_product_search_client():
    """Get Azure Search client for products with lazy initialization"""
    global _product_client
    if _product_client is None and has_azure_search_config():
        try:
            _product_client = SearchClient(
                endpoint=settings.azure_search_endpoint,
                index_name=settings.azure_search_product_index,
                credential=AzureKeyCredential(settings.azure_search_api_key),
            )
            logger.info("Azure Product Search client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Product Search client: {e}")
            _product_client = None
    return _product_client

def search_reference(query: str, top: int = 5):
    """Search reference documents with enhanced capabilities"""
    client = get_search_client()
    if not client:
        logger.warning("Azure Search not configured, returning empty results")
        return []
    
    try:
        # Try semantic search first, fallback to simple search
        try:
            results = client.search(
                search_text=query,
                top=top,
                query_type="semantic",
                semantic_configuration_name="default",
                query_language="en-us",
                speller="lexicon",
                query_answer="extractive|count-3",
                query_caption="extractive|highlight-true"
            )
        except Exception as semantic_error:
            logger.warning(f"Semantic search failed, falling back to simple search: {semantic_error}")
            results = client.search(search_text=query, top=top, query_type="simple")
        
        hits = []
        for r in results:
            hit = {
                "id": r.get("id"),
                "title": r.get("title"),
                "content": r.get("content"),
                "score": getattr(r, "@search.score", None),
            }
            
            # Add semantic search enhancements if available
            if hasattr(r, "@search.answers") and r["@search.answers"]:
                hit["answers"] = [answer["text"] for answer in r["@search.answers"]]
            
            if hasattr(r, "@search.captions") and r["@search.captions"]:
                hit["captions"] = [caption["text"] for caption in r["@search.captions"]]
            
            hits.append(hit)
        
        logger.info(f"Search query '{query}' returned {len(hits)} results")
        return hits
    except Exception as e:
        logger.error(f"Error searching reference documents: {e}")
        return []

def search_reference_enhanced(query: str, top: int = 5, context: str = ""):
    """Enhanced search with context awareness and better query processing"""
    client = get_search_client()
    if not client:
        logger.warning("Azure Search not configured, returning empty results")
        return []
    
    try:
        # Enhance query with context
        enhanced_query = f"{query} {context}".strip()
        
        # Try multiple search strategies
        search_strategies = [
            # Strategy 1: Semantic search with answers
            {
                "query_type": "semantic",
                "semantic_configuration_name": "default",
                "query_answer": "extractive|count-3",
                "query_caption": "extractive|highlight-true"
            },
            # Strategy 2: Full search with highlighting
            {
                "query_type": "full",
                "highlight": "content",
                "highlight_pre_tag": "<mark>",
                "highlight_post_tag": "</mark>"
            },
            # Strategy 3: Simple search fallback
            {
                "query_type": "simple"
            }
        ]
        
        hits = []
        for strategy in search_strategies:
            try:
                results = client.search(
                    search_text=enhanced_query,
                    top=top,
                    **strategy
                )
                
                hits = []
                for r in results:
                    hit = {
                        "id": r.get("id"),
                        "title": r.get("title"),
                        "content": r.get("content"),
                        "score": getattr(r, "@search.score", None),
                    }
                    
                    # Add strategy-specific enhancements
                    if "query_answer" in strategy and hasattr(r, "@search.answers"):
                        hit["answers"] = [answer["text"] for answer in r["@search.answers"]]
                    
                    if "highlight" in strategy and hasattr(r, "@search.highlights"):
                        hit["highlights"] = r["@search.highlights"]
                    
                    hits.append(hit)
                
                if hits:  # If we got results, use this strategy
                    logger.info(f"Search strategy '{strategy['query_type']}' returned {len(hits)} results")
                    break
                    
            except Exception as strategy_error:
                logger.warning(f"Search strategy failed: {strategy_error}")
                continue
        
        return hits
    except Exception as e:
        logger.error(f"Enhanced search error: {e}")
        return search_reference(query, top)  # Fallback to basic search

def search_products(query: str, top: int = 5, context: str = ""):
    """Search products using Azure AI Search with semantic capabilities"""
    client = get_product_search_client()
    if not client:
        logger.warning("Azure Product Search not configured, returning empty results")
        return []
    
    try:
        # Enhance query with context
        enhanced_query = f"{query} {context}".strip()
        
        # Try multiple search strategies for products
        search_strategies = [
            # Strategy 1: Try semantic search first (if available)
            {
                "query_type": "semantic",
                "semantic_configuration_name": "default",
                "query_answer": "extractive|count-3",
                "query_caption": "extractive|highlight-true"
            },
            # Strategy 2: Full search with highlighting
            {
                "query_type": "full",
                "highlight": "title,description,content",
                "highlight_pre_tag": "<mark>",
                "highlight_post_tag": "</mark>"
            },
            # Strategy 3: Simple search fallback
            {
                "query_type": "simple"
            },
            # Strategy 4: Basic search (no parameters)
            {}
        ]
        
        hits = []
        for strategy in search_strategies:
            try:
                results = client.search(
                    search_text=enhanced_query,
                    top=top,
                    **strategy
                )
                
                hits = []
                for r in results:
                    hit = {
                        "id": r.get("id"),
                        "title": r.get("title"),
                        "description": r.get("description"),
                        "price": r.get("price"),
                        "category": r.get("category"),
                        "inventory": r.get("inventory"),
                        "image": r.get("image"),
                        "tags": r.get("tags", ""),
                        "score": getattr(r, "@search.score", None),
                    }
                    
                    # Add strategy-specific enhancements
                    if "query_answer" in strategy and hasattr(r, "@search.answers"):
                        hit["answers"] = [answer["text"] for answer in r["@search.answers"]]
                    
                    if "highlight" in strategy and hasattr(r, "@search.highlights"):
                        hit["highlights"] = r["@search.highlights"]
                    
                    hits.append(hit)
                
                if hits:  # If we got results, use this strategy
                    logger.info(f"Product search strategy '{strategy.get('query_type', 'basic')}' returned {len(hits)} results")
                    break
                    
            except Exception as strategy_error:
                logger.warning(f"Product search strategy failed: {strategy_error}")
                continue
        
        return hits
    except Exception as e:
        logger.error(f"Product search error: {e}")
        return []

def search_products_fast(query: str, top: int = 3):
    """Fast product search optimized for chat responses"""
    client = get_product_search_client()
    if not client:
        return []
    
    try:
        # Try semantic search first, fallback to basic search
        try:
            results = client.search(
                search_text=query,
                top=top,
                query_type="semantic",
                semantic_configuration_name="default",
                query_answer="extractive|count-2",  # Limit answers for speed
                query_caption="extractive|highlight-false"  # Disable highlighting for speed
            )
        except Exception:
            # Fallback to basic search if semantic search fails
            results = client.search(
                search_text=query,
                top=top
            )
        
        hits = []
        for r in results:
            hit = {
                "id": r.get("id"),
                "title": r.get("title"),
                "description": r.get("description"),
                "price": r.get("price"),
                "category": r.get("category"),
                "inventory": r.get("inventory"),
                "score": getattr(r, "@search.score", None),
            }
            
            # Add extracted answers if available
            if hasattr(r, "@search.answers") and r["@search.answers"]:
                hit["answers"] = [answer["text"] for answer in r["@search.answers"]]
            
            hits.append(hit)
        
        logger.info(f"Fast product search returned {len(hits)} results for query: {query}")
        return hits
        
    except Exception as e:
        logger.error(f"Fast product search error: {e}")
        return []









