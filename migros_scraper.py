import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

def scrape_migros():
    url = "https://www.migros.com.tr/atistirmalik-c-113fb"
    
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    print(f"Migros sayfası açılıyor: {url}")
    # Using version_main=146 to match your chrome version
    driver = uc.Chrome(options=options, version_main=146)
    driver.get(url)
    
    print("Sayfanın ve korumaların yüklenmesi bekleniyor (15s)...")
    time.sleep(15)
    
    products = []
    seen_products = set()

    print("Sayfa aşağı kaydırılıyor...")
    scroll_attempts = 0
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        
        # Migros ürün kartları genelde 'sm-list-page-item' veya 'mat-mdc-card' içinde olur.
        # Angular custom element yapısını yakalamaya çalışıyoruz.
        cards = driver.find_elements(By.CSS_SELECTOR, "sm-list-page-item, mat-card.mdc-card, article.product-card")
        
        for card in cards:
            try:
                raw_text = card.text
                if not raw_text.strip():
                    continue
                
                lines = raw_text.split("\n")
                lines = [line.strip() for line in lines if line.strip()]
                
                # İsim genelde ilk satırlardan biri olur, veya karta tıklamadan önceki uzun metindir.
                name = lines[0] # Çok kaba bir varsayım, ancak dinamik siteler için başlangıç
                price = "Bilinmiyor"
                
                # Fiyat genelde TL içeren satırdır
                for line in lines:
                    if "TL" in line:
                        price = line
                        break
                
                # Spesifik tag araması da yapabiliriz
                try:
                     name_elem = card.find_element(By.CSS_SELECTOR, "fe-product-name, .product-name")
                     name = name_elem.text.strip()
                except:
                     pass
                     
                try:
                     price_elem = card.find_element(By.CSS_SELECTOR, "fe-product-price, .price")
                     price = price_elem.text.strip()
                except:
                     pass

                price_val = 999.0
                try:
                    clean_price = price.replace(" TL", "").replace(",", ".")
                    price_val = float(clean_price)
                except:
                    pass

                if price_val <= 40.0 and name and name not in seen_products:
                    seen_products.add(name)
                    products.append({
                        "name": name,
                        "price": price,
                        "market": "Migros"
                    })
            except Exception as e:
                pass
        
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            scroll_attempts += 1
            if scroll_attempts >= 3:
                print("Sayfa sonuna gelindi.")
                break
        else:
            scroll_attempts = 0
            last_height = new_height
            print(f"Kaydırılıyor... Şu ana kadar {len(products)} ürün çekildi.")
            
        # Toplamda 100 ürün çekildeyse çık (test amaçlı)
        if len(products) > 100:
            break

    driver.quit()
    
    file_name = "market_data.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump({"snacks": products}, f, ensure_ascii=False, indent=4)
        
    print(f"\nToplam {len(products)} Migros ürünü başarıyla '{file_name}' dosyasına kaydedildi!")

if __name__ == "__main__":
    scrape_migros()
