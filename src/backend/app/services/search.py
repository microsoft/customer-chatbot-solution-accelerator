from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from ..config import settings

_client = SearchClient(
    endpoint=settings.search_endpoint,
    index_name=settings.search_index,
    credential=AzureKeyCredential(settings.search_api_key),
)

def search_reference(query: str, top: int = 5):
    results = _client.search(search_text=query, top=top, query_type="simple")
    hits = []
    for r in results:
        hits.append({
            "id": r.get("id"),
            "title": r.get("title"),
            "content": r.get("content"),
            "score": getattr(r, "@search.score", None),
        })
    return hits
