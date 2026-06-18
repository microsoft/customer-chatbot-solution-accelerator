from typing import List

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db_service
from ..models import Product

router = APIRouter(prefix="/api/services", tags=["healthcare"])


@router.get("/", response_model=List[Product])
async def get_services(
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
        raise HTTPException(status_code=500, detail=f"Error fetching services: {str(e)}")


@router.get("/categories", response_model=List[str])
async def get_service_categories():
    try:
        return await get_db_service().get_product_categories()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")
