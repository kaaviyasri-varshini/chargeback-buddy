"""MongoDB connection management with Beanie ODM."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ServerSelectionTimeoutError

from app.config import settings
from app.db.documents import ALL_DOCUMENTS

logger = logging.getLogger(__name__)

# Global client instance
_client: AsyncIOMotorClient | None = None
_change_streams_available: bool = False


async def init_db(db_name: str | None = None) -> None:
    """
    Initialize MongoDB connection and Beanie ODM.
    
    Args:
        db_name: Optional database name override (for testing)
    """
    global _client, _change_streams_available
    
    database_name = db_name or settings.mongodb_db_name
    
    try:
        logger.info(f"Connecting to MongoDB: {settings.mongodb_uri}")
        _client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        
        # Test connection
        await _client.admin.command('ping')
        logger.info("MongoDB connection successful")
        
        # Check if change streams are available (requires replica set)
        try:
            db = _client[database_name]
            # Try to check replica set status
            status = await _client.admin.command('replSetGetStatus')
            _change_streams_available = True
            logger.info("MongoDB change streams available (replica set detected)")
        except Exception:
            _change_streams_available = False
            logger.warning(
                "MongoDB change streams NOT available (not a replica set). "
                "Live updates will use polling. Run 'docker compose up' for local dev."
            )
        
        # Initialize Beanie with document models
        await init_beanie(
            database=_client[database_name],
            document_models=ALL_DOCUMENTS,
        )
        logger.info(f"Beanie initialized with database: {database_name}")
        
    except ServerSelectionTimeoutError:
        logger.error(
            f"Could not connect to MongoDB at {settings.mongodb_uri}. "
            "Make sure MongoDB is running (docker compose up) or check MONGODB_URI."
        )
        raise
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db() -> None:
    """Close MongoDB connection."""
    global _client
    
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")
        _client = None


def get_client() -> AsyncIOMotorClient:
    """Get the MongoDB client instance."""
    if _client is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _client


def change_streams_available() -> bool:
    """Check if MongoDB change streams are available."""
    return _change_streams_available


@asynccontextmanager
async def lifespan_context() -> AsyncGenerator[None, None]:
    """
    Async context manager for application lifespan.
    Use with FastAPI/NiceGUI lifespan parameter.
    """
    await init_db()
    try:
        yield
    finally:
        await close_db()
