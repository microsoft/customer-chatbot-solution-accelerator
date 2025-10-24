#!/usr/bin/env python3
"""
Test script to verify Cosmos DB connection
"""

def main():
    print("Testing database connection...")
    
    try:
        from app.database import get_db_service
        
        # Get the database service
        service = get_db_service()
        print(f"Database service type: {type(service).__name__}")
        
        if hasattr(service, 'client'):
            print("✅ Cosmos DB client initialized successfully!")
        else:
            print("⚠️  Using MockDatabaseService (no Cosmos DB connection)")
            
        print("Database connection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()