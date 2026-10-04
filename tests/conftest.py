"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator

import pytest
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.db.documents import ALL_DOCUMENTS


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Create a test database for each test function.
    Drops the database after the test completes.
    """
    test_db_name = settings.mongodb_test_db_name
    
    # Create client and connect
    client = AsyncIOMotorClient(settings.mongodb_uri)
    
    # Initialize Beanie with test database
    await init_beanie(
        database=client[test_db_name],
        document_models=ALL_DOCUMENTS,
    )
    
    yield client
    
    # Clean up: drop test database
    await client.drop_database(test_db_name)
    client.close()
