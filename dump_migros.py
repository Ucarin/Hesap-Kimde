import time
import undetected_chromedriver as uc

def dump_page():
    url = "https://www.migros.com.tr/atistirmalik-c-113fb"
    options = uc.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    
    print(f"Migros açılıyor...")
    driver = uc.Chrome(options=options, version_main=146)
    driver.get(url)
    time.sleep(10) # wait for cloudflare
    
    with open("migros_debug.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("Kaydedildi!")
    driver.quit()

if __name__ == '__main__':
    dump_page()
