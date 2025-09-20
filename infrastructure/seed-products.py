#!/usr/bin/env python3
"""
Product Data Seeding Script for Cosmos DB
This script seeds the products container with paint product data
"""

import os
import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError

# Cosmos DB configuration
COSMOS_ENDPOINT = "https://ecommerce-chat-dev-cosmos.documents.azure.com:443/"
DATABASE_NAME = "ecommerce-db"
CONTAINER_NAME = "products"

# Product data
PRODUCTS_DATA = [
    {
        "ProductID": "PROD0001",
        "ProductName": "Pale Meadow",
        "ProductCategory": "Paint Shades",
        "Price": 29.99,
        "ProductDescription": "A soft, earthy green reminiscent of open meadows at dawn.",
        "ProductPunchLine": "Nature's touch inside your home",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/PaleMeadow.png"
    },
    {
        "ProductID": "PROD0002",
        "ProductName": "Tranquil Lavender",
        "ProductCategory": "Paint Shades",
        "Price": 31.99,
        "ProductDescription": "A muted lavender that soothes and reassures, ideal for relaxation.",
        "ProductPunchLine": "Find your peaceful moment",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/TranquilLavender.png"
    },
    {
        "ProductID": "PROD0003",
        "ProductName": "Whispering Blue",
        "ProductCategory": "Paint Shades",
        "Price": 47.99,
        "ProductDescription": "Light, breezy blue that lifts spirits and refreshes the space.",
        "ProductPunchLine": "Float away on blue skies",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlue.png"
    },
    {
        "ProductID": "PROD0004",
        "ProductName": "Whispering Blush",
        "ProductCategory": "Paint Shades",
        "Price": 50.82,
        "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.",
        "ProductPunchLine": "Add a blush of beauty",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"
    },
    {
        "ProductID": "PROD0005",
        "ProductName": "Ocean Mist",
        "ProductCategory": "Paint Shades",
        "Price": 84.83,
        "ProductDescription": "Premium quality ocean mist paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Ocean Mist!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Ocean Mist_Paint.png"
    },
    {
        "ProductID": "PROD0006",
        "ProductName": "Sunset Coral",
        "ProductCategory": "Paint Shades",
        "Price": 48.57,
        "ProductDescription": "Premium quality sunset coral paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Sunset Coral!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sunset Coral Paint.png"
    },
    {
        "ProductID": "PROD0007",
        "ProductName": "Forest Whisper",
        "ProductCategory": "Paint Shades",
        "Price": 43.09,
        "ProductDescription": "Premium quality forest whisper paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Forest Whisper!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Forest Whisper Paint.png"
    },
    {
        "ProductID": "PROD0008",
        "ProductName": "Morning Dew",
        "ProductCategory": "Paint Shades",
        "Price": 81.94,
        "ProductDescription": "Premium quality morning dew paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Morning Dew!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Morning Dew Paint.png"
    },
    {
        "ProductID": "PROD0009",
        "ProductName": "Dusty Rose",
        "ProductCategory": "Paint Shades",
        "Price": 75.62,
        "ProductDescription": "Premium quality dusty rose paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Dusty Rose!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Dusty Rose Paint.png"
    },
    {
        "ProductID": "PROD0010",
        "ProductName": "Sage Harmony",
        "ProductCategory": "Paint Shades",
        "Price": 33.26,
        "ProductDescription": "Premium quality sage harmony paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.",
        "ProductPunchLine": "Transform Your Space with Sage Harmony!",
        "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Sage Harmony.png"
    }
]

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

def seed_products(container):
    """Seed products into the container"""
    success_count = 0
    error_count = 0
    
    for product in PRODUCTS_DATA:
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
    print(f"📝 Total products: {len(PRODUCTS_DATA)}")

def main():
    print("🌱 Starting product data seeding...")
    print(f"Database: {DATABASE_NAME}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Products to seed: {len(PRODUCTS_DATA)}")
    
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
    
    # Seed products
    seed_products(container)
    
    print("\n🎉 Product seeding completed!")

if __name__ == "__main__":
    main()
