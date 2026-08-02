from pymongo import MongoClient


def connect_to_mongo(uri: str, db_name: str):
    """Create a PyMongo client and return the client plus the database handle."""
    client = MongoClient(uri)
    db = client[db_name]
    return client, db


def close_mongo_connection(client: MongoClient) -> None:
    """Close the PyMongo client connection cleanly."""
    client.close()
