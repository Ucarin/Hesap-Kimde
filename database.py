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
accounts_collection = db["accounts"]

# --- Account Operations --- #

async def get_account(username):
    try:
        return await accounts_collection.find_one({"username": username})
    except Exception as e:
        print(f"DATABASE ERROR (get_account): {e}")
        return None

async def create_account(username, password_hash):
    try:
        new_user = {
            "username": username,
            "password": password_hash,
            "total_spent": 0.0,
            "wins": 0,
            "losses": 0,
            "created_at": os.getenv("CURRENT_TIME", "2026-04-04T18:44:11Z")
        }
        await accounts_collection.insert_one(new_user)
        return True
    except Exception as e:
        print(f"DATABASE ERROR (create_account): {e}")
        return False

async def update_account_stats(username, amount=0.0, is_loss=True):
    try:
        update_query = {"$inc": {"total_spent": amount}}
        if is_loss:
            update_query["$inc"]["losses"] = 1
        else:
            update_query["$inc"]["wins"] = 1
            
        await accounts_collection.update_one({"username": username}, update_query)
        return True
    except Exception as e:
        print(f"DATABASE ERROR (update_account_stats): {e}")
        return False

# --- Other Operations --- #
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
