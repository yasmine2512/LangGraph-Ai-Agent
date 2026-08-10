import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "automated_agent")

if not MONGODB_URI:
    raise ValueError("MONGODB_URI is not defined in .env")

client = MongoClient(MONGODB_URI)

db = client[MONGODB_DATABASE]


def test_connection():
    try:
        client.admin.command("ping")
        print("MongoDB connected successfully!")
    except Exception as e:
        print("MongoDB connection failed:", e)