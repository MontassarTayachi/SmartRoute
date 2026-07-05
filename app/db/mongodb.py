from motor.motor_asyncio import AsyncIOMotorClient


def connect_to_mongo(uri: str, db_name: str):
    """Create a Motor client and return the client plus the database handle."""
    client = AsyncIOMotorClient(uri)
    db = client[db_name]
    return client, db


async def close_mongo_connection(client: AsyncIOMotorClient):
    """Close the Motor client connection cleanly."""
    client.close()
