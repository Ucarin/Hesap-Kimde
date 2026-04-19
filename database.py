import os
import datetime
import uuid
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# .env dosyasını yükle


# Railway Variables'tan veya .env'den gelen değerleri al
# NOT: tlsAllowInvalidCertificates eklendi çünkü bazı sunucu ortamlarında SSL kütüphanesi hata verebiliyor
# database.py içindeki DEFAULT_URI kısmını şu şekilde güncelle:

DEFAULT_URI = "mongodb://hesapkimde_ersinucar:3dTpZkzOUYo5eFL3@acx5con-shard-00-00.mongodb.net:27017,acx5con-shard-00-01.mongodb.net:27017,acx5con-shard-00-02.mongodb.net:27017/hesapkimde?replicaSet=atlas-acx5com-shard-0&ssl=true&authSource=admin&retryWrites=true"
MONGODB_URI = DEFAULT_URI
DB_NAME = "hesapkimde"

# MongoDB Bağlantısı (Timeout eklendi: Bağlantı sorunu varsa 5sn içinde hata versin)
print(f"--- DATABASE DIAGNOSTIC: URI Başlatılıyor... (Cluster: acx5com) ---")
try:
    client = AsyncIOMotorClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=10000,
        appName="HesapKimdeServer"
    )
    db = client[DB_NAME]
    print(f"--- DATABASE DIAGNOSTIC: Client oluşturuldu, veritabanı: {DB_NAME} ---")
except Exception as e:
    print(f"--- DATABASE CRITICAL ERROR: Client oluşturulamadı: {e} ---")

# Koleksiyonlar
history_collection = db["payment_history"]
snacks_collection = db["snacks"]
accounts_collection = db["accounts"]

async def check_db_connectivity():
    """Bağlantıyı test eder ve detaylı hata raporu döndürür"""
    try:
        # 1. Ping testi
        print("--- DEBUG: Veritabanı ping testi yapılıyor... ---")
        # SSL hataları için detaylı log
        await client.admin.command('ping')
        
        # 2. Koleksiyon sayımı
        s_count = await snacks_collection.count_documents({})
        a_count = await accounts_collection.count_documents({})
        h_count = await history_collection.count_documents({})
        
        status = {
            "success": True,
            "message": "Bağlantı Başarılı! ✅",
            "counts": {
                "snacks_docs": s_count,
                "accounts": a_count,
                "history": h_count
            }
        }
        print(f"--- DATABASE SUCCESS: {status['message']} | Snacks: {s_count}, Accounts: {a_count} ---")
        return status
    except Exception as e:
        error_msg = str(e)
        detailed_error = f"Hata Türü: {type(e).__name__} | Mesaj: {error_msg}"
        print(f"--- DATABASE DIAGNOSTIC FAIL: {detailed_error} ❌ ---")
        
        advice = ""
        if "timeout" in error_msg.lower():
            advice = "ÖNERİ: IP Whitelist (Atlas) veya Oracle Outbound Port 27017'yi kontrol et!"
        elif "dnspython" in error_msg.lower() or "dns" in error_msg.lower():
            advice = "ÖNERİ: dnspython kütüphanesi kurulu mu? pip install dnspython"
        elif "ssl" in error_msg.lower() or "cert" in error_msg.lower():
            advice = "ÖNERİ: SSL Sertifika hatası. Python certifi paketini güncellemeyi veya OS CA-certificates paketini kontrol etmeyi dene."
        elif "auth" in error_msg.lower():
            advice = "ÖNERİ: Kullanıcı adı veya şifreyi kontrol et!"
            
        print(f"--- {advice} ---")
        return {"success": False, "message": error_msg, "advice": advice}

# --- 1. ÇARK GEÇMİŞİ FONKSİYONLARI ---
async def get_history():
    history = []
    try:
        cursor = history_collection.find().sort("date", -1).limit(50)
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            history.append(doc)
    except Exception as e:
        print(f"HATA (get_history): {e}")
    return history

async def add_history_record(record):
    try:
        if "date" not in record: record["date"] = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        await history_collection.insert_one(record)
    except Exception as e:
        print(f"HATA (add_history_record): {e}")

async def clear_history():
    await history_collection.delete_many({})

# --- 2. ÜRÜN (SNACK) FONKSİYONLARI ---
async def get_snacks():
    all_snacks = []
    try:
        # Atlas'taki yapıya göre tek bi döküman içinde 'snacks' array'i aranıyor
        cursor = snacks_collection.find({"deleted": {"$ne": True}})
        async for doc in cursor:
            if "snacks" in doc and isinstance(doc["snacks"], list):
                for item in doc["snacks"]:
                    item["_id"] = str(item.get("_id", uuid.uuid4()))
                    all_snacks.append(item)
            elif "name" in doc:
                doc["_id"] = str(doc.get("_id", ""))
                all_snacks.append(doc)
    except Exception as e:
        print(f"--- DATABASE ERROR (get_snacks): {e} ---")
    return all_snacks

# --- 3. KULLANICI HESAP VE PANEL FONKSİYONLARI ---
async def get_account(username):
    try:
        return await accounts_collection.find_one({"username": username})
    except Exception as e:
        print(f"--- AUTH ERROR (get_account): {e} ---")
        return None

async def create_account(username, hashed_password):
    try:
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
    except Exception as e:
        print(f"--- AUTH ERROR (create_account): {e} ---")
        return False

async def update_account_stats(username, amount=0.0, is_loss=False):
    try:
        update_query = {"$inc": {"total_spent": amount}}
        if is_loss:
            update_query["$inc"]["losses"] = 1
        else:
            update_query["$inc"]["wins"] = 1
        await accounts_collection.update_one({"username": username}, update_query)
    except Exception as e:
        print(f"--- STATS ERROR: {e} ---")