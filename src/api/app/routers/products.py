from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db_service
from ..models import APIResponse, Product, ProductCreate, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/", response_model=List[Product])
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating"),
    in_stock_only: bool = Query(False, description="Only show in-stock products"),
    query: Optional[str] = Query(None, description="Search query"),
    sort_by: str = Query("name", description="Sort field"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """Get products with filtering and pagination"""
    try:
        search_params = {
            "category": category,
            "min_price": min_price,
            "max_price": max_price,
            "min_rating": min_rating,
            "in_stock_only": in_stock_only,
            "query": query,
            "sort_by": sort_by,
            "sort_order": sort_order,
        }

        products = await get_db_service().get_products(search_params)

        # Simple pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_products = products[start_idx:end_idx]

        return paginated_products

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching products: {str(e)}"
        )


@router.get("/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    try:
        product = await get_db_service().get_product(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")


@router.post("/", response_model=Product)
async def create_product(product: ProductCreate):
    """Create a new product (Admin only)"""
    try:
        new_product = await get_db_service().create_product(product)
        return new_product
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")


@router.put("/{product_id}", response_model=Product)
async def update_product(product_id: str, product: ProductUpdate):
    """Update a product (Admin only)"""
    try:
        updated_product = await get_db_service().update_product(product_id, product)
        if not updated_product:
            raise HTTPException(status_code=404, detail="Product not found")
        return updated_product
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")


@router.delete("/{product_id}", response_model=APIResponse)
async def delete_product(product_id: str):
    """Delete a product (Admin only)"""
    try:
        success = await get_db_service().delete_product(product_id)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")
        return APIResponse(message="Product deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")


@router.get("/categories/list", response_model=List[str])
async def get_categories():
    """Get list of all product categories"""
    try:
        products = await get_db_service().get_products()
        categories = list(set(product.category for product in products))
        categories.sort()
        return categories
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching categories: {str(e)}"
        )
