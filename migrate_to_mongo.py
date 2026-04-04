import json
import asyncio
import os
from database import bulk_add_snacks, add_history_record, history_collection

async def migrate():
    print("Migrasyon basliyor...")
    
    # 1. Atistirmaliklar (Snacks)
    if os.path.exists("market_data.json"):
        with open("market_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            snacks = data.get("snacks", [])
            if snacks:
                # _id'leri temizle (ObjectId cakismasi olmasin diye)
                for s in snacks:
                    if "_id" in s: del s["_id"]
                await bulk_add_snacks(snacks)
                print(f"{len(snacks)} atistirmalik MongoDB'ye yuklendi.")
    
    # 2. Odeme Gecmisi (History)
    if os.path.exists("payment_history.json"):
        with open("payment_history.json", "r", encoding="utf-8") as f:
            history = json.load(f)
            if history:
                # Mevcut kayitlari temizle ve yeniden ekle (basitlik icin)
                await history_collection.delete_many({})
                for h in history:
                    if "_id" in h: del h["_id"]
                    await add_history_record(h)
                print(f"{len(history)} gecmis kaydi MongoDB'ye yuklendi.")
                
    print("Migrasyon tamamlandi! OK")

if __name__ == "__main__":
    asyncio.run(migrate())
