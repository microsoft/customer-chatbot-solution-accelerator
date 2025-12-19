import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_current_user
from ..config import settings
from ..database import get_db_service
from ..models import (
    AddToCartRequest,
    APIResponse,
    Cart,
    CartItem,
    TransactionCreate,
    TransactionItem,
)

router = APIRouter(prefix="/api/cart", tags=["cart"])


@router.post("/add", response_model=APIResponse)
async def add_to_cart(
    request: AddToCartRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Add item to cart"""
    try:
        user_id = current_user.get("user_id")
        print(f"Cart ADD - Current user: {current_user}")
        print(f"Cart ADD - User ID: {user_id}")
        print(f"Cart ADD - Request: {request}")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get product to validate it exists
        product = await get_db_service().get_product(request.product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

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
            existing_item.quantity += request.quantity
        else:
            new_item = CartItem(
                product_id=request.product_id,
                product_title=product.title,
                product_price=product.price,
                product_image=product.image,
                quantity=request.quantity,
            )
            cart.items.append(new_item)

        # Update totals efficiently
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Item added to cart successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding to cart: {str(e)}")


@router.get("/", response_model=Cart)
async def get_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get user's cart"""
    try:
        user_id = current_user.get("user_id")
        print(f"Cart GET - Current user: {current_user}")
        print(f"Cart GET - User ID: {user_id}")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        print(f"Cart GET - Retrieved cart: {cart}")

        if not cart:
            # Create empty cart
            cart = Cart(
                id=str(uuid.uuid4()),
                user_id=user_id,
                items=[],
                total_items=0,
                total_price=0.0,
            )
            print(f"Cart GET - Created empty cart: {cart}")
        return cart
    except Exception as e:
        print(f"Cart GET - Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching cart: {str(e)}")


@router.put("/update", response_model=APIResponse)
async def update_cart_item(
    product_id: str,
    quantity: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update cart item quantity"""
    try:
        user_id = current_user.get("user_id")
        print(f"Cart UPDATE - Current user: {current_user}")
        print(f"Cart UPDATE - User ID: {user_id}")
        print(f"Cart UPDATE - Product ID: {product_id}, Quantity: {quantity}")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Find and update item
        item_found = False
        for item in cart.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    cart.items.remove(item)
                else:
                    item.quantity = quantity
                item_found = True
                break

        if not item_found and quantity > 0:
            # Add new item
            product = await get_db_service().get_product(product_id)
            if not product:
                raise HTTPException(status_code=404, detail="Product not found")

            new_item = CartItem(
                product_id=product_id,
                product_title=product.title,
                product_price=product.price,
                product_image=product.image,
                quantity=quantity,
            )
            cart.items.append(new_item)

        # Update totals efficiently
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Cart updated successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating cart: {str(e)}")


@router.delete("/{product_id}", response_model=APIResponse)
async def remove_from_cart(
    product_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove item from cart"""
    try:
        user_id = current_user.get("user_id")
        print(f"Cart DELETE - Current user: {current_user}")
        print(f"Cart DELETE - User ID: {user_id}")
        print(f"Cart DELETE - Product ID: {product_id}")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = await get_db_service().get_cart(user_id)
        if not cart:
            raise HTTPException(status_code=404, detail="Cart not found")

        # Remove item
        cart.items = [item for item in cart.items if item.product_id != product_id]

        # Update totals efficiently
        cart.total_items = sum(item.quantity for item in cart.items)
        cart.total_price = sum(item.total_price for item in cart.items)

        # Save cart
        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Item removed from cart successfully")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error removing from cart: {str(e)}"
        )


@router.delete("/", response_model=APIResponse)
async def clear_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Clear all items from cart"""
    try:
        user_id = current_user.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        cart = Cart(
            id=str(uuid.uuid4()),
            user_id=user_id,
            items=[],
            total_items=0,
            total_price=0.0,
        )

        await get_db_service().update_cart(user_id, cart)

        return APIResponse(message="Cart cleared successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cart: {str(e)}")


@router.post("/checkout", response_model=APIResponse)
async def checkout_cart(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Checkout cart and create order"""
    try:
        user_id = current_user.get("user_id")
        print(f"Cart CHECKOUT - Current user: {current_user}")
        print(f"Cart CHECKOUT - User ID: {user_id}")

        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        # Get user's cart
        cart = await get_db_service().get_cart(user_id)
        if not cart or not cart.items:
            raise HTTPException(status_code=400, detail="Cart is empty")

        print(f"Cart CHECKOUT - Cart items: {len(cart.items)}")

        # Convert cart items to transaction items
        transaction_items = []
        for cart_item in cart.items:
            transaction_item = TransactionItem(
                product_id=cart_item.product_id,
                product_title=cart_item.product_title,
                quantity=cart_item.quantity,
                unit_price=cart_item.product_price,
                total_price=cart_item.total_price,
            )
            transaction_items.append(transaction_item)

        # Create transaction
        transaction_data = TransactionCreate(
            items=transaction_items,
            shipping_address={
                "name": current_user.get("name", "Customer"),
                "email": current_user.get("email", ""),
                "address": "123 Main St",  # Default address for demo
                "city": "Anytown",
                "state": "ST",
                "zip": "12345",
                "country": "US",
            },
            payment_method="credit_card",  # Default payment method for demo
            payment_reference=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        )

        # Create the transaction
        transaction = await get_db_service().create_transaction(
            transaction_data, user_id
        )
        print(f"Cart CHECKOUT - Created transaction: {transaction.id}")

        # Clear the cart after successful checkout
        empty_cart = Cart(
            id=str(uuid.uuid4()),
            user_id=user_id,
            items=[],
            total_items=0,
            total_price=0.0,
        )
        await get_db_service().update_cart(user_id, empty_cart)
        print(f"Cart CHECKOUT - Cleared cart for user: {user_id}")

        return APIResponse(
            message="Order created successfully",
            data={
                "order_id": transaction.id,
                "order_number": transaction.order_number,
                "total": transaction.total,
                "status": transaction.status.value,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Cart CHECKOUT - Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during checkout: {str(e)}")
