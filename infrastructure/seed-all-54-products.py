#!/usr/bin/env python3
"""
Seed All 54 Products Script for Cosmos DB
This script clears existing products and seeds all 54 products directly
"""

import os
import json
import uuid
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceExistsError, CosmosResourceNotFoundError

# Cosmos DB configuration
COSMOS_ENDPOINT = "https://ecommerce-chat-dev-cosmos.documents.azure.com:443/"
DATABASE_NAME = "ecommerce-db"
CONTAINER_NAME = "products"

# All 54 products data
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
    {"ProductID": "PROD0011", "ProductName": "Vanilla Dream", "ProductCategory": "Paint Shades", "Price": 54.66, "ProductDescription": "Premium quality vanilla dream paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Vanilla Dream!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Vanilla Dream.png"},
    {"ProductID": "PROD0012", "ProductName": "Charcoal Storm", "ProductCategory": "Paint Shades", "Price": 43.45, "ProductDescription": "Premium quality charcoal storm paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Charcoal Storm!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Charcoal Storm.png"},
    {"ProductID": "PROD0013", "ProductName": "Golden Wheat", "ProductCategory": "Paint Shades", "Price": 109.73, "ProductDescription": "Premium quality golden wheat paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Golden Wheat!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Golden Wheat.png"},
    {"ProductID": "PROD0014", "ProductName": "Soft Pebble", "ProductCategory": "Paint Shades", "Price": 110.92, "ProductDescription": "Premium quality soft pebble paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Soft Pebble!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Soft Pebble.png"},
    {"ProductID": "PROD0015", "ProductName": "Misty Gray", "ProductCategory": "Paint Shades", "Price": 96.04, "ProductDescription": "Premium quality misty gray paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Misty Gray!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Misty Gray.png"},
    {"ProductID": "PROD0016", "ProductName": "Rustic Clay", "ProductCategory": "Paint Shades", "Price": 83.37, "ProductDescription": "Premium quality rustic clay paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Rustic Clay!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Rustic Clay.png"},
    {"ProductID": "PROD0017", "ProductName": "Ivory Pearl", "ProductCategory": "Paint Shades", "Price": 91.99, "ProductDescription": "Premium quality ivory pearl paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Ivory Pearl!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Ivory Pearl.png"},
    {"ProductID": "PROD0018", "ProductName": "Deep Forest", "ProductCategory": "Paint Shades", "Price": 119.93, "ProductDescription": "Premium quality deep forest paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Deep Forest!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Deep Forest.png"},
    {"ProductID": "PROD0019", "ProductName": "Autumn Spice", "ProductCategory": "Paint Shades", "Price": 30.34, "ProductDescription": "Premium quality autumn spice paint with excellent coverage and durability. Perfect for interior and exterior surfaces with long-lasting color retention.", "ProductPunchLine": "Transform Your Space with Autumn Spice!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Autumn Spice.png"},
    {"ProductID": "PROD0020", "ProductName": "Coastal Whisper", "ProductCategory": "Paint Shades", "Price": 39.99, "ProductDescription": "An airy, tranquil blue that evokes relaxing days by the ocean.", "ProductPunchLine": "Let the calm of the coast breeze in", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/CoastalWhisper.png"},
    {"ProductID": "PROD0021", "ProductName": "Effervescent Jade", "ProductCategory": "Paint Shades", "Price": 42.99, "ProductDescription": "A sparkling, uplifting jade green for spaces brimming with vitality.", "ProductPunchLine": "Energize your room, refresh your mind", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/EffervescentJade.png"},
    {"ProductID": "PROD0022", "ProductName": "Frosted Blue", "ProductCategory": "Paint Shades", "Price": 36.99, "ProductDescription": "A crisp, subtle blue perfect for creating peaceful retreats.", "ProductPunchLine": "Chill out in classic blue", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/FrestedBlue.png"},
    {"ProductID": "PROD0023", "ProductName": "Frosted Lemon", "ProductCategory": "Paint Shades", "Price": 28.99, "ProductDescription": "A zesty, pale yellow that uplifts and brightens every corner.", "ProductPunchLine": "Awaken spaces with a citrus twist", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/FrostedLemon.png"},
    {"ProductID": "PROD0024", "ProductName": "Honeydew Sunrise", "ProductCategory": "Paint Shades", "Price": 45.99, "ProductDescription": "A velvety, refreshing green for rejuvenated and cozy spaces.", "ProductPunchLine": "Freshen up with a gentle green glow", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/HoneydewSunrise.png"},
    {"ProductID": "PROD0025", "ProductName": "Lavender Whisper", "ProductCategory": "Paint Shade", "Price": 33.99, "ProductDescription": "Soft lavender hues for a restful, dreamy ambiance.", "ProductPunchLine": "A delicate fragrance of color", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/LavenderWhisper.png"},
    {"ProductID": "PROD0026", "ProductName": "Lilac Mist", "ProductCategory": "Paint Shade", "Price": 55.99, "ProductDescription": "A gentle purple mist that brings elegance and calm.", "ProductPunchLine": "Wrap your walls in a purple haze", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/LilacMist.png"},
    {"ProductID": "PROD0027", "ProductName": "Soft Creamsicle", "ProductCategory": "Paint Shade", "Price": 41.99, "ProductDescription": "A creamy, orange-tinted shade for gentle warmth and cheer.", "ProductPunchLine": "Sweeten your space with a smile", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/SoftCreamsicle.png"},
    {"ProductID": "PROD0028", "ProductName": "Whispering Blush", "ProductCategory": "Paint Shade", "Price": 26.99, "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.", "ProductPunchLine": "Add a blush of beauty", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"},
    {"ProductID": "PROD0029", "ProductName": "Lavender Whisper", "ProductCategory": "Paint Shade", "Price": 33.99, "ProductDescription": "Soft lavender hues for a restful, dreamy ambiance.", "ProductPunchLine": "A delicate fragrance of color", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/LavenderWhisper.png"},
    {"ProductID": "PROD0030", "ProductName": "Lilac Mist", "ProductCategory": "Paint Shade", "Price": 55.99, "ProductDescription": "A gentle purple mist that brings elegance and calm.", "ProductPunchLine": "Wrap your walls in a purple haze", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/LilacMist.png"},
    {"ProductID": "PROD0031", "ProductName": "Soft Creamsicle", "ProductCategory": "Paint Shade", "Price": 41.99, "ProductDescription": "A creamy, orange-tinted shade for gentle warmth and cheer.", "ProductPunchLine": "Sweeten your space with a smile", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/SoftCreamsicle.png"},
    {"ProductID": "PROD0032", "ProductName": "Whispering Blush", "ProductCategory": "Paint Shade", "Price": 26.99, "ProductDescription": "A subtle, enchanting pink for warmth and understated elegance.", "ProductPunchLine": "Add a blush of beauty", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/WhisperingBlush.png"},
    {"ProductID": "PROD0033", "ProductName": "Cordless Airless Pro", "ProductCategory": "Paint Sprayer", "Price": 120.99, "ProductDescription": "Go cordless and conquer any project with this ultra-portable airless paint sprayer. Delivers smooth, even coverage on walls, decks, and fences—anywhere freedom is needed.", "ProductPunchLine": "Spray without limits, anywhere you go!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/CordlessAirlessPaintSprayer.png"},
    {"ProductID": "PROD0034", "ProductName": "Cordless Compact Painter", "ProductCategory": "Paint Sprayer", "Price": 149.99, "ProductDescription": "Perfect for precision DIYers—this compact, cordless paint sprayer is ideal for touch-ups, furniture, and tight corners. Lightweight, portable, and powerful.", "ProductPunchLine": "Precision in the palm of your hand", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/CordlessPaintSprayerCompact.png"},
    {"ProductID": "PROD0035", "ProductName": "Electric Sprayer 350", "ProductCategory": "Paint Sprayer", "Price": 135.99, "ProductDescription": "A dependable electric paint sprayer offering 350W of steady power for smooth, consistent finishes. Ideal for home interiors, cabinetry, and more.", "ProductPunchLine": "Power up your paint game!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/ElectricPaintSprayer350.png"},
    {"ProductID": "PROD0036", "ProductName": "HVLP SuperFinish", "ProductCategory": "Paint Sprayer", "Price": 125.99, "ProductDescription": "A high-volume, low-pressure paint sprayer for a professional, glass-smooth finish on cabinets, crafts, and trim. Super controllable with minimal overspray.", "ProductPunchLine": "Smooth as silk, pro-grade results", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/HVLPPaintSprayerSuperFinish.png"},
    {"ProductID": "PROD0037", "ProductName": "Handheld Airless 360", "ProductCategory": "Paint Sprayer", "Price": 130.99, "ProductDescription": "Advanced handheld airless sprayer with 360-degree usability for walls, ceilings, furniture, and more. Perfect for quick projects and detailed work.", "ProductPunchLine": "Complete flexibility, flawless finish", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/HandheldAirlessSprayer360.png"},
    {"ProductID": "PROD0038", "ProductName": "Handheld HVLP Pro", "ProductCategory": "Paint Sprayer", "Price": 139.99, "ProductDescription": "A user-friendly, handheld HVLP paint sprayer designed for crafts, small to mid-sized furniture, and décor. Get precise results with little mess.", "ProductPunchLine": "Create, decorate, and elevate", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/HandheldHVLPPaintSprayer.png"},
    {"ProductID": "PROD0039", "ProductName": "Paint Safe Drop Cloth", "ProductCategory": "Paint Accessories", "Price": 55.99, "ProductDescription": "Heavy-duty, reusable drop cloth designed to protect floors and furniture during painting, staining, or remodeling projects. Ideal for both professional painters and DIY enthusiasts seeking reliable surface coverage.", "ProductPunchLine": "Shield your space, paint with confidence.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/drop_cloth_1.png"},
    {"ProductID": "PROD0040", "ProductName": "Paint Guard Reusable Drop Cloth", "ProductCategory": "Paint Accessories", "Price": 60.99, "ProductDescription": "Protect your floors and furniture from paint spills and splatters with this durable, reusable drop cloth, perfect for both professional painters and DIY home improvement projects.", "ProductPunchLine": "Protect your floors, perfect your paint – drop cloths done right!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/drop_cloth_2.png"},
    {"ProductID": "PROD0041", "ProductName": "Fine Finish Paint Brush", "ProductCategory": "Paint Accessories", "Price": 2.99, "ProductDescription": "Achieve crisp lines and smooth finishes with this precision paint brush, ideal for detailed trim work, cutting in edges, and painting smaller surfaces with ease.", "ProductPunchLine": "Smooth Strokes, Flawless Finish.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Bresh_1.png"},
    {"ProductID": "PROD0042", "ProductName": "All-Purpose Wall Paint Brush", "ProductCategory": "Paint Accessories", "Price": 3.99, "ProductDescription": "Designed for broad coverage and consistent application, this versatile paint brush delivers smooth results on walls, ceilings, and large furniture pieces, making every painting project more efficient.", "ProductPunchLine": "Smooth Strokes, Flawless Finish.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Bresh_2.png"},
    {"ProductID": "PROD0043", "ProductName": "Large Area Applicator Brush", "ProductCategory": "Paint Accessories", "Price": 4.99, "ProductDescription": "Effortlessly cover expansive surfaces with this innovative roller-style brush, offering the broad coverage of a roller with the control of a brush, perfect for applying specialized coatings or achieving unique textured finishes.", "ProductPunchLine": "Smooth Strokes, Flawless Finish.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Bresh_3.png"},
    {"ProductID": "PROD0044", "ProductName": "Classic Flat Sash Brush", "ProductCategory": "Paint Accessories", "Price": 3.99, "ProductDescription": "Featuring a comfortable wooden handle and fine bristles, this versatile flat sash brush provides excellent control and smooth paint application, making it ideal for painting trim, doors, and smaller wall sections.", "ProductPunchLine": "The Brush That Makes Color Come Alive!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Bresh_7.png"},
    {"ProductID": "PROD0045", "ProductName": "Standard Paint Tray", "ProductCategory": "Paint Accessories", "Price": 10.99, "ProductDescription": "This versatile paint tray is ideal for small to medium painting projects, providing a stable base for easy paint loading. Its design ensures efficient paint distribution, making it perfect for quick touch-ups or detailed trim work.", "ProductPunchLine": "Grip it. Dip it. Master your finish with ease.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Tray_1.png"},
    {"ProductID": "PROD0046", "ProductName": "Deep Well Paint Tray", "ProductCategory": "Paint Accessories", "Price": 7.99, "ProductDescription": "This sturdy paint tray features a generous well for holding ample paint, minimizing refills during larger projects. Its ribbed ramp ensures even paint loading, making it ideal for covering broad surfaces like walls and ceilings efficiently.", "ProductPunchLine": "Grip it. Dip it. Master your finish with ease.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Tray_2.png"},
    {"ProductID": "PROD0047", "ProductName": "Compact Paint Tray", "ProductCategory": "Paint Accessories", "Price": 8.99, "ProductDescription": "This clean, white paint tray and roller set is perfect for small-scale painting projects. Its compact size makes it ideal for touch-ups, trim work, or crafts, ensuring easy paint application and minimal waste.", "ProductPunchLine": "Grip it. Dip it. Master your finish with ease.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Tray_3.png"},
    {"ProductID": "PROD0048", "ProductName": "Heavy-Duty Paint Tray with Grid", "ProductCategory": "Paint Accessories", "Price": 135.99, "ProductDescription": "The robust paint tray and roller features a sturdy design, making it suitable for larger painting tasks. The integrated grid ensures even paint loading onto the roller, ideal for smooth, consistent coverage on walls and ceilings.", "ProductPunchLine": "Grip it. Dip it. Master your finish with ease.", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Paint_Tray_4.png"},
    {"ProductID": "PROD0049", "ProductName": "Blue Painter's Tape", "ProductCategory": "Paint Accessories", "Price": 3.99, "ProductDescription": "The Blue painter's tape offers strong adhesion and clean removal, ideal for precise masking in painting projects to achieve crisp lines.", "ProductPunchLine": "Clean Lines, Every Time!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/painters_tape_1.png"},
    {"ProductID": "PROD0050", "ProductName": "Green Painter's Tape", "ProductCategory": "Paint Accessories", "Price": 2.99, "ProductDescription": "The green painter tape is a versatile option known for its excellent conformability, perfect for delicate surfaces and curves in both indoor and outdoor painting applications.", "ProductPunchLine": "Clean Lines, Every Time!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/painters_tape_3.png"},
    {"ProductID": "PROD0051", "ProductName": "Standard Paint Roller", "ProductCategory": "Paint Accessories", "Price": 15.99, "ProductDescription": " This versatile roller offers reliable performance for a wide range of painting tasks, from touch-ups to full room renovations, providing excellent coverage.", "ProductPunchLine": "Roll with Precision, Paint with Power!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Roller_3.png"},
    {"ProductID": "PROD0052", "ProductName": "Ergonomic Grip Paint Roller", "ProductCategory": "Paint Accessories", "Price": 10.99, "ProductDescription": "Designed with a comfortable ergonomic handle, this roller is perfect for extended painting projects, reducing hand fatigue for a more efficient finish.", "ProductPunchLine": "Roll with Precision, Paint with Power!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Roller_2.png"},
    {"ProductID": "PROD0053", "ProductName": "Classic Wood Handle Paint Roller", "ProductCategory": "Paint Accessories", "Price": 9.99, "ProductDescription": "Featuring a timeless wooden handle, this roller is ideal for achieving smooth, even coverage on walls and ceilings in any room.", "ProductPunchLine": "Roll with Precision, Paint with Power!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Roller_1.png"},
    {"ProductID": "PROD0054", "ProductName": "Wooden Handle Paint Roller", "ProductCategory": "Paint Accessories", "Price": 8.99, "ProductDescription": "Featuring a durable wooden handle and a plush roller cover making it ideal for high-quality painting projects.", "ProductPunchLine": "Roll with Precision, Paint with Power!", "ImageURL": "https://staidemodev.blob.core.windows.net/hero-demos-hardcoded-chat-images/Roller_4.png"}
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
    print(f"Products to process: {len(ALL_PRODUCTS)}")
    
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
    
    # Clear existing products
    if not clear_all_products(container):
        print("❌ Failed to clear existing products.")
        return
    
    # Seed all products
    success_count, error_count = seed_all_products(container, ALL_PRODUCTS)
    
    if success_count > 0:
        print(f"\n🎉 Product refresh completed successfully!")
        print(f"📊 Final Results:")
        print(f"   ✅ Products inserted: {success_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📝 Total processed: {len(ALL_PRODUCTS)}")
    else:
        print("\n❌ No products were successfully inserted.")

if __name__ == "__main__":
    main()
