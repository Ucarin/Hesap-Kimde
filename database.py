import os
import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# .env dosyasını yükle (Yerel çalışma için)
load_dotenv()

# Railway Variables'tan gelen değerleri al, yoksa varsayılanları kullan
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "ersinucar")

# MongoDB Bağlantısı
client = AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]

# Koleksiyon Tanımlamaları
history_collection = db["payment_history"]
snacks_collection = db["snacks"]
accounts_collection = db["accounts"]

# --- 1. ÇARK GEÇMİŞİ FONKSİYONLARI ---
async def get_history():
    """Tüm çark çevirme geçmişini getirir (Son eklenen en üstte)"""
    history = []
    try:
        cursor = history_collection.find().sort("date", -1)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(doc)
    except Exception as e:
        print(f"HATA (get_history): {e}")
    return history

async def add_history_record(record):
    """Yeni bir çark sonucunu veritabanına kaydeder"""
    await history_collection.insert_one(record)

async def clear_history():
    """Tüm geçmişi temizler"""
    await history_collection.delete_many({})

# --- 2. ÜRÜN (SNACK) FONKSİYONLARI ---
async def get_snacks():
    """Market ürünlerini listeler"""
    snacks = []
    cursor = snacks_collection.find()
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        snacks.append(doc)
    return snacks

# --- 3. KULLANICI HESAP VE PANEL FONKSİYONLARI ---
async def get_account(username):
    """Kullanıcı adı ile hesap bilgilerini çeker"""
    return await accounts_collection.find_one({"username": username})

async def create_account(username, hashed_password):
    """Yeni bir kullanıcı hesabı oluşturur"""
    user_doc = {
        "username": username,
        "password": hashed_password,
        "total_spent": 0.0,
        "wins": 0,
        "losses": 0,
        "created_at": datetime.datetime.now()
    }
    result = await accounts_collection.insert_one(user_doc)
    return result.acknowledged

async def update_account_stats(username, amount=0.0, is_loss=False):
    """Kullanıcının harcama, galibiyet ve mağlubiyet sayılarını günceller"""
    update_query = {"$inc": {"total_spent": amount}}
    if is_loss:
        update_query["$inc"]["losses"] = 1
    else:
        update_query["$inc"]["wins"] = 1
    
    await accounts_collection.update_one({"username": username}, update_query)