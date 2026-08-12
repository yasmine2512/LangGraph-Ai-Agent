import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "automated_agent")

_client = None

_db = None


def connect_db():
    global _client, _db

    if _client is None:
        _client = MongoClient(MONGODB_URI)

        _client.admin.command("ping")

        _db = _client[MONGODB_DATABASE]

        print("MongoDB connected")

    return _db


def get_db():
    if _db is None:
        raise RuntimeError("Database is not initialized")

    return _db

def get_client():
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")

    return _client


def close_db():
    global _client, _db

    if _client:
        _client.close()
        _client = None
        _db = None

        print("MongoDB connection closed")
        
