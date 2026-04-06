import time
import json
import pymongo
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# --- MONGODB AYARLARI ---
# Buradaki tırnak içine kendi MongoDB Connection String'ini yapıştır
MONGO_URI = "mongodb+srv://ersinucar:SIFREN@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
client = pymongo.MongoClient(MONGO_URI)
db = client["ersinucar"] # Görselindeki DB adı
collection = db["snacks"] # Görselindeki koleksiyon adı

def save_to_mongodb(products):
    if not products:
        return
    print(f"\n{len(products)} ürün MongoDB'ye senkronize ediliyor...")
    for product in products:
        # Upsert: Ürün varsa güncelle, yoksa ekle (İsim ve Market eşleşmesine göre)
        collection.update_one(
            {"name": product["name"], "market": product["market"]},
            {"$set": product},
            upsert=True
        )
    print("Veritabanı güncellendi! ✅")

def scrape_a101():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("A101 tarayıcısı başlatılıyor...")
    driver = uc.Chrome(options=options)

    all_products = [] 
    seen_products = set()

    for cat_info in CATEGORIES:
        url = cat_info["url"]
        category_name = cat_info["category"]
        cat_count = 0

        print(f"\n[{category_name}] İşleniyor: {url}")
        driver.get(url)
        time.sleep(8) 

        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Sayfayı parça parça kaydır (Lazy Load'ı tetikler)
            for i in range(1, 5):
                driver.execute_script(f"window.scrollTo(0, {last_height} * {i/4});")
                time.sleep(1)

            cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer, li.set-product-item")
            
            for card in cards:
                try:
                    name = ""
                    name_els = card.find_elements(By.TAG_NAME, "h3")
                    if name_els:
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
                time.sleep(2)
                if driver.execute_script("return document.body.scrollHeight") == last_height:
                    break 
            last_height = new_height
            print(f"  > {category_name}: {cat_count} ürün bulundu...", end="\r")

        print(f"\n  [{category_name}] bitti. Toplam: {cat_count} ürün.")

    driver.quit()

    # --- KAYIT İŞLEMLERİ ---
    if all_products:
        # 1. Yerel Yedek (JSON)
        with open("market_data.json", "w", encoding="utf-8") as f:
            json.dump({"snacks": all_products}, f, ensure_ascii=False, indent=4)
        
        # 2. Canlı Veritabanı (MongoDB)
        save_to_mongodb(all_products)
        
        print(f"\nİŞLEM TAMAM: Toplam {len(all_products)} ürün hem JSON'a hem MongoDB'ye kaydedildi!")

if __name__ == "__main__":
    scrape_a101()