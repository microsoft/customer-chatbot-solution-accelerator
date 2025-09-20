#!/usr/bin/env python3
"""
Clear and Seed All Products Script for Cosmos DB
This script clears existing products and seeds all 54 products from the data file
"""

import os
import json
import uuid
import csv
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosResourceNotFoundError

# Cosmos DB configuration
COSMOS_ENDPOINT = "https://ecommerce-chat-dev-cosmos.documents.azure.com:443/"
DATABASE_NAME = "ecommerce-db"
CONTAINER_NAME = "products"

def create_cosmos_client():
    """Create and return a Cosmos DB client"""
    try:
        client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
        return client
    except Exception as e:
        print(f"Error creating Cosmos client: {e}")
        return None

def get_database_and_container(client):
    """Get or create database and container"""
    try:
        # Get database
        database = client.get_database_client(DATABASE_NAME)
        
        # Get container
        container = database.get_container_client(CONTAINER_NAME)
        
        return database, container
    except Exception as e:
        print(f"Error getting database/container: {e}")
        return None, None

def clear_all_products(container):
    """Clear all existing products from the container"""
    print("🗑️ Clearing all existing products...")
    
    try:
        # Query all items
        items = list(container.query_items(
            query="SELECT c.id, c.ProductID FROM c",
            enable_cross_partition_query=True
        ))
        
        deleted_count = 0
        for item in items:
            try:
                container.delete_item(
                    item=item['id'],
                    partition_key=item['ProductID']
                )
                deleted_count += 1
                print(f"✅ Deleted: {item.get('ProductID', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error deleting {item.get('ProductID', 'Unknown')}: {e}")
        
        print(f"🗑️ Cleared {deleted_count} products")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing products: {e}")
        return False

def load_products_from_csv():
    """Load all products from the CSV data file"""
    products = []
    
    try:
        # Read the data file
        with open('../data', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                # Convert price to float
                try:
                    price = float(row['Price'])
                except ValueError:
                    price = 0.0
                
                product = {
                    "ProductID": row['ProductID'],
                    "ProductName": row['ProductName'],
                    "ProductCategory": row['ProductCategory'],
                    "Price": price,
                    "ProductDescription": row['ProductDescription'],
                    "ProductPunchLine": row['ProductPunchLine'],
                    "ImageURL": row['ImageURL']
                }
                products.append(product)
        
        print(f"📄 Loaded {len(products)} products from data file")
        return products
        
    except Exception as e:
        print(f"❌ Error loading products from CSV: {e}")
        return []

def seed_all_products(container, products):
    """Seed all products into the container"""
    success_count = 0
    error_count = 0
    
    print(f"🌱 Seeding {len(products)} products...")
    
    for product in products:
        try:
            # Add Cosmos DB required fields
            product_doc = {
                "id": str(uuid.uuid4()),
                "partitionKey": product["ProductID"],
                **product
            }
            
            # Insert the document
            container.create_item(body=product_doc)
            print(f"✅ Inserted: {product['ProductName']} ({product['ProductID']})")
            success_count += 1
            
        except CosmosResourceExistsError:
            print(f"⚠️  Product already exists: {product['ProductName']} ({product['ProductID']})")
        except Exception as e:
            print(f"❌ Error inserting {product['ProductName']}: {e}")
            error_count += 1
    
    print(f"\n📊 Seeding Summary:")
    print(f"✅ Successfully inserted: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📝 Total products: {len(products)}")
    
    return success_count, error_count

def main():
    print("🚀 Starting Complete Product Data Refresh...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Container: {CONTAINER_NAME}")
    
    # Create Cosmos client
    client = create_cosmos_client()
    if not client:
        print("❌ Failed to create Cosmos client. Please check your connection string.")
        return
    
    # Get database and container
    database, container = get_database_and_container(client)
    if not container:
        print("❌ Failed to get database/container. Please check your configuration.")
        return
    
    # Load products from CSV
    products = load_products_from_csv()
    if not products:
        print("❌ Failed to load products from data file.")
        return
    
    # Clear existing products
    if not clear_all_products(container):
        print("❌ Failed to clear existing products.")
        return
    
    # Seed all products
    success_count, error_count = seed_all_products(container, products)
    
    if success_count > 0:
        print(f"\n🎉 Product refresh completed successfully!")
        print(f"📊 Final Results:")
        print(f"   ✅ Products inserted: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📝 Total processed: {len(products)}")
    else:
        print("\n❌ No products were successfully inserted.")

if __name__ == "__main__":
    main()
