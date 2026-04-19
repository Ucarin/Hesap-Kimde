import json
import pymongo

# Atlas bağlantı linkin
MONGO_URI = "mongodb+srv://hesapkimde_ersinucar:3dTpZkzOUYo5eFL3@hesapkimde.acx5con.mongodb.net/?retryWrites=true&w=majority&appName=hesapkimde"

def migrate_now():
    print("🚀 Veriler Atlas'a fırlatılıyor...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client["hesapkimde"]
    
    # 1. Snacks (Ürünler)
    with open("market_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        # Eğer liste değilse 'snacks' anahtarını bul
        snacks = data if isinstance(data, list) else data.get("snacks", [])
        
        if snacks:
            db.snacks.delete_many({}) # Eski bozuk verileri temizle
            db.snacks.insert_many(snacks)
            print(f"✅ {len(snacks)} ürün tertemiz şekilde yüklendi!")

    print("🎉 İşlem bitti! Artık Atlas ekranında kategorileri görebilirsin.")

if __name__ == "__main__":
    migrate_now()