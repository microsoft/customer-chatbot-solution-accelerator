#!/usr/bin/env python3
"""
Comprehensive Cosmos DB Seeding Script
This script seeds both products and sample transactions into the new Cosmos DB
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosResourceNotFoundError

# Get configuration from environment variables
COSMOS_ENDPOINT = os.getenv('COSMOS_DB_ENDPOINT')
COSMOS_KEY = os.getenv('COSMOS_DB_KEY')
DATABASE_NAME = os.getenv('COSMOS_DB_DATABASE_NAME', 'ecommerce_db')

if not COSMOS_ENDPOINT or not COSMOS_KEY:
    print("❌ Missing Cosmos DB configuration!")
    print("Please set COSMOS_DB_ENDPOINT and COSMOS_DB_KEY environment variables")
    exit(1)

# Products data from CSV (matching your existing data structure)
ALL_PRODUCTS = [
    {"ProductID": "CP-0001", "ProductName": "Snow Veil", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A crisp white with a hint of warmth — perfect for open, modern interiors.", "ProductPunchLine": "Soft white, airy, minimal, fresh", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/SnowVeil.jpg"},
    {"ProductID": "CP-0002", "ProductName": "Porcelain Mist", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A gentle off-white that softens spaces with a cozy, inviting glow.", "ProductPunchLine": "Warm neutral, beige, cozy, calm", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/PorcelainMist.jpg"},
    {"ProductID": "CP-0003", "ProductName": "Stone Dusk", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A balanced mix of gray and beige, ideal for grounding a room without heaviness.", "ProductPunchLine": "Greige, muted, balanced, modern", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/StoneDusk.jpg"},
    {"ProductID": "CP-0004", "ProductName": "Fog Harbor", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A moody gray with blue undertones that feels sleek and contemporary.", "ProductPunchLine": "Cool gray, stormy, industrial, sleek", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/FogHarbor.jpg"},
    {"ProductID": "CP-0005", "ProductName": "Graphite Fade", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A dark graphite shade that adds weight and sophistication to feature walls.", "ProductPunchLine": "Charcoal, deep gray, moody, bold", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/GraphiteFade.jpg"},
    {"ProductID": "CP-0006", "ProductName": "Obsidian Pearl", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A rich black that creates contrast and drama while staying refined.", "ProductPunchLine": "Black, matte, dramatic, luxe", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/ObsidianPearl.jpg"},
    {"ProductID": "CP-0007", "ProductName": "Steel Sky", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A mid-tone slate blue that feels steady, grounded, and architectural.", "ProductPunchLine": "Slate, bluish gray, urban, cool", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/SteelSky.jpg"},
    {"ProductID": "CP-0008", "ProductName": "Blue Ash", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A softened navy with gray undertones — stylish but not overpowering.", "ProductPunchLine": "Midnight, muted navy, grounding, refined", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/BlueAsh.jpg"},
    {"ProductID": "CP-0009", "ProductName": "Cloud Drift", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A breezy pastel blue that brings calm and a sense of open sky.", "ProductPunchLine": "Pale blue, soft, tranquil, airy", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/CloudDrift.jpg"},
    {"ProductID": "CP-0010", "ProductName": "Silver Shore", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A frosty gray with subtle silver hints — sharp, bright, and clean.", "ProductPunchLine": "Cool gray, icy, clean, modern", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/SilverShore.jpg"},
    {"ProductID": "CP-0011", "ProductName": "Seafoam Light", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A soft seafoam tone that feels breezy and coastal without being too bold.", "ProductPunchLine": "Pale green, misty, fresh, coastal", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/SeafoamLight.jpg"},
    {"ProductID": "CP-0012", "ProductName": "Quiet Moss", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A sage-infused gray that adds organic calm to any interior palette.", "ProductPunchLine": "Sage gray, organic, muted, grounding", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/QuietMoss.jpg"},
    {"ProductID": "CP-0013", "ProductName": "Olive Stone", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A grounded olive shade that pairs well with natural textures like wood and linen.", "ProductPunchLine": "Earthy, muted green, natural, rustic", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/OliveStone.jpg"},
    {"ProductID": "CP-0014", "ProductName": "Verdant Haze", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A muted teal that blends serenity with just enough depth for modern accents.", "ProductPunchLine": "Soft teal, subdued, calming, serene", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/VerdantHaze.jpg"},
    {"ProductID": "CP-0015", "ProductName": "Glacier Tint", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A barely-there aqua that brings a refreshing, clean lift to light spaces.", "ProductPunchLine": "Pale aqua, refreshing, crisp, airy", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/GlacierTint.jpg"},
    {"ProductID": "CP-0016", "ProductName": "Pine Shadow", "ProductCategory": "Paint Shades", "Price": 59.5, "ProductDescription": "A forest-tinged gray with a natural edge, anchoring without feeling heavy.", "ProductPunchLine": "Forest gray, cool green, earthy, grounding", "ImageURL": "https://raw.githubusercontent.com/TravisHilbert/CCBSAP/main/JPG/PineShadow.jpg"}
]

# Sample transactions for all users
SAMPLE_TRANSACTIONS = [
    {
        "user_id": "sample-user-1",
        "order_number": "ORD-001",
        "status": "delivered",
        "items": [
            {"product_id": "CP-0001", "product_title": "Snow Veil", "quantity": 2, "unit_price": 59.5, "total_price": 119.0},
            {"product_id": "CP-0008", "product_title": "Blue Ash", "quantity": 1, "unit_price": 59.5, "total_price": 59.5}
        ],
        "subtotal": 178.5,
        "tax": 14.28,
        "shipping": 0.0,
        "total": 192.78,
        "shipping_address": {
            "name": "John Doe",
            "street": "123 Main St",
            "city": "Seattle",
            "state": "WA",
            "zip": "98101",
            "country": "USA"
        },
        "payment_method": "Credit Card",
        "payment_reference": "PAY-001"
    },
    {
        "user_id": "sample-user-2", 
        "order_number": "ORD-002",
        "status": "shipped",
        "items": [
            {"product_id": "CP-0004", "product_title": "Fog Harbor", "quantity": 1, "unit_price": 59.5, "total_price": 59.5},
            {"product_id": "CP-0011", "product_title": "Seafoam Light", "quantity": 1, "unit_price": 59.5, "total_price": 59.5}
        ],
        "subtotal": 119.0,
        "tax": 9.52,
        "shipping": 0.0,
        "total": 128.52,
        "shipping_address": {
            "name": "Jane Smith",
            "street": "456 Oak Ave",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "USA"
        },
        "payment_method": "PayPal",
        "payment_reference": "PAY-002"
    },
    {
        "user_id": "sample-user-3",
        "order_number": "ORD-003", 
        "status": "processing",
        "items": [
            {"product_id": "CP-0013", "product_title": "Olive Stone", "quantity": 3, "unit_price": 59.5, "total_price": 178.5},
            {"product_id": "CP-0016", "product_title": "Pine Shadow", "quantity": 2, "unit_price": 59.5, "total_price": 119.0}
        ],
        "subtotal": 297.5,
        "tax": 23.8,
        "shipping": 0.0,
        "total": 321.3,
        "shipping_address": {
            "name": "Bob Johnson",
            "street": "789 Pine St",
            "city": "San Francisco",
            "state": "CA",
            "zip": "94102",
            "country": "USA"
        },
        "payment_method": "Credit Card",
        "payment_reference": "PAY-003"
    }
]

def create_cosmos_client():
    """Create and return a Cosmos DB client"""
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        return client
    except Exception as e:
        print(f"❌ Error creating Cosmos client: {e}")
        return None

def get_database_and_containers(client):
    """Get database and all containers"""
    try:
        database = client.get_database_client(DATABASE_NAME)
        
        containers = {
            'products': database.get_container_client('products'),
            'users': database.get_container_client('users'),
            'chat_sessions': database.get_container_client('chat_sessions'),
            'carts': database.get_container_client('carts'),
            'transactions': database.get_container_client('transactions')
        }
        
        return database, containers
    except Exception as e:
        print(f"❌ Error getting database/containers: {e}")
        return None, None

def seed_products(container):
    """Seed products into the products container"""
    print("🌱 Seeding products...")
    
    success_count = 0
    error_count = 0
    
    for product in ALL_PRODUCTS:
        try:
            # Convert to backend model format
            product_doc = {
                "id": str(uuid.uuid4()),
                "title": product["ProductName"],
                "price": product["Price"],
                "original_price": product["Price"] * 1.2,  # 20% markup for original price
                "rating": 4.0 + (hash(product["ProductID"]) % 10) / 10,  # Random rating 4.0-4.9
                "review_count": (hash(product["ProductID"]) % 100) + 10,  # Random review count 10-109
                "image": product["ImageURL"],
                "category": product["ProductCategory"],
                "in_stock": True,
                "description": product["ProductDescription"],
                "tags": product["ProductPunchLine"].split(", "),
                "specifications": {
                    "punchLine": product["ProductPunchLine"],
                    "productId": product["ProductID"]
                },
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            container.create_item(body=product_doc)
            print(f"✅ Inserted: {product['ProductName']} ({product['ProductID']})")
            success_count += 1
            
        except CosmosResourceExistsError:
            print(f"⚠️  Product already exists: {product['ProductName']} ({product['ProductID']})")
        except Exception as e:
            print(f"❌ Error inserting {product['ProductName']}: {e}")
            error_count += 1
    
    print(f"📊 Products Summary: {success_count} inserted, {error_count} errors")
    return success_count, error_count

def seed_transactions(container):
    """Seed sample transactions into the transactions container"""
    print("🌱 Seeding sample transactions...")
    
    success_count = 0
    error_count = 0
    
    for transaction in SAMPLE_TRANSACTIONS:
        try:
            # Add Cosmos DB required fields
            transaction_doc = {
                "id": str(uuid.uuid4()),
                "user_id": transaction["user_id"],
                "order_number": transaction["order_number"],
                "status": transaction["status"],
                "items": transaction["items"],
                "subtotal": transaction["subtotal"],
                "tax": transaction["tax"],
                "shipping": transaction["shipping"],
                "total": transaction["total"],
                "shipping_address": transaction["shipping_address"],
                "payment_method": transaction["payment_method"],
                "payment_reference": transaction["payment_reference"],
                "created_at": (datetime.utcnow() - timedelta(days=hash(transaction["order_number"]) % 30)).isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            container.create_item(body=transaction_doc)
            print(f"✅ Inserted transaction: {transaction['order_number']} for user {transaction['user_id']}")
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error inserting transaction {transaction['order_number']}: {e}")
            error_count += 1
    
    print(f"📊 Transactions Summary: {success_count} inserted, {error_count} errors")
    return success_count, error_count

def seed_sample_users(container):
    """Seed sample users"""
    print("🌱 Seeding sample users...")
    
    sample_users = [
        {
            "id": "sample-user-1",
            "email": "john.doe@example.com",
            "name": "John Doe",
            "role": "customer",
            "is_active": True,
            "preferences": {"theme": "light", "notifications": True},
            "last_login": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "created_at": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "sample-user-2",
            "email": "jane.smith@example.com", 
            "name": "Jane Smith",
            "role": "customer",
            "is_active": True,
            "preferences": {"theme": "dark", "notifications": False},
            "last_login": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "created_at": (datetime.utcnow() - timedelta(days=15)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "sample-user-3",
            "email": "bob.johnson@example.com",
            "name": "Bob Johnson", 
            "role": "customer",
            "is_active": True,
            "preferences": {"theme": "light", "notifications": True},
            "last_login": datetime.utcnow().isoformat(),
            "created_at": (datetime.utcnow() - timedelta(days=7)).isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    success_count = 0
    error_count = 0
    
    for user in sample_users:
        try:
            container.create_item(body=user)
            print(f"✅ Inserted user: {user['name']} ({user['email']})")
            success_count += 1
        except Exception as e:
            print(f"❌ Error inserting user {user['name']}: {e}")
            error_count += 1
    
    print(f"📊 Users Summary: {success_count} inserted, {error_count} errors")
    return success_count, error_count

def main():
    print("🚀 Starting Cosmos DB Data Seeding...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Endpoint: {COSMOS_ENDPOINT}")
    
    # Create Cosmos client
    client = create_cosmos_client()
    if not client:
        print("❌ Failed to create Cosmos client")
        return
    
    # Get database and containers
    database, containers = get_database_and_containers(client)
    if not containers:
        print("❌ Failed to get database/containers")
        return
    
    print("✅ Connected to Cosmos DB successfully!")
    
    # Seed data
    total_success = 0
    total_errors = 0
    
    # Seed products
    success, errors = seed_products(containers['products'])
    total_success += success
    total_errors += errors
    
    # Seed users
    success, errors = seed_sample_users(containers['users'])
    total_success += success
    total_errors += errors
    
    # Seed transactions
    success, errors = seed_transactions(containers['transactions'])
    total_success += success
    total_errors += errors
    
    print(f"\n🎉 Seeding completed!")
    print(f"📊 Final Results:")
    print(f"   ✅ Total items inserted: {total_success}")
    print(f"   ❌ Total errors: {total_errors}")
    print(f"   📝 Products: {len(ALL_PRODUCTS)}")
    print(f"   👥 Users: 3")
    print(f"   🛒 Transactions: {len(SAMPLE_TRANSACTIONS)}")

if __name__ == "__main__":
    main()
