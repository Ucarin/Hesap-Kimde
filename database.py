import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "snack_roulette")

client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Collections
history_collection = db["payment_history"]
snacks_collection = db["snacks"]

async def get_history():
    history = []
    cursor = history_collection.find().sort("date", -1) # Son eklenenler en üstte
    async for doc in cursor:
        doc["_id"] = str(doc["_id"]) # ObjectId'yi stringe çevir
        history.append(doc)
    return history

async def add_history_record(record):
    await history_collection.insert_one(record)

async def clear_history():
    await history_collection.delete_many({})

async def get_snacks():
    snacks = []
    cursor = snacks_collection.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        snacks.append(doc)
    return snacks

async def bulk_add_snacks(snacks_list):
    if snacks_list:
        await snacks_collection.delete_many({}) # Temizle ve yeniden yükle
        await snacks_collection.insert_many(snacks_list)
