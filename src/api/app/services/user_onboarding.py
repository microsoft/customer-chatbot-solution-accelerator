import logging
import random
from datetime import datetime, timedelta
from typing import List

from ..cosmos_service import get_cosmos_service
from ..models import OrderStatus, Transaction, TransactionItem

logger = logging.getLogger(__name__)

SAMPLE_USER_IDS = ["sample-user-1", "sample-user-2", "sample-user-3"]


async def create_demo_order_history(user_id: str) -> List[Transaction]:
    cosmos_service = get_cosmos_service()

    existing_orders = await cosmos_service.get_orders_by_customer(user_id, limit=1)
    if existing_orders:
        logger.info(f"User {user_id} already has order history, skipping demo creation")
        return []

    logger.info(
        f"Creating demo order history for new user: {user_id} by replicating sample user orders"
    )

    demo_orders = []

    # Get all orders from sample users
    all_sample_orders = []
    for sample_user_id in SAMPLE_USER_IDS:
        try:
            sample_orders = await cosmos_service.get_orders_by_customer(
                sample_user_id, limit=50
            )
            all_sample_orders.extend(sample_orders)
            logger.info(
                f"Found {len(sample_orders)} orders for sample user {sample_user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to get orders for sample user {sample_user_id}: {e}")

    if not all_sample_orders:
        logger.warning("No sample orders found, falling back to generic demo orders")
        return await create_fallback_demo_orders(user_id)

    # Randomly select orders to replicate (between 3-8 orders)
    num_orders_to_replicate = min(random.randint(3, 8), len(all_sample_orders))
    selected_orders = random.sample(all_sample_orders, num_orders_to_replicate)

    logger.info(f"Replicating {len(selected_orders)} orders from sample users")

    for idx, sample_order in enumerate(selected_orders, start=1):
        try:
            # Create new order based on sample order
            new_order_number = f"ORD-{user_id[:8].upper()}-{idx:04d}"

            # Create transaction items
            items = []
            for item_data in sample_order.get("items", []):
                items.append(
                    TransactionItem(
                        product_id=item_data.get("product_id", ""),
                        product_title=item_data.get("product_title", ""),
                        quantity=item_data.get("quantity", 1),
                        unit_price=item_data.get("unit_price", 0.0),
                        total_price=item_data.get("total_price", 0.0),
                    )
                )

            # Create new transaction
            transaction = Transaction(
                id=f"order-{user_id}-{idx}",
                user_id=user_id,
                order_number=new_order_number,
                status=OrderStatus.DELIVERED,  # Set all replicated orders as delivered
                items=items,
                subtotal=sample_order.get("subtotal", 0.0),
                tax=sample_order.get("tax", 0.0),
                shipping=sample_order.get("shipping", 0.0),
                total=sample_order.get("total", 0.0),
                shipping_address=sample_order.get(
                    "shipping_address",
                    {
                        "street": "123 Demo Street",
                        "city": "Seattle",
                        "state": "WA",
                        "zip": "98101",
                        "country": "USA",
                    },
                ),
                payment_method=sample_order.get("payment_method", "Credit Card"),
                payment_reference=f"PAY-{random.randint(100000, 999999)}",
                created_at=datetime.utcnow()
                - timedelta(
                    days=random.randint(1, 180)
                ),  # Random date within last 6 months
                updated_at=datetime.utcnow(),
            )

            # Save to database
            transaction_dict = transaction.model_dump()
            transaction_dict["created_at"] = transaction.created_at.isoformat()
            transaction_dict["updated_at"] = transaction.updated_at.isoformat()

            cosmos_service.transactions_container.create_item(transaction_dict)  # type: ignore
            demo_orders.append(transaction)
            logger.info(
                f"Created replicated order {new_order_number} for user {user_id}"
            )

        except Exception as e:
            logger.error(f"Failed to replicate order: {e}")

    logger.info(
        f"Successfully created {len(demo_orders)} replicated orders for user {user_id}"
    )
    return demo_orders


async def create_fallback_demo_orders(user_id: str) -> List[Transaction]:
    """Fallback method if no sample orders are found"""
    logger.info("Creating fallback demo orders")

    cosmos_service = get_cosmos_service()
    demo_orders = []
    now = datetime.utcnow()

    order_scenarios = [
        {
            "days_ago": 15,
            "status": OrderStatus.DELIVERED,
            "products": [
                {
                    "id": "prod-001",
                    "title": "Dusty Rose Paint - 1 Gallon",
                    "price": 45.99,
                    "qty": 2,
                },
                {
                    "id": "prod-005",
                    "title": "Premium Paint Brush Set",
                    "price": 29.99,
                    "qty": 1,
                },
            ],
        },
        {
            "days_ago": 45,
            "status": OrderStatus.DELIVERED,
            "products": [
                {
                    "id": "prod-002",
                    "title": "Forest Green Paint - 1 Gallon",
                    "price": 42.99,
                    "qty": 3,
                },
                {
                    "id": "prod-006",
                    "title": "Paint Roller Kit",
                    "price": 19.99,
                    "qty": 1,
                },
                {
                    "id": "prod-007",
                    "title": "Painter's Tape - 3 Pack",
                    "price": 12.99,
                    "qty": 2,
                },
            ],
        },
        {
            "days_ago": 90,
            "status": OrderStatus.DELIVERED,
            "products": [
                {
                    "id": "prod-003",
                    "title": "Ocean Blue Paint - 1 Gallon",
                    "price": 44.99,
                    "qty": 1,
                },
                {"id": "prod-008", "title": "Drop Cloth Set", "price": 24.99, "qty": 1},
            ],
        },
    ]

    for idx, scenario in enumerate(order_scenarios, start=1):
        order_date = now - timedelta(days=scenario["days_ago"])

        items = []
        subtotal = 0.0

        for prod in scenario["products"]:
            item_total = prod["price"] * prod["qty"]
            items.append(
                TransactionItem(
                    product_id=prod["id"],
                    product_title=prod["title"],
                    quantity=prod["qty"],
                    unit_price=prod["price"],
                    total_price=item_total,
                )
            )
            subtotal += item_total

        tax = round(subtotal * 0.08, 2)
        shipping = 0.0 if subtotal > 50 else 9.99
        total = subtotal + tax + shipping

        order_number = f"ORD-{user_id[:8].upper()}-{idx:04d}"

        transaction = Transaction(
            id=f"order-{user_id}-{idx}",
            user_id=user_id,
            order_number=order_number,
            status=scenario["status"],
            items=items,
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=total,
            shipping_address={
                "street": "123 Demo Street",
                "city": "Seattle",
                "state": "WA",
                "zip": "98101",
                "country": "USA",
            },
            payment_method="Credit Card",
            payment_reference=f"PAY-{random.randint(100000, 999999)}",
            created_at=order_date,
            updated_at=order_date,
        )

        try:
            transaction_dict = transaction.model_dump()
            transaction_dict["created_at"] = order_date.isoformat()
            transaction_dict["updated_at"] = order_date.isoformat()

            cosmos_service.transactions_container.create_item(transaction_dict)  # type: ignore
            demo_orders.append(transaction)
            logger.info(
                f"Created fallback demo order {order_number} for user {user_id}"
            )
        except Exception as e:
            logger.error(f"Failed to create fallback demo order: {e}")

    logger.info(
        f"Successfully created {len(demo_orders)} fallback demo orders for user {user_id}"
    )
    return demo_orders
