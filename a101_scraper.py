def scrape_a101():
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    # Bazı headless algılamalarını aşmak için
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("A101 tarayıcısı başlatılıyor...")
    driver = uc.Chrome(options=options)

    all_products = [] # Tüm kategorileri burada toplayacağız
    seen_products = set()

    for cat_info in CATEGORIES:
        url = cat_info["url"]
        category_name = cat_info["category"]
        cat_count = 0

        print(f"\n[{category_name}] İşleniyor: {url}")
        driver.get(url)
        time.sleep(8) # Sayfa yüklenme payı

        # Sayfa sonuna kadar yavaş yavaş kaydır (Lazy Load dostu)
        last_height = driver.execute_script("return document.body.scrollHeight")
        
        while True:
            # Parça parça kaydır ki resimler ve yeni ürünler yüklensin
            for i in range(1, 5):
                driver.execute_script(f"window.scrollTo(0, {last_height} * {i/4});")
                time.sleep(1)

            # Yeni ürünleri topla
            cards = driver.find_elements(By.CSS_SELECTOR, "div.w-full.border.cursor-pointer, li.set-product-item")
            
            for card in cards:
                try:
                    # İsim bulma
                    name = ""
                    name_els = card.find_elements(By.TAG_NAME, "h3")
                    if name_els:
                        name = name_els[0].text.strip()
                    
                    if not name or name in seen_products:
                        continue

                    # Fiyat bulma
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

                    seen_products.add(name)
                    all_products.append({
                        "name": name,
                        "price": price_text,
                        "image": img_url,
                        "category": category_name,
                        "market": "A101"
                    })
                    cat_count += 1
                except:
                    continue

            # Döngü kontrolü: Daha fazla ürün yükleniyor mu?
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # 2 saniye daha bekle, belki internet yavaştır
                time.sleep(2)
                if driver.execute_script("return document.body.scrollHeight") == last_height:
                    break # Gerçekten bitti
            last_height = new_height
            print(f"  > Şu ana kadar {cat_count} ürün bulundu...", end="\r")

        print(f"\n  [{category_name}] bitti. Toplam: {cat_count} ürün.")

    driver.quit()

    # JSON Kaydetme
    if all_products:
        with open("market_data.json", "w", encoding="utf-8") as f:
            json.dump({"snacks": all_products}, f, ensure_ascii=False, indent=4)
        print(f"\nİŞLEM TAMAM: Toplam {len(all_products)} ürün MongoDB'ye basılmaya hazır!")