# ============================================================
# 🍿 Hesap Kimde? - Tek Tıkla Deploy Scripti (v1.1)
# ============================================================

# --- AYARLAR ---
$SERVER_IP = "92.5.117.194"
$SERVER_USER = "ubuntu"
$REMOTE_PATH = "/home/ubuntu/app"
$SSH_KEY = ".\oracle_yeni"
$COMMIT_MSG = "Auto-deploy: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

# 1. YEREL İŞLEMLER (GIT)
Write-Host "`n[1/3] Yerel değişiklikler kaydediliyor..." -ForegroundColor Cyan
git add .
git commit -m $COMMIT_MSG
Write-Host ">>> GitHub'a gönderiliyor..." -ForegroundColor Cyan
git push origin main

# 2. SUNUCU İŞLEMLERİ (SSH)
Write-Host "`n[2/3] Sunucuya bağlanılıyor ($SERVER_IP)..." -ForegroundColor Cyan

# Sunucuda çalışacak komutlar dizisi
$REMOTE_COMMANDS = "cd $REMOTE_PATH && git pull && pip install -r requirements.txt"

# Senin belirttiğin özel restart yöntemi
$RESTART_CMD = "sudo fuser -k 8000/tcp; nohup python3 server.py > debug.log 2>&1 &"

Write-Host ">>> Kodlar güncelleniyor ve uygulama yeniden başlatılıyor..." -ForegroundColor Cyan
ssh -i $SSH_KEY -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "$REMOTE_COMMANDS && $RESTART_CMD"

# 3. SONUÇ
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[BAŞARILI] Deploy tamamlandı! 🚀" -ForegroundColor Green
    Write-Host "Adres: http://$SERVER_IP`n" -ForegroundColor Green
} else {
    Write-Host "`n[HATA] Bir sorun oluştu. Sunucu bağlantısını veya yolu kontrol et." -ForegroundColor Red
}
