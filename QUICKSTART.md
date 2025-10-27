# ⚡ Hızlı Başlangıç - 15 Dakikada Sigma Analyst

Bu rehber, sistemi **en hızlı şekilde** çalıştırmanızı sağlar.

---

## 📋 Ön Hazırlık (5 dakika)

### 1. Docker Desktop Çalıştırın

```powershell
# Docker Desktop'ın açık olduğunu kontrol edin
docker --version
```

✅ Çıktı: `Docker version 27.x.x`

---

### 2. .env Dosyası Oluşturun

```powershell
# Proje klasörüne gidin
cd D:\3\dosya

# .env dosyasını kopyalayın
Copy-Item .env.example .env

# Düzenleyin (sadece 2 satır gerekli!)
notepad .env
```

**Minimum .env (sadece şu 2 satırı değiştirin):**
```env
POSTGRES_PASSWORD=SizinSifreniz123!
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
```

💡 **Anthropic API key almanız 2 dakika sürer:** https://console.anthropic.com/settings/keys

---

## 🚀 Başlatma (10 dakika)

### 3. Container'ları Başlatın

```powershell
docker-compose up -d --build
```

⏳ **İlk çalıştırmada 10-15 dakika sürer** (paketler indiriliyor).

Çıktı:
```
[+] Building 125.3s ...
[+] Running 6/6
 ✔ Container sigma_postgres      Started
 ✔ Container sigma_redis         Started
 ✔ Container sigma_backend       Started
 ✔ Container sigma_celery_worker Started
 ✔ Container sigma_flower        Started
```

---

### 4. Test Edin

**API test:**
```
http://localhost:8000/docs
```

→ Swagger UI görmelisiniz ✅

**Celery izleme:**
```
http://localhost:5555
```

→ Flower dashboard görmelisiniz ✅

---

## 🎯 İlk Analiz (5 dakika)

### 5. Oneshot Analiz

```powershell
# Backend container'ına girin
docker-compose exec backend bash

# Bitcoin analizi yapın
python -m backend.cli analyze --symbols BTCUSDT --mode oneshot
```

**Çıktı:**
```
🤖 Sigma Analyst - Market Analysis
═══════════════════════════════════

📊 Symbol: BTCUSDT
⏰ Timeframes: 1H, 4H, 1D

⏳ Collecting data... ✅
⏳ Feature engineering... ✅
⏳ Model inference... ✅
⏳ Claude reasoning... ✅

═══════════════════════════════════
📈 MARKET PULSE
═══════════════════════════════════

**BTCUSDT: BULLISH BIAS** 🟢
...
(detaylı analiz)
...
```

✅ **İlk analiz tamamlandı!**

---

## 📚 Sonraki Adımlar

Artık sisteminiz çalışıyor! Şunları yapabilirsiniz:

### 1. Model Eğitimi

```bash
# Tarihsel veri indirin (container içindeyken)
python -m backend.data.collectors.binance_collector download \
  --symbol BTCUSDT --interval 1h --start 2023-01-01 --end 2024-12-31

# Model eğitin
python -m backend.models.train \
  --data data/features/BTCUSDT_1h_features.parquet \
  --model ensemble \
  --device cuda
```

---

### 2. Backtest

```bash
python -m backend.backtest.backtest_engine run \
  --strategy ensemble \
  --symbol BTCUSDT \
  --start 2023-01-01 \
  --end 2024-12-31
```

---

### 3. Monitor Mode (sürekli izleme)

```bash
python -m backend.cli monitor \
  --symbols BTCUSDT \
  --freq 15m
```

**Durdurma:** `Ctrl+C`

---

## 🛑 Durdurma

```powershell
# Geçici durdur
docker-compose stop

# Tekrar başlat
docker-compose start

# Tamamen sil (veriler kalır)
docker-compose down
```

---

## 🆘 Sorun mu var?

**Container çalışmıyor?**
```powershell
docker-compose logs -f backend
```

**Port hatası?**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Detaylı sorun giderme:** [DOCKER_SETUP_GUIDE.md#10-sorun-giderme](DOCKER_SETUP_GUIDE.md#10-sorun-giderme)

---

## 📖 Tam Rehber

**Tüm özellikleri öğrenmek için:**
- [DOCKER_SETUP_GUIDE.md](DOCKER_SETUP_GUIDE.md) - Detaylı kurulum ve kullanım
- [README.md](README.md) - Genel proje bilgisi

---

**Made with 🧠 and 📊 for smarter crypto trading**
