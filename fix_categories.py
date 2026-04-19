import json
import os

# --- DÜZELTME KURALLARI ---
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

def fix_json_file():
    input_file = "market_data.json"
    
    if not os.path.exists(input_file):
        print(f"❌ HATA: {input_file} dosyası bulunamadı!")
        return

    print(f"📂 {input_file} okunuyor ve kategoriler düzeltiliyor...")
    
    with open(input_file, "r", encoding="utf-8") as f:
        products = json.load(f)

    updated_count = 0
    
    # Eğer JSON bir liste değilse (sözlük içindeyse) düzeltelim
    if isinstance(products, dict) and "snacks" in products:
        target_list = products["snacks"]
    else:
        target_list = products

    for product in target_list:
        name_lower = product.get("name", "").lower()
        old_category = product.get("category", "Bilinmiyor")
        found_category = None

        # Kuralları kontrol et
        for cat_name, keywords in rules.items():
            if any(key in name_lower for key in keywords):
                found_category = cat_name
                break
        
        # Eğer bir eşleşme bulduysak ve eskiden farklıysa (veya hepsi çikolataysa) güncelle
        if found_category and old_category != found_category:
            product["category"] = found_category
            updated_count += 1
            # print(f"Düzenlendi: {product['name']} -> {found_category}")

    # Düzeltilmiş veriyi aynı dosyaya geri yaz
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

    print(f"\n✅ İŞLEM TAMAMLANDI!")
    print(f"📊 Toplam {len(target_list)} üründen {updated_count} tanesinin kategorisi güncellendi.")
    print(f"💾 Değişiklikler {input_file} dosyasına kaydedildi.")

if __name__ == "__main__":
    fix_json_file()