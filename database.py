import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# Railway/Render gibi platformlarda bu degeri "Variables" kismindan alir.
# Yerelde calisirken ise .env dosyasindan alir.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "snack_roulette")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Collections
history_collection = db["payment_history"]
snacks_collection = db["snacks"]

async def get_history():
    try:
        history = []
        cursor = history_collection.find().sort("date", -1)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(doc)
        print(f"DEBUG: Found {len(history)} history records in MongoDB.")
        return history
    except Exception as e:
        print(f"DATABASE ERROR (get_history): {e}")
        return []

async def get_snacks():
    try:
        snacks = []
        cursor = snacks_collection.find()
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            snacks.append(doc)
        print(f"DEBUG: Found {len(snacks)} snacks in MongoDB Database: {DB_NAME}")
        return snacks
    except Exception as e:
        print(f"DATABASE ERROR (get_snacks): {e}")
        return []

async def add_history_record(record):
    await history_collection.insert_one(record)

async def clear_history():
    await history_collection.delete_many({})

async def bulk_add_snacks(snacks_list):
    if snacks_list:
        await snacks_collection.delete_many({})
        await snacks_collection.insert_many(snacks_list)
