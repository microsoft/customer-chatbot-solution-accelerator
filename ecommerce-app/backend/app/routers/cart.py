import uuid
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..database import get_db_service
from ..models import (
    AddToCartRequest,
    APIResponse,
    Cart,
    CartItem,
    UpdateCartItemRequest,
)

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.get("/", response_model=Cart)
async def get_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user's shopping cart"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        
        # Return empty cart if none exists
        if not cart:
            cart = Cart(
                id=str(uuid.uuid4()),
                user_id=user_id,
                items=[],
                total_items=0,
                total_price=0.0,
            )

        return cart

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cart: {str(e)}")


@router.post("/add", response_model=APIResponse)
async def add_to_cart(
    request: AddToCartRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add item to cart"""
    try:
        user_id = current_user.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get product to validate it exists
        product = await get_db_service().get_product(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Check stock availability
        if product.stock_quantity < request.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock. Only {product.stock_quantity} items available."
            )

        # Get current cart
        cart = await get_db_service().get_cart(user_id)
        if not cart:
            cart = Cart(
                id=str(uuid.uuid4()),
                user_id=user_id,
                items=[],
                total_items=0,
                total_price=0.0,
            )

        # Check if item already exists in cart
        existing_item = None
        for item in cart.items:
            if item.product_id == request.product_id:
                existing_item = item
                break

        if existing_item:
            # Check total quantity won't exceed stock
            new_quantity = existing_item.quantity + request.quantity
            if new_quantity > product.stock_quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot add {request.quantity} more items. Cart would exceed available stock of {product.stock_quantity}."
                )
            existing_item.quantity = new_quantity
        else:
            new_item = CartItem(
                product_id=request.product_id,
                product_title=product.title,
                product_price=product.price,
                product_image=product.image,
                quantity=request.quantity,
            )
            cart.items.append(new_item)

        # Update totals
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Item added to cart successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")


@router.put("/update", response_model=APIResponse)
async def update_cart_item(
    request: UpdateCartItemRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update cart item quantity"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Find the item to update
        item_found = False
        for item in cart.items:
            if item.product_id == request.product_id:
                if request.quantity <= 0:
                    # Remove item from cart
                    cart.items.remove(item)
                else:
                    # Validate stock
                    product = await get_db_service().get_product(request.product_id)
                    if product and request.quantity > product.stock_quantity:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Requested quantity exceeds available stock of {product.stock_quantity}"
                        )
                    item.quantity = request.quantity
                item_found = True
                break

        if not item_found:
            raise HTTPException(status_code=404, detail="Item not found in cart")

        # Update totals
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Cart updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cart: {str(e)}")


@router.delete("/remove/{product_id}", response_model=APIResponse)
async def remove_from_cart(
    product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove item from cart"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Find and remove the item
        item_removed = False
        for item in cart.items[:]:  # Use slice to avoid modification during iteration
            if item.product_id == product_id:
                cart.items.remove(item)
                item_removed = True
                break

        if not item_removed:
            raise HTTPException(status_code=404, detail="Item not found in cart")

        # Update totals
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Item removed from cart successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing from cart: {str(e)}")


@router.delete("/clear", response_model=APIResponse)
async def clear_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Clear all items from cart"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Clear the cart
        await get_db_service().clear_cart(user_id)

        return APIResponse(message="Cart cleared successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cart: {str(e)}")