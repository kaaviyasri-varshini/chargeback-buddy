#!/usr/bin/env python
"""Quick test to check MongoDB connectivity."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

async def test_connection():
    """Test MongoDB connection."""
    try:
        print(f"🔍 Attempting to connect to: {settings.mongodb_uri}")
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # List databases
        db_list = await client.list_database_names()
        print(f"📊 Available databases: {db_list}")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Solutions:")
        print("   1. Start Docker Desktop: open -a Docker && docker compose up -d")
        print("   2. Use MongoDB Atlas (free): https://cloud.mongodb.com")
        print("   3. Install locally: brew install mongodb-community@7.0")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection())
