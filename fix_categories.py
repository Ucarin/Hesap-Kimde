import pymongo

# --- MONGODB BAĞLANTISI ---
MONGO_URI = "mongodb+srv://ersinucar:1597538520Ersin%3F@ucar.83bqvaj.mongodb.net/ersinucar?retryWrites=true&w=majority&appName=Ucar"
client = pymongo.MongoClient(MONGO_URI)
db = client["ersinucar"]
collection = db["snacks"]

# --- DÜZELTME KURALLARI ---
# Ürün isminin içinde bu kelimeler geçiyorsa kategoriyi güncelle
rules = {
    "Gofret": ["gofret", "didido", "hoşbeş"],
    "Bisküvi & Kraker": ["bisküvi", "kurabiye", "kraker", "çubuk", "hanımeller", "halley", "negro", "petibör"],
    "Kek": ["kek", "dankek", "popkek", "topkek", "turti"],
    "Cips": ["cips", "chips", "lays", "doritos", "ruffles", "patos", "çerezza"],
    "Kuruyemiş": ["fıstık", "fındık", "badem", "ceviz", "leblebi", "kaju", "çekirdek"],
    "Şekerleme": ["şeker", "jelibon", "bonibon", "sakız", "yumuşak şeker", "olips"],
    "Sağlıklı": ["protein", "fit", "yulaf", "chia", "glutensiz", "diyet"],
    "Çikolata": ["çikolata", "bitter", "sütlü", "tadelle", "metro", "albeni", "snickers"]
}

def fix_it():
    print("Kategori düzeltme işlemi başlıyor...")
    updated_total = 0

    # Veritabanındaki tüm ürünleri çek
    all_products = collection.find({})

    for product in all_products:
        name_lower = product["name"].lower()
        new_category = None

        # Kuralları kontrol et
        for cat_name, keywords in rules.items():
            if any(key in name_lower for key in keywords):
                new_category = cat_name
                break
        
        # Eğer bir eşleşme bulduysak ve eski kategorisinden farklıysa güncelle
        if new_category and product.get("category") != new_category:
            collection.update_one(
                {"_id": product["_id"]},
                {"$set": {"category": new_category}}
            )
            updated_total += 1
            print(f"Güncellendi: {product['name']} -> {new_category}")

    print(f"\nİşlem Tamamlandı! Toplam {updated_total} ürünün kategorisi düzeltildi. ✅")

if __name__ == "__main__":
    fix_it()