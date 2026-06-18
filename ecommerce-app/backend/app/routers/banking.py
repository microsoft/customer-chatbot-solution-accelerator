from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db_service
from ..models import Product

router = APIRouter(prefix="/api/accounts", tags=["banking"])


@router.get("/", response_model=List[Product])
async def get_accounts(
    category: str | None = Query(None),
    query: str | None = Query(None),
):
    try:
        search_params = {
            "category": category,
            "query": query,
            "sort_by": "name",
            "sort_order": "asc",
        }
        return await get_db_service().get_products(search_params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching accounts: {str(e)}")
