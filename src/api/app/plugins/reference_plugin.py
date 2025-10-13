from semantic_kernel.functions import kernel_function
from ..services.search import search_reference
from ..config import has_azure_search_config
import json
import logging

logger = logging.getLogger(__name__)

class ReferencePlugin:
    """Plugin for reference document lookup using Azure Search"""
    
    def __init__(self):
        self.is_configured = has_azure_search_config()

    @kernel_function(description="Search reference documents for policy and support information")
    def lookup(self, query: str, top: int = 3) -> str:
        """Lookup reference information"""
        if not self.is_configured:
            return json.dumps({
                "error": "Reference search not available - Azure Search not configured",
                "fallback": "Please contact support for assistance with policies and reference information."
            })
        
        try:
            hits = search_reference(query, top)
            return json.dumps(hits)
        except Exception as e:
            logger.error(f"Error searching reference documents: {e}")
            return json.dumps({
                "error": f"Failed to search reference documents: {str(e)}",
                "fallback": "Please contact support for assistance."
            })

    @kernel_function(description="Get return policy information")
    def get_return_policy(self) -> str:
        """Get return policy information"""
        return self.lookup("return policy refund exchange", top=2)

    @kernel_function(description="Get shipping information")
    def get_shipping_info(self) -> str:
        """Get shipping information"""
        return self.lookup("shipping delivery time cost", top=2)

    @kernel_function(description="Get warranty information")
    def get_warranty_info(self) -> str:
        """Get warranty information"""
        return self.lookup("warranty guarantee coverage", top=2)
