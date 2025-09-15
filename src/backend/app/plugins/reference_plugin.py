from semantic_kernel.functions import kernel_function
from ..services.search import search_reference
import json

class ReferencePlugin:
    @kernel_function(description="Search reference docs / policies; return top matches as JSON")
    def lookup(self, query: str) -> str:
        return json.dumps(search_reference(query))
