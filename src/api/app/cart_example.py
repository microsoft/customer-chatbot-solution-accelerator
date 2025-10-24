#!/usr/bin/env python3
"""
Example of CartItem model usage with datetime fields
"""
import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from models import CartItem, Cart
import json

def demo_cart_item_creation():
    """Demonstrate how CartItem automatically sets added_at timestamp"""
    
    print("=== CartItem Creation Examples ===\n")
    
    # Example 1: Create a cart item - added_at is automatically set
    print("1. Creating a CartItem:")
    cart_item1 = CartItem(
        product_id="paint-001",
        product_title="Premium White Paint",
        product_price=29.99,
        product_image="/images/white-paint.jpg",
        quantity=2
        # Note: added_at is NOT specified - it will be auto-generated
    )
    
    print(f"   Product: {cart_item1.product_title}")
    print(f"   Quantity: {cart_item1.quantity}")
    print(f"   Unit Price: ${cart_item1.product_price}")
    print(f"   Total Price: ${cart_item1.total_price}")
    print(f"   Added At: {cart_item1.added_at}")
    print(f"   Added At (ISO format): {cart_item1.added_at.isoformat()}")
    
    # Example 2: Create another item a moment later
    print("\n2. Creating another CartItem (different timestamp):")
    import time
    time.sleep(0.1)  # Small delay to show different timestamps
    
    cart_item2 = CartItem(
        product_id="paint-002",
        product_title="Blue Ocean Paint",
        product_price=34.99,
        product_image="/images/blue-paint.jpg",
        quantity=1
    )
    
    print(f"   Product: {cart_item2.product_title}")
    print(f"   Added At: {cart_item2.added_at}")
    print(f"   Time difference: {(cart_item2.added_at - cart_item1.added_at).total_seconds()} seconds")
    
    # Example 3: Create a complete cart with multiple items
    print("\n3. Creating a Cart with multiple CartItems:")
    cart = Cart(
        id="cart-12345",
        user_id="guest-user-00000000",
        items=[cart_item1, cart_item2],
        total_items=3,  # 2 + 1
        total_price=cart_item1.total_price + cart_item2.total_price
    )
    
    print(f"   Cart ID: {cart.id}")
    print(f"   User ID: {cart.user_id}")
    print(f"   Total Items: {cart.total_items}")
    print(f"   Total Price: ${cart.total_price}")
    print(f"   Cart Created At: {cart.created_at}")
    print(f"   Cart Updated At: {cart.updated_at}")
    
    # Example 4: Show JSON serialization
    print("\n4. JSON representation:")
    cart_json = cart.model_dump()
    print(json.dumps(cart_json, indent=2, default=str))
    
    # Example 5: Show what happens when you explicitly set added_at
    print("\n5. Explicitly setting added_at:")
    specific_time = datetime(2024, 10, 24, 14, 30, 0)
    cart_item3 = CartItem(
        product_id="paint-003",
        product_title="Red Fire Paint",
        product_price=39.99,
        product_image="/images/red-paint.jpg",
        quantity=1,
        added_at=specific_time  # Explicitly set the timestamp
    )
    
    print(f"   Product: {cart_item3.product_title}")
    print(f"   Added At (explicit): {cart_item3.added_at}")

if __name__ == "__main__":
    demo_cart_item_creation()