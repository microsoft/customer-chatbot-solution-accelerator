from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..cosmos_service import get_cosmos_service

router = APIRouter(prefix="/api/banking/transactions", tags=["banking"])


@router.get("/")
async def get_transactions(current_user: dict = Depends(get_current_user)) -> List[dict[str, Any]]:
    user_id = current_user.get("id") or current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    try:
        orders = await get_cosmos_service().get_orders_by_customer(user_id, limit=20)
        return [
            {
                "id": order.get("id"),
                "reference": order.get("order_number"),
                "status": order.get("status"),
                "amount": order.get("total"),
                "created_at": order.get("created_at"),
                "items": order.get("items", []),
            }
            for order in orders
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching transactions: {str(e)}")
