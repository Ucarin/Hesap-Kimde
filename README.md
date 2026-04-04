# 🍿 Hesap Kimde? - Bulut Göçü ve Kurulum Rehberi

Bu rehber, uygulamayı MongoDB kullanarak buluta (Railway, Render vb.) taşımak ve internet üzerinden herkesin erişimine açmak için hazırlanmıştır.

## 1. Hazırlık ve Gereksinimler

Uygulamanın çalışması için MongoDB bağlantısına ihtiyacı vardır.

1.  **MongoDB Atlas Hesabı:** [mongodb.com](https://www.mongodb.com/cloud/atlas) üzerinden ücretsiz bir hesap açın ve bir "Cluster" oluşturun.
2.  **Bağlantı Linki (URI):** "Connect" butonuna basarak Python sürücüsü için olan bağlantı linkini kopyalayın.
3.  **Environment Variables:** `.env.template` dosyasının adını `.env` olarak değiştirin ve içine kopyaladığınız linki yapıştırın:
    ```env
    MONGODB_URI=mongodb+srv://kullanici:sifre@cluster.mongodb.net/snack_roulette?retryWrites=true&w=majority
    ```

## 2. Mevcut Verileri Taşıma (Migrasyon)

Eğer yerel bilgisayarınızdaki `market_data.json` ve `payment_history.json` verilerini MongoDB'ye aktarmak isterseniz:
1.  Bağımlılıkları yükleyin: `pip install -r requirements.txt`
2.  `.env` dosyasının hazır olduğundan emin olun.
3.  Şu komutu çalıştırın:
    ```bash
    python migrate_to_mongo.py
    ```

## 3. Buluta Verilme (Deployment)

Uygulama **Railway** veya **Render** gibi platformlar için uyumludur (Procfile hazır).

### Railway Kurulumu:
1.  Projeyi GitHub'a yükleyin.
2.  Railway.app üzerinde yeni bir servis oluşturun ve GitHub deponuzu bağlayın.
3.  "Variables" kısmına `.env` dosyasındaki `MONGODB_URI` değerini ekleyin.
4.  Railway otomatik olarak `Procfile` dosyasını tanıyacak ve uygulamayı başlatacaktır.

## 4. Yerel Çalıştırma

Geliştirme aşamasında yerel olarak çalıştırmak için:
```bash
python server.py
```
Uygulama `http://localhost:8000` adresinden erişilebilir olacaktır.

---

İyi eğlenceler! 🍿🔥
