from pymongo import MongoClient

from app.core.config import MONGODB_URI

client = MongoClient(MONGODB_URI)

db = client["EST_AI_HUMAN_DAON_PROJECT"]