import time
import json
import re
import pymongo
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- KONFİGÜRASYON ---
MONGO_URI = "mongodb+srv://ersinucar:1597538520Ersin%3F@ucar.83bqvaj.mongodb.net/ersinucar?retryWrites=true&w=majority&appName=Ucar"
DB_NAME = "ersinucar"
COLLECTION_NAME = "snacks"
PRICE_LIMIT = 40.0

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

# --- YARDIMCI FONKSİYONLAR ---
def parse_price(price_str):
    try:
        clean = price_str.replace("TL", "").replace("₺", "").replace(" ", "").replace("\xa0", "").replace(",", ".").strip()
        return float(clean)
    except:
        return 999.0

def pick_product_image_url(card):
    try:
        img = card.find_element(By.TAG_NAME, "img")
        url = img.get_attribute("src") or img.get_attribute("data-src")
        return url if url and url.startswith("http") else ""
    except:
        return ""

# --- MONGODB BAĞLANTI TESTİ ---
print("MongoDB'ye bağlanılıyor...")
try:
    client = pymongo.MongoClient(MONGO_URI)
    db = client[DB_NAME]
    collection = db[COLLECTION_NAME]
    client.admin.command('ping')
    print("Bağlantı Başarılı! ✅")
except Exception as e:
    print(f"Bağlantı HATASI: {e} ❌")
    exit()

def save_to_mongodb(products):
    if not products:
        print("Kaydedilecek ürün bulunamadı! ❌")
        return
    
    print(f"\n{len(products)} ürün veritabanına işleniyor...")
    count = 0
    for product in products:
        # Upsert: Aynı isim ve markette ürün varsa güncelle, yoksa ekle
        collection.update_one(
            {"name": product["name"], "market": product["market"]},
            {"$set": product},
            upsert=True
        )
        count += 1
    print(f"Başarıyla {count} ürün güncellendi/eklendi. ✅")

# --- ANA SCRAPER ---
def scrape_a101():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("Tarayıcı başlatılıyor...")
    driver = uc.Chrome(options=options)

    all_products = []
    seen_products = set()

    for cat_info in CATEGORIES:
        url = cat_info["url"]
        category_name = cat_info["category"]
        cat_count = 0

        print(f"\n[{category_name}] Sayfası açılıyor...")
        driver.get(url)
        time.sleep(10) # Sayfanın tam yüklenmesi için

        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Yavaş yavaş kaydır (Lazy load tetiklemesi)
            for i in range(1, 4):
                driver.execute_script(f"window.scrollTo(0, {last_height} * {i/3});")
                time.sleep(1.5)

            cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer, li.set-product-item")
            
            for card in cards:
                try:
                    name_els = card.find_elements(By.TAG_NAME, "h3")
                    if not name_els: continue
                    name = name_els[0].text.strip()
                    
                    if not name or name in seen_products:
                        continue

                    price_text = ""
                    price_els = card.find_elements(By.CSS_SELECTOR, "[class*='font-medium'], .price")
                    for p in price_els:
                        if "₺" in p.text:
                            price_text = p.text.strip()
                            break

                    if not price_text: continue
                    
                    price_val = parse_price(price_text)
                    if price_val > PRICE_LIMIT: continue

                    img_url = pick_product_image_url(card)

                    product_data = {
                        "name": name,
                        "price": price_text,
                        "image": img_url,
                        "category": category_name,
                        "market": "A101"
                    }

                    seen_products.add(name)
                    all_products.append(product_data)
                    cat_count += 1
                except:
                    continue

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(3)
                if driver.execute_script("return document.body.scrollHeight") == last_height:
                    break 
            last_height = new_height
            print(f"  > Bulunan: {cat_count}", end="\r")

        print(f"\n  [{category_name}] bitti. Toplam: {cat_count}")

    driver.quit()

    if all_products:
        save_to_mongodb(all_products)
    else:
        print("Hiç ürün toplanamadı, veri çekme kısmını kontrol et! ⚠️")

if __name__ == "__main__":
    scrape_a101()