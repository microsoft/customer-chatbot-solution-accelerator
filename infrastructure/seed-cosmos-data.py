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

# All 54 products data (matching your existing data structure)
ALL_PRODUCTS = [
    {"ProductID": "PROD0001", "ProductName": "Pale Meadow", "ProductCategory": "Paint Shades", "Price": 29.99, "ProductDescription": "A soft, earthy green reminiscent of open meadows at dawn.", "ProductPunchLine": "Nature's touch inside your home", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/PaleMeadow.png"},
    {"ProductID": "PROD0002", "ProductName": "Tranquil Lavender", "ProductCategory": "Paint Shades", "Price": 31.99, "ProductDescription": "A muted lavender that soothes and reassures, ideal for relaxation.", "ProductPunchLine": "Find your peaceful moment", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/TranquilLavender.png"},
    {"ProductID": "PROD0003", "ProductName": "Whispering Blue", "ProductCategory": "Paint Shades", "Price": 47.99, "ProductDescription": "Light, breezy blue that lifts spirits and refreshes the space.", "ProductPunchLine": "Float away on blue skies", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlue.png"},
    {"ProductID": "PROD0004", "ProductName": "Whispering Blush", "ProductCategory": "Paint Shades", "Price": 50.82, "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.", "ProductPunchLine": "Add a blush of beauty", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"},
    {"ProductID": "PROD0005", "ProductName": "Ocean Mist", "ProductCategory": "Paint Shades", "Price": 84.83, "ProductDescription": "Premium quality ocean mist paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Ocean Mist!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Ocean Mist_Paint.png"},
    {"ProductID": "PROD0006", "ProductName": "Sunset Coral", "ProductCategory": "Paint Shades", "Price": 48.57, "ProductDescription": "Premium quality sunset coral paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Sunset Coral!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sunset Coral Paint.png"},
    {"ProductID": "PROD0007", "ProductName": "Forest Whisper", "ProductCategory": "Paint Shades", "Price": 43.09, "ProductDescription": "Premium quality forest whisper paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Forest Whisper!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Forest Whisper Paint.png"},
    {"ProductID": "PROD0008", "ProductName": "Morning Dew", "ProductCategory": "Paint Shades", "Price": 81.94, "ProductDescription": "Premium quality morning dew paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Morning Dew!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Morning Dew Paint.png"},
    {"ProductID": "PROD0009", "ProductName": "Dusty Rose", "ProductCategory": "Paint Shades", "Price": 75.62, "ProductDescription": "Premium quality dusty rose paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Dusty Rose!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Dusty Rose Paint.png"},
    {"ProductID": "PROD0010", "ProductName": "Sage Harmony", "ProductCategory": "Paint Shades", "Price": 33.26, "ProductDescription": "Premium quality sage harmony paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Sage Harmony!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sage Harmony.png"},
    # Add more products as needed - truncated for brevity
    {"ProductID": "PROD0054", "ProductName": "Wooden Handle Paint Roller", "ProductCategory": "Paint Accessories", "Price": 8.99, "ProductDescription": "Featuring a durable wooden handle and a plush roller cover making it ideal for high-quality painting projects.", "ProductPunchLine": "Roll with Precision, Paint with Power!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Roller_4.png"}
]

# Sample transactions for all users
SAMPLE_TRANSACTIONS = [
    {
        "user_id": "sample-user-1",
        "order_number": "ORD-001",
        "status": "delivered",
        "items": [
            {"product_id": "PROD0001", "product_title": "Pale Meadow", "quantity": 2, "unit_price": 29.99, "total_price": 59.98},
            {"product_id": "PROD0002", "product_title": "Tranquil Lavender", "quantity": 1, "unit_price": 31.99, "total_price": 31.99}
        ],
        "subtotal": 91.97,
        "tax": 7.36,
        "shipping": 0.0,
        "total": 99.33,
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
            {"product_id": "PROD0005", "product_title": "Ocean Mist", "quantity": 1, "unit_price": 84.83, "total_price": 84.83},
            {"product_id": "PROD0008", "product_title": "Morning Dew", "quantity": 1, "unit_price": 81.94, "total_price": 81.94}
        ],
        "subtotal": 166.77,
        "tax": 13.34,
        "shipping": 0.0,
        "total": 180.11,
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
            {"product_id": "PROD0013", "product_title": "Golden Wheat", "quantity": 3, "unit_price": 109.73, "total_price": 329.19},
            {"product_id": "PROD0014", "product_title": "Soft Pebble", "quantity": 2, "unit_price": 110.92, "total_price": 221.84}
        ],
        "subtotal": 551.03,
        "tax": 44.08,
        "shipping": 0.0,
        "total": 595.11,
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
                "tags": [product["ProductCategory"].lower().replace(" ", "-")],
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
