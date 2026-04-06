import time
import json
import pymongo
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- MONGODB YAPILANDIRMASI ---
MONGO_URI = "mongodb+srv://ersinucar:1597538520Ersin%3F@ucar.83bqvaj.mongodb.net/ersinucar?retryWrites=true&w=majority&appName=Ucar"
DB_NAME = "ersinucar"
COLLECTION_NAME = "snacks"

# --- KATEGORİLER (TÜM LİSTE) ---
CATEGORIES = [
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/cikolata", "category": "Çikolata"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/gofret", "category": "Gofret"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/biskuvi-kraker", "category": "Bisküvi & Kraker"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/kek", "category": "Kek"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/cips", "category": "Cips"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/kuruyemis-kuru-meyve", "category": "Kuruyemiş"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/sakiz-sekerleme", "category": "Şekerleme & Sakız"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/saglikli-atistirmaliklar", "category": "Sağlıklı"},
]

def save_to_mongodb(products):
    if not products: return
    print(f"\n{len(products)} ürün MongoDB'ye aktarılıyor...")
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION_NAME]
    for p in products:
        # Upsert: Ürün ismi ve markete göre güncelleme
        col.update_one({"name": p["name"], "market": "A101"}, {"$set": p}, upsert=True)
    print("Veritabanı Başarıyla Güncellendi! ✅")

def scrape_a101():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    # Chrome 146 sürümün için use_subprocess ve version_main kritik
    driver = uc.Chrome(options=options, version_main=146, use_subprocess=True)

    all_products = []
    seen_names = set()

    for cat in CATEGORIES:
        print(f"\n[{cat['category']}] Sayfası taranıyor...")
        driver.get(cat['url'])
        time.sleep(12) # Sayfanın oturması için

        # Sayfayı yavaşça sona kadar indir (Lazy Load Tetikleyici)
        last_h = driver.execute_script("return document.body.scrollHeight")
        for i in range(1, 9):
            driver.execute_script(f"window.scrollTo(0, {last_h} * {i/8});")
            time.sleep(2)

        # Kartları bul (A101'in tüm olası kutu yapıları)
        cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer, li.set-product-item, div[class*='ProductCard']")
        print(f"  > {len(cards)} potansiyel kutu bulundu.")

        cat_count = 0
        for card in cards:
            try:
                card_text = card.text.strip()
                if not card_text or "₺" not in card_text: continue

                # İSİM BULMA: Karttaki en uzun metin genelde ürün ismidir
                lines = card_text.split('\n')
                name = max(lines, key=len).strip()
                
                if len(name) < 5 or name in seen_names: continue

                # FİYAT BULMA: ₺ içeren ilk satırı al
                price_text = ""
                for line in lines:
                    if "₺" in line:
                        price_text = line.strip()
                        break
                
                if not price_text: continue

                # RESİM BULMA
                img_url = ""
                try:
                    img_el = card.find_element(By.TAG_NAME, "img")
                    img_url = img_el.get_attribute("src") or img_el.get_attribute("data-src")
                except: pass

                all_products.append({
                    "name": name,
                    "price": price_text, # "35,50 ₺" şeklinde kaydedecek
                    "display_price": f"Ort. {price_text}", # Sitede böyle gösterebilirsin
                    "image": img_url,
                    "category": cat['category'],
                    "market": "A101",
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                seen_names.add(name)
                cat_count += 1
            except: continue
        
        print(f"  > {cat['category']} bitti: {cat_count} ürün yakalandı.")

    driver.quit()
    save_to_mongodb(all_products)

if __name__ == "__main__":
    scrape_a101()