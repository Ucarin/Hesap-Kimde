import time
import json
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By

# A101 kartlarında ilk sıradaki img bazen kampanya rozeti (aldın aldın, haftanın yıldızları).
_BAD_URL_PARTS = (
    "aldin-aldin", "aldin_aldin", "haftanin-yildizlari", "haftanin_yildizlari",
    "placeholder", "default_image", "/logo", ".svg",
)
_IMG_EXT = re.compile(r"\.(png|jpg|jpeg|webp)(\?|$)", re.I)


def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    if u.startswith("//"):
        u = "https:" + u
    return u


def _urls_from_srcset(srcset: str) -> list:
    if not srcset:
        return []
    out = []
    for part in srcset.split(","):
        url = part.strip().split()[0] if part.strip() else ""
        if url:
            out.append(_normalize_url(url))
    return out


def _a101_image_score(url: str) -> int:
    if not url or not url.startswith("http"):
        return -1
    low = url.lower()
    if any(b in low for b in _BAD_URL_PARTS):
        return -1
    if ".svg" in low:
        return -1
    m = re.search(r"/CALL/Image/get/([^_/?]+)_(\d+)x(\d+)\.(png|jpg|jpeg|webp)", url, re.I)
    if not m:
        return 1  # harici CDN vb.
    slug, w, h = m.group(1), int(m.group(2)), int(m.group(3))
    # Kampanya rozetleri: tireli, tamamı küçük harf, rakam yok (ürün anahtarları genelde karışık)
    if "-" in slug and slug.islower() and not any(c.isdigit() for c in slug):
        return -1
    pixels = w * h
    bonus = 500_000 if (any(c.isupper() for c in slug) or any(c.isdigit() for c in slug)) else 0
    return bonus + pixels


def _collect_image_candidates(card) -> list:
    cands = []
    for sel in card.find_elements(By.TAG_NAME, "picture"):
        for src_el in sel.find_elements(By.TAG_NAME, "source"):
            ss = (src_el.get_attribute("srcset") or "").strip()
            cands.extend(_urls_from_srcset(ss))
    for img in card.find_elements(By.TAG_NAME, "img"):
        for attr in ("src", "data-src", "data-lazy-src", "data-original", "data-srcset"):
            raw = img.get_attribute(attr)
            if not raw:
                continue
            if "srcset" in attr or ("," in raw and " " in raw and _IMG_EXT.search(raw)):
                cands.extend(_urls_from_srcset(raw))
            else:
                cands.append(_normalize_url(raw))
    seen = set()
    uniq = []
    for u in cands:
        if u and u.startswith("http") and u not in seen:
            seen.add(u)
            uniq.append(u)
    return uniq


def pick_product_image_url(card) -> str:
    scored = [(_a101_image_score(u), u) for u in _collect_image_candidates(card)]
    scored = [(s, u) for s, u in scored if s >= 0]
    if not scored:
        return ""
    scored.sort(key=lambda x: -x[0])
    return scored[0][1]

PRICE_LIMIT = 40.0

def parse_price(price_str):
    try:
        clean = price_str.replace("TL", "").replace("₺", "").replace(" ", "").replace("\xa0", "").replace(",", ".").strip()
        return float(clean)
    except:
        return 999.0

CATEGORIES = [
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/cikolata",        "category": "Çikolata"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/gofret",           "category": "Gofret"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/biskuvi-kraker",   "category": "Bisküvi & Kraker"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/kek",              "category": "Kek"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/cips",             "category": "Cips"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/kuruyemis-kuru-meyve", "category": "Kuruyemiş"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/sakiz-sekerleme",  "category": "Şekerleme & Sakız"},
    {"url": "https://www.a101.com.tr/kapida/atistirmalik/saglikli-atistirmaliklar", "category": "Sağlıklı"},
]

def scrape_a101():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--lang=tr-TR")

    print("A101 tarayıcısı başlatılıyor...")
    driver = uc.Chrome(options=options, version_main=146)

    products = []
    seen_products = set()
    first_page = True

    for cat_info in CATEGORIES:
        url = cat_info["url"]
        category_name = cat_info["category"]

        print(f"\n[{category_name}] Açılıyor: {url}")
        driver.get(url)
        time.sleep(12)  # Tüm sayfalar için yeterli bekleme

        # Sayfanın en üstüne git
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)

        # Adres/modal varsa kapat - daha kapsamlı
        for close_sel in [
            "button[aria-label='Kapat']",
            "button[aria-label='Close']",
            "button.close",
            "[class*='modal-close']",
            "[class*='Close']",
        ]:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, close_sel)
                for btn in btns:
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(1)
                        break
            except:
                pass

        # Hafifçe aşağı kaydır - lazy load tetikle
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        cat_count = 0

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

            # Ana kart selector - site yapısına göre güncellendi
            cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer.rounded-2xl")
            if not cards:
                cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer")
            if not cards:
                cards = driver.find_elements(By.CSS_SELECTOR, "li.set-product-item, [class*='ProductCard']")

            for card in cards:
                try:
                    # İsim: önce h3 dene, yoksa uzun text içeren ilk div'i bul
                    name = ""
                    name_h3 = card.find_elements(By.TAG_NAME, "h3")
                    if name_h3:
                        name = name_h3[0].text.strip()
                    else:
                        # Sitede bazı kategoriler h3 yerine div kullanıyor
                        for d in card.find_elements(By.TAG_NAME, "div"):
                            t = d.text.strip()
                            if len(t) > 10 and "₺" not in t and len(t) < 120:
                                name = t
                                break

                    if not name or name in seen_products:
                        continue

                    # Fiyat: önce bilinen class'ı dene, sonra ₺ içeren div
                    price_text = ""
                    price_specific = card.find_elements(By.CSS_SELECTOR, "[class*='font-medium']")
                    for p in price_specific:
                        if "₺" in p.text and len(p.text) < 20:
                            price_text = p.text.strip()
                            break

                    if not price_text:
                        price_divs = [d for d in card.find_elements(By.TAG_NAME, "div")
                                      if "₺" in d.text and len(d.text.strip()) < 20]
                        if price_divs:
                            price_text = price_divs[-1].text.strip()

                    if not price_text:
                        continue

                    price_val = parse_price(price_text)
                    if price_val > PRICE_LIMIT:
                        continue

                    img_url = pick_product_image_url(card)

                    seen_products.add(name)
                    products.append({
                        "name": name,
                        "price": price_text,
                        "image": img_url,
                        "category": category_name,
                        "market": "A101"
                    })
                    cat_count += 1

                except Exception:
                    pass

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                scroll_attempts += 1
                if scroll_attempts >= 2:
                    break
            else:
                scroll_attempts = 0
                last_height = new_height

        print(f"  [{category_name}] {cat_count} yeni ürün eklendi. (Toplam biriken: {len(products)})")

    driver.quit()

    if not products:
        print("\nUYARI: Hiç ürün bulunamadı! JSON dosyası güncellenmedi.")
        return

    file_name = "market_data.json"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump({"snacks": products}, f, ensure_ascii=False, indent=4)

    print(f"\nBAŞARILI: Toplam {len(products)} A101 ürünü '{file_name}' dosyasına kaydedildi!")

if __name__ == "__main__":
    scrape_a101()
