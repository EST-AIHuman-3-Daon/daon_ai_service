from pymongo import MongoClient

from app.core.config import MONGODB_URI

client = MongoClient(
    MONGODB_URI,
    serverSelectionTimeoutMS=3000,
)

db = client["main_db"]
