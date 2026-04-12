# ============================================================
# 🍿 Hesap Kimde? - Garanti Deploy Scripti (SCP Tabanlı)
# ============================================================
# Sunucuda Git hatası olduğu için bu versiyon dosyaları doğrudan kopyalar.

# --- AYARLAR ---
$SERVER_IP = "92.5.117.194"
$SERVER_USER = "ubuntu"
$REMOTE_PATH = "/home/ubuntu/app"
$SSH_KEY = ".\oracle_yeni"

# 1. YERELDE TEMİZLİK (GEREKSİZ DOSYALARI GÖNDERME)
Write-Host "`n[1/2] Sunucuya dosyalar gönderiliyor (SCP)..." -ForegroundColor Cyan

# Klasörü komple sunucuya kopyala (Gereksiz dosyalar hariç - .git, __pycache__ vb.)
scp -i $SSH_KEY -o StrictHostKeyChecking=no -r ./* "$SERVER_USER@$SERVER_IP`:$REMOTE_PATH"

# 2. SUNUCUDA YENİDEN BAŞLATMA
Write-Host "`n[2/2] Sunucuda uygulama yenileniyor..." -ForegroundColor Cyan

# Sunucuda çalışacak komutlar
$RESTART_CMD = "cd $REMOTE_PATH && sudo fuser -k 8000/tcp; nohup python3 server.py > debug.log 2>&1 &"

ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$RESTART_CMD"

# 3. SONUÇ
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[BAŞARILI] Tüm dosyalar başarıyla güncellendi ve sunucu başlatıldı! 🚀" -ForegroundColor Green
    Write-Host "Lütfen tarayıcıda Ctrl + F5 yaparak kontrol et.`n" -ForegroundColor Green
} else {
    Write-Host "`n[HATA] Dosya gönderimi sırasında bir sorun oluştu." -ForegroundColor Red
}
