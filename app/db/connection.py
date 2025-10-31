from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
from app.core.config import settings


class Database:
    client: Optional[AsyncIOMotorClient] = None
    db = None


db_instance = Database()


async def connect_to_mongo():
    """Connect to MongoDB"""
    db_instance.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db_instance.db = db_instance.client[settings.DATABASE_NAME]
    print(f"✅ Connected to MongoDB database: {settings.DATABASE_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db_instance.client:
        db_instance.client.close()
        print("❌ Closed MongoDB connection")


def get_database():
    """Get database instance"""
    return db_instance.db
