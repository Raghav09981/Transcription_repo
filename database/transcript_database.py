from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from configs.file_configs import MONGO_URL

try:
    client = MongoClient(MONGO_URL)
    client.admin.command("ping")
    print("Connected Successfully")
    db = client["transcript_db"]
    transcript_collection = db["meeting_summary"]

except ConnectionFailure as e:
    print("Failed to connect to database", e)
    client = None
    db = None
    transcript_collection = None
