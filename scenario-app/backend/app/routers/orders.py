from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import get_current_authenticated_user
from ..database import get_db_service
from ..models import Order, OrderCreate, OrderStatus

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("/", response_model=Order)
async def place_order(
    body: OrderCreate,
    current_user: Dict[str, Any] = Depends(get_current_authenticated_user),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    cart = await get_db_service().get_cart(user_id)
    if not cart or not cart.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    pm = (
        body.payment_method.value
        if hasattr(body.payment_method, "value")
        else str(body.payment_method)
    )

    order = await get_db_service().create_order(
        user_id,
        cart,
        body.shipping_address.model_dump(),
        pm,
    )
    if body.payment_reference:
        order.payment_reference = body.payment_reference

    await get_db_service().clear_cart(user_id)
    return order


@router.get("/", response_model=List[Order])
async def list_orders(
    current_user: Dict[str, Any] = Depends(get_current_authenticated_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[OrderStatus] = None,
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    return await get_db_service().get_customer_orders(
        user_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/{order_id}", response_model=Order)
async def get_order_detail(
    order_id: str,
    current_user: Dict[str, Any] = Depends(get_current_authenticated_user),
):
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")

    order = await get_db_service().get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.customer_id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return order
