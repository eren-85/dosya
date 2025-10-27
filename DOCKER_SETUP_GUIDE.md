# 🐳 Docker ile Sigma Analyst - Komple Kurulum Rehberi

**Son güncelleme**: 2025-01-27

Bu rehber, **hiç Docker bilmeyen** biri için hazırlanmıştır. Her adımı **detaylıca** açıklayacağım.

---

## 📋 İçindekiler

1. [Docker Nedir ve Ne İşe Yarar?](#1-docker-nedir-ve-ne-i̇şe-yarar)
2. [Kurulum Öncesi Hazırlık](#2-kurulum-öncesi-hazırlık)
3. [Adım Adım Docker Kurulumu](#3-adım-adım-docker-kurulumu)
4. [Sistemi İlk Kez Çalıştırma](#4-sistemi-i̇lk-kez-çalıştırma)
5. [API Anahtarlarını Ayarlama](#5-api-anahtarlarını-ayarlama)
6. [Model Eğitimi](#6-model-eğitimi)
7. [Analiz Çalıştırma](#7-analiz-çalıştırma)
8. [Backtest Yapma](#8-backtest-yapma)
9. [Sistemi Durdurma ve Yönetme](#9-sistemi-durdurma-ve-yönetme)
10. [Sorun Giderme](#10-sorun-giderme)

---

## 1. Docker Nedir ve Ne İşe Yarar?

**Docker**, uygulamaları "container" (konteyner) adı verilen izole ortamlarda çalıştırmanızı sağlar.

**Neden Docker kullanıyoruz?**
- ✅ **Kurulum kolaylığı**: Python, PostgreSQL, Redis vs. tek komutla kurulur
- ✅ **Bağımlılık yok**: Windows'ta Linux uygulamaları çalışır
- ✅ **Temiz sistem**: Sisteminizi kirletmez, istediğiniz zaman silebilirsiniz
- ✅ **Aynı ortam**: Herkesin aynı versiyonları çalışır

**Sigma Analyst'da Docker ile çalışan parçalar:**
```
┌─────────────────────────────────────────┐
│  Docker Desktop (ana program)           │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Container 1: PostgreSQL          │  │ <- Veritabanı
│  │ (verileri saklar)                │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Container 2: Redis               │  │ <- Hızlı cache
│  │ (geçici veri)                    │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Container 3: Backend (FastAPI)   │  │ <- Ana uygulama
│  │ (Python kodları çalışır)         │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Container 4: Celery Worker       │  │ <- Arka plan işleri
│  │ (model eğitimi, veri toplama)    │  │
│  └──────────────────────────────────┘  │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │ Container 5: Flower              │  │ <- İzleme paneli
│  │ (işleri görselleştirir)          │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 2. Kurulum Öncesi Hazırlık

### 2.1. Sistem Gereksinimleri

**Windows için:**
- Windows 10/11 Pro veya Home (64-bit)
- En az 8GB RAM (16GB önerilir)
- En az 20GB boş disk alanı
- WSL 2 (Windows Subsystem for Linux) - Docker otomatik kuracak

**Donanım:**
- RTX 4060 8GB (var ✅) - GPU eğitimi için mükemmel

### 2.2. Dosya Yapısı

Projeniz şu şekilde olmalı:
```
D:\3\dosya\                          <- Ana klasör
├── backend\                         <- Python kodları
│   ├── api\                         <- FastAPI server
│   ├── models\                      <- ML modelleri
│   ├── data\                        <- Veri işleme
│   └── ...
├── data\                            <- Veri klasörü
│   ├── knowledge\                   <- PDF'ler buraya
│   ├── annotations\                 <- Manuel eğitim verileri
│   ├── historical\                  <- Tarihsel veriler
│   └── training\                    <- Eğitim sonuçları
├── Dockerfile                       <- Docker build talimatları
├── docker-compose.yml               <- Container ayarları
├── requirements.txt                 <- Python paketleri
├── .env                             <- ⚠️ Siz oluşturacaksınız
└── README.md
```

---

## 3. Adım Adım Docker Kurulumu

### 3.1. Docker Desktop'ı Başlatma

Docker Desktop'ı kurdunuz (✅). Şimdi:

**Adım 1: Docker Desktop'ı açın**
```powershell
# Başlat menüsünden "Docker Desktop" araması yapın
# veya PowerShell'de:
start "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

**Adım 2: Docker'ın başlamasını bekleyin**
- Docker Desktop açıldığında sağ altta "Docker Engine starting..." yazacak
- Başladığında "Docker Desktop is running" göreceksiniz (2-3 dakika sürer)
- Whale (balina) ikonu sistem tepsisinde görünecek

**Adım 3: Docker'ın çalıştığını kontrol edin**
```powershell
# PowerShell'i yönetici olarak açın (Sağ tık -> "Run as administrator")
docker --version
```

**Çıktı şöyle olmalı:**
```
Docker version 27.x.x, build xxxxx
```

**Eğer hata alırsanız:**
```
docker: command not found
```
→ Docker Desktop'ı kapatıp tekrar açın ve 2-3 dakika bekleyin.

---

### 3.2. WSL 2 Kontrolü (Windows için)

Docker, Windows'ta WSL 2 (Windows Subsystem for Linux) kullanır.

**Kontrol:**
```powershell
wsl --status
```

**Eğer WSL kurulu değilse:**
```powershell
# Yönetici PowerShell'de:
wsl --install
# Bilgisayarı yeniden başlatın
```

---

## 4. Sistemi İlk Kez Çalıştırma

### 4.1. Proje Klasörüne Gidin

```powershell
# PowerShell'de projenizin klasörüne gidin:
cd D:\3\dosya
```

**Klasörde olduğunuzu doğrulayın:**
```powershell
ls
```
→ `docker-compose.yml`, `Dockerfile`, `backend/` gibi dosyaları görmelisiniz.

---

### 4.2. `.env` Dosyasını Oluşturun

`.env` dosyası, **şifreler ve API anahtarlarınızı** saklar.

**Adım 1: `.env.example` dosyasını kopyalayın**
```powershell
# PowerShell'de:
Copy-Item .env.example .env
```

**Adım 2: `.env` dosyasını düzenleyin**
```powershell
# Notepad ile açın:
notepad .env
```

**Minimum çalışması için şunları düzenleyin:**
```env
# === Veritabanı Şifresi (ÖNEMLİ: Değiştirin!) ===
POSTGRES_PASSWORD=SizinGucluSifreniz123!

# === API Anahtarları (başlangıç için boş bırakabilirsiniz) ===
BINANCE_API_KEY=
BINANCE_API_SECRET=

# === AI API Anahtarları (Claude veya OpenAI - en az biri gerekli) ===
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxx
# veya
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxx
```

**💡 İpucu:** API anahtarları olmadan da sistem çalışır, ancak bazı özellikler eksik olur.

**Kaydedin ve kapatın** (Ctrl+S → Notepad'i kapatın).

---

### 4.3. Docker Container'ları Başlatma

Artık sistemi başlatmaya hazırız! 🚀

**Adım 1: Container'ları build edin ve başlatın**
```powershell
docker-compose up -d --build
```

**Ne yapıyor bu komut?**
- `docker-compose`: Birden fazla container'ı yönetir
- `up`: Container'ları başlat
- `-d`: Arka planda çalıştır (detached mode)
- `--build`: İlk kez çalıştırıyorsak, image'ları build et

**İlk çalıştırmada ne olur?**
```
[+] Building 125.3s (14/14) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 650B
 => [internal] load .dockerignore
 => CACHED [base 1/7] FROM python:3.10-slim
 => [base 2/7] RUN apt-get update && apt-get install -y ...
 => [base 3/7] WORKDIR /app
 => [base 4/7] COPY requirements.txt .
 => [base 5/7] RUN pip install --upgrade pip && ...
    ⏳ PyTorch, NumPy, pandas vs. kurulumu (5-10 dakika sürer!)
 => [base 6/7] COPY backend /app/backend
 => [base 7/7] COPY data /app/data
 => exporting to image
 => => writing image sha256:abc123...
 => => naming to docker.io/library/dosya-backend
[+] Running 6/6
 ✔ Network dosya_sigma_network          Created
 ✔ Volume "dosya_postgres_data"         Created
 ✔ Volume "dosya_redis_data"            Created
 ✔ Container sigma_postgres             Started
 ✔ Container sigma_redis                Started
 ✔ Container sigma_backend              Started
 ✔ Container sigma_celery_worker        Started
 ✔ Container sigma_celery_beat          Started
 ✔ Container sigma_flower               Started
```

**⏱️ Süre:** İlk çalıştırmada **10-15 dakika** sürer (Python paketleri indiriliyor).

---

### 4.4. Container'ların Çalıştığını Kontrol Edin

**Komut:**
```powershell
docker-compose ps
```

**Çıktı şöyle olmalı:**
```
NAME                   IMAGE              STATUS          PORTS
sigma_backend          dosya-backend      Up 2 minutes    0.0.0.0:8000->8000/tcp
sigma_celery_beat      dosya-backend      Up 2 minutes
sigma_celery_worker    dosya-backend      Up 2 minutes
sigma_flower           dosya-backend      Up 2 minutes    0.0.0.0:5555->5555/tcp
sigma_postgres         timescale/...      Up 2 minutes    0.0.0.0:5432->5432/tcp
sigma_redis            redis:7-alpine     Up 2 minutes    0.0.0.0:6379->6379/tcp
```

**Tüm container'lar `Up` durumunda olmalı! ✅**

---

### 4.5. API'nin Çalıştığını Test Edin

**Tarayıcınızda açın:**
```
http://localhost:8000/docs
```

**Göreceğiniz sayfa:**
- **Swagger UI** - API'nin tüm endpoint'leri listelenir
- `GET /health` endpoint'i test edebilirsiniz (Try it out → Execute)

**Çıktı:**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-01-27T10:30:00Z"
}
```

✅ **Sistem çalışıyor!**

---

### 4.6. Celery Flower (İzleme Paneli)

Arka plan işlerini izlemek için:

**Tarayıcınızda açın:**
```
http://localhost:5555
```

**Göreceğiniz:**
- **Tasks**: Çalışan/tamamlanan görevler
- **Workers**: Aktif worker sayısı
- **Monitor**: Gerçek zamanlı grafik

---

## 5. API Anahtarlarını Ayarlama

Sistemin **tüm özelliklerini** kullanmak için API anahtarları gerekiyor.

### 5.1. Hangi API Anahtarları Gerekli?

| API | Zorunlu mu? | Ne için? | Nasıl alınır? |
|-----|-------------|----------|---------------|
| **Anthropic (Claude)** | ✅ Evet | Ana AI analiz | https://console.anthropic.com |
| **OpenAI** | ❌ Opsiyonel | Alternatif AI | https://platform.openai.com |
| **Binance** | ❌ Opsiyonel | Fiyat/hacim verisi | https://www.binance.com/en/my/settings/api-management |
| **Glassnode** | ❌ Opsiyonel | On-chain veriler | https://studio.glassnode.com/settings/api |
| **CryptoQuant** | ❌ Opsiyonel | On-chain veriler | https://cryptoquant.com/asset/btc/summary |

**💡 Minimum çalışma:**
- Sadece **Anthropic API** ile sistem çalışır
- Diğer API'lar olmadan → Ücretsiz veri kaynaklarını kullanır (CoinGecko, Binance public API)

---

### 5.2. Anthropic API Anahtarı Alma (Claude)

**Adım 1: Anthropic Console'a gidin**
```
https://console.anthropic.com
```

**Adım 2: Kaydolun / Giriş yapın**
- Email + şifre ile hesap oluşturun
- Email doğrulaması yapın

**Adım 3: API Key oluşturun**
- Sol menüden **"API Keys"** sekmesine tıklayın
- **"Create Key"** butonuna tıklayın
- Key'i kopyalayın (örnek: `sk-ant-api03-xxxxxxxxxxxxx`)

**Adım 4: `.env` dosyasına ekleyin**
```powershell
notepad .env
```

Şu satırı bulun ve yapıştırın:
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxx
```

Kaydedin.

**Adım 5: Container'ları yeniden başlatın**
```powershell
docker-compose restart
```

---

### 5.3. Binance API Anahtarı Alma (Opsiyonel)

**Adım 1: Binance'te giriş yapın**
```
https://www.binance.com
```

**Adım 2: API Management**
- Profil → API Management → Create API

**Adım 3: Güvenlik ayarları**
- **Read** yetkisi yeterli (Trade yetkisi KAPALI olsun!)
- IP whitelist ekleyin (güvenlik için)

**Adım 4: API Key ve Secret'i kopyalayın**

**Adım 5: `.env` dosyasına ekleyin**
```env
BINANCE_API_KEY=xxxxxxxxxxxxxxxxx
BINANCE_API_SECRET=xxxxxxxxxxxxxxxxx
```

---

## 6. Model Eğitimi

Sigma Analyst'ın **makine öğrenmesi modellerini** eğitelim.

### 6.1. Tarihsel Veri İndirme

**Backend container'ına bağlanın:**
```powershell
docker-compose exec backend bash
```

**Şimdi container içindesiniz!** Prompt şöyle değişir:
```
root@abc123:/app#
```

**Binance'ten tarihsel veri indirin:**
```bash
python -m backend.data.collectors.binance_collector download \
  --symbol BTCUSDT \
  --interval 1h \
  --start "2023-01-01" \
  --end "2024-12-31"
```

**Çıktı:**
```
📊 Binance Historical Data Download
Symbol: BTCUSDT
Interval: 1h
Period: 2023-01-01 → 2024-12-31

⏳ Downloading... (8760 candles)
████████████████████████████████ 100%

✅ Downloaded 8760 candles
💾 Saved to: data/historical/BTCUSDT_1h.csv
```

**Daha fazla sembol için:**
```bash
# Ethereum
python -m backend.data.collectors.binance_collector download \
  --symbol ETHUSDT --interval 1h --start "2023-01-01" --end "2024-12-31"

# Solana
python -m backend.data.collectors.binance_collector download \
  --symbol SOLUSDT --interval 1h --start "2023-01-01" --end "2024-12-31"
```

---

### 6.2. Feature Engineering (Özellik Çıkarımı)

İndirdiğimiz verilerden **200+ teknik indikatör** hesaplayalım.

```bash
python -m backend.data.processors.feature_engineering process \
  --input data/historical/BTCUSDT_1h.csv \
  --output data/features/BTCUSDT_1h_features.parquet
```

**Çıktı:**
```
🔧 Feature Engineering
Input: BTCUSDT_1h.csv (8760 rows)

⏳ Calculating indicators...
  ✅ Trend indicators (21) - 0.5s
  ✅ Momentum indicators (35) - 0.8s
  ✅ Volatility indicators (12) - 0.3s
  ✅ Volume indicators (18) - 0.4s
  ✅ ICT concepts (25) - 1.2s
  ✅ Smart Money (15) - 0.6s
  ✅ Fibonacci levels (10) - 0.2s

✅ Total features: 248
💾 Saved: data/features/BTCUSDT_1h_features.parquet
```

---

### 6.3. Model Eğitimi

Artık **Ensemble Model** (XGBoost + LightGBM + CatBoost) eğitebiliriz!

```bash
python -m backend.models.train \
  --data data/features/BTCUSDT_1h_features.parquet \
  --model ensemble \
  --epochs 100 \
  --device cuda  # RTX 4060 kullan
```

**Çıktı:**
```
🚀 Model Training - Ensemble
📊 Dataset: 8760 samples, 248 features
🔀 Train/Val split: 7008 / 1752

⚙️ GPU Detection
   Device: NVIDIA GeForce RTX 4060 Laptop
   VRAM: 8.0 GiB (8.6 GB)
   Compute: 8.9 (Ada Lovelace)
   ✅ BF16: Enabled
   ✅ TF32: Enabled

🌲 Training XGBoost...
   [10]   train-rmse:0.0245   val-rmse:0.0312
   [20]   train-rmse:0.0189   val-rmse:0.0287
   [50]   train-rmse:0.0098   val-rmse:0.0234
   [100]  train-rmse:0.0045   val-rmse:0.0223
   ✅ XGBoost - Val Accuracy: 97.7%

🍃 Training LightGBM...
   Epoch 50/100: loss=0.0256, val_loss=0.0278
   ✅ LightGBM - Val Accuracy: 94.2%

🐈 Training CatBoost...
   Epoch 80/100: loss=0.0201, val_loss=0.0198
   ✅ CatBoost - Val Accuracy: 99.2%

🎯 Ensemble Model
   Weighted Accuracy: 96.8%
   💾 Saved: data/models/ensemble_btcusdt_1h.pkl
```

**⏱️ Süre:** RTX 4060 ile ~10-20 dakika

---

### 6.4. Deep Learning Model Eğitimi (LSTM/Transformer)

**LSTM eğitimi:**
```bash
python -m backend.models.deep_learning_trainer \
  --data data/features/BTCUSDT_1h_features.parquet \
  --model lstm \
  --epochs 100 \
  --batch-size 112  # RTX 4060 optimal
```

**Çıktı:**
```
🚀 Deep Learning Trainer (LSTM)
   Device: cuda
   Batch Size: 112
   Mixed Precision: BF16

🏋️  Training LSTM Model
   Training samples: 7008
   Validation samples: 1752
   Total parameters: 1,847,553
   Trainable parameters: 1,847,553

   Epoch 10/100 | Train Loss: 0.0234 | Val Loss: 0.0312
   Epoch 20/100 | Train Loss: 0.0189 | Val Loss: 0.0287
   ...
   Epoch 90/100 | Train Loss: 0.0067 | Val Loss: 0.0098

⏹️  Early stopping at epoch 95

✅ Training completed
💾 Model saved: data/models/lstm_btcusdt_1h.pth
```

---

### 6.5. Reinforcement Learning (RL) Eğitimi

**PPO agent eğitimi:**
```bash
python -m backend.models.rl_trainer \
  --env TradingEnv-v0 \
  --data data/features/BTCUSDT_1h_features.parquet \
  --episodes 10000 \
  --device cuda
```

**Çıktı:**
```
🎮 Reinforcement Learning - PPO
   Environment: TradingEnv-v0
   Device: cuda (RTX 4060)
   Episodes: 10000

⏳ Training...
   Episode 100  | Reward: 125.3  | Win Rate: 45.2%
   Episode 500  | Reward: 348.7  | Win Rate: 52.1%
   Episode 1000 | Reward: 567.2  | Win Rate: 56.8%
   ...
   Episode 10000| Reward: 892.4  | Win Rate: 61.3%

✅ Training completed
💾 Saved: data/models/ppo_btcusdt_1h.zip

📊 Final Stats:
   Sharpe Ratio: 2.1
   Max Drawdown: 14.2%
   Win Rate: 61.3%
```

**⏱️ Süre:** ~2-4 saat (10K episode)

---

### 6.6. Container'dan Çıkma

```bash
exit
```

→ PowerShell'e geri dönersiniz.

---

## 7. Analiz Çalıştırma

Şimdi **gerçek zamanlı analiz** yapalım!

### 7.1. CLI ile Oneshot Analiz

**Backend container'ına girin:**
```powershell
docker-compose exec backend bash
```

**Analiz komutu:**
```bash
python -m backend.cli analyze \
  --symbols BTCUSDT,ETHUSDT \
  --timeframes 1H,4H,1D \
  --mode oneshot
```

**Çıktı:**
```
🤖 Sigma Analyst - Market Analysis
═══════════════════════════════════

📊 Symbols: BTCUSDT, ETHUSDT
⏰ Timeframes: 1H, 4H, 1D
🔍 Mode: Oneshot

⏳ Collecting data...
  ✅ Binance: BTCUSDT, ETHUSDT
  ✅ On-chain: Glassnode metrics
  ✅ Derivatives: OI, Funding Rate

⏳ Feature engineering...
  ✅ 248 features calculated

⏳ Model inference...
  ✅ Ensemble: BUY (confidence: 78.5%)
  ✅ LSTM: BUY (confidence: 82.1%)
  ✅ RL Agent: HOLD (Q-value: 0.345)

⏳ Claude reasoning...
  ✅ Analysis completed

═══════════════════════════════════
📈 MARKET PULSE
═══════════════════════════════════

**BTCUSDT: BULLISH BIAS** 🟢

**Teknik Analiz (1H/4H/1D):**
- 1H: Yükseliş trendi devam ediyor
- 4H: Golden Cross (EMA 50/200)
- 1D: RSI 65 (overbought değil)

**Smart Money Kavramları:**
- Order Block: $67,800 (destek)
- FVG: $68,200-$68,450 (hedef)
- Kill Zone: New York açılışında yükseliş

**On-chain Veriler:**
- Exchange Netflow: -2,500 BTC (çıkış)
- Whale Transactions: 15 tx > $10M
- Stablecoin Inflow: +$450M (USDT)

**Model Tahminleri:**
- Ensemble: %78.5 BUY
- LSTM: %82.1 BUY
- RL Agent: HOLD (pozisyon %60 dolu)

**Risk Yönetimi:**
- Stop Loss: $67,200 (-2.1%)
- Take Profit 1: $69,500 (+2.8%)
- Take Profit 2: $71,000 (+4.5%)
- Risk/Reward: 1:2.1

**Sonuç:**
Kısa-orta vadeli LONG pozisyon önerilebilir.
$67,800 desteği kırılırsa stratejiden çıkış yapın.

═══════════════════════════════════
```

**Bu analiz:**
- `data/reports/analysis_BTCUSDT_20250127_103000.json` olarak kaydedilir
- Web dashboard'da görüntülenebilir

---

### 7.2. Monitor Mode (Sürekli İzleme)

**15 dakikada bir otomatik analiz:**
```bash
python -m backend.cli monitor \
  --symbols BTCUSDT \
  --freq 15m \
  --alert-discord https://discord.com/api/webhooks/your-webhook
```

**Çıktı:**
```
🔔 Monitor Mode Started
Symbol: BTCUSDT
Frequency: 15 minutes
Alert: Discord webhook

[10:30] ✅ Analysis completed - NEUTRAL
[10:45] ✅ Analysis completed - NEUTRAL
[11:00] 🚨 ALERT! Signal changed: NEUTRAL → BUY
        Reason: Golden Cross on 1H
        Discord notification sent ✅
[11:15] ✅ Analysis completed - BUY
...
```

**Durdurma:** `Ctrl+C`

---

## 8. Backtest Yapma

**Stratejinizi tarihsel verilerle test edin.**

### 8.1. Basit Backtest

```bash
python -m backend.backtest.backtest_engine run \
  --strategy ensemble \
  --symbol BTCUSDT \
  --start 2023-01-01 \
  --end 2024-12-31 \
  --capital 10000
```

**Çıktı:**
```
📊 Backtest Engine
Strategy: Ensemble Model
Symbol: BTCUSDT
Period: 2023-01-01 → 2024-12-31
Initial Capital: $10,000

⏳ Running backtest...
  ✅ 8760 candles processed
  ✅ 342 trades executed

═══════════════════════════════════
📈 BACKTEST RESULTS
═══════════════════════════════════

Performance:
  Final Capital: $18,732
  Total Return: +87.3%
  Annualized Return: +87.3%
  Sharpe Ratio: 2.1
  Sortino Ratio: 3.2
  Max Drawdown: -12.7%
  Calmar Ratio: 6.9

Trading:
  Total Trades: 342
  Wins: 198 (57.9%)
  Losses: 144 (42.1%)
  Avg Win: $127.45
  Avg Loss: -$68.32
  Win/Loss Ratio: 1.87
  Profit Factor: 2.34

Risk:
  Max Consecutive Wins: 12
  Max Consecutive Losses: 7
  Avg Trade Duration: 25.4 hours
  Best Trade: +$892.15
  Worst Trade: -$234.67

✅ Backtest completed
💾 Report: data/backtests/ensemble_BTCUSDT_20250127.json
📊 Charts: data/backtests/ensemble_BTCUSDT_20250127_charts.html
```

**HTML dosyasını tarayıcıda açın:**
```powershell
# PowerShell'de:
start data/backtests/ensemble_BTCUSDT_20250127_charts.html
```

→ İnteraktif grafikler göreceksiniz (equity curve, drawdown, trades).

---

### 8.2. Gelişmiş Backtest (Parametre Optimizasyonu)

```bash
python -m backend.backtest.optimizer \
  --strategy ensemble \
  --symbol BTCUSDT \
  --params "stop_loss:[0.01,0.02,0.03],take_profit:[0.02,0.03,0.04]" \
  --metric sharpe_ratio
```

**Çıktı:**
```
🔍 Parameter Optimization
Strategy: Ensemble
Metric: Sharpe Ratio

⏳ Testing 9 parameter combinations...
  [1/9] stop_loss=0.01, take_profit=0.02 → Sharpe: 1.8
  [2/9] stop_loss=0.01, take_profit=0.03 → Sharpe: 2.1 ⭐
  [3/9] stop_loss=0.01, take_profit=0.04 → Sharpe: 2.0
  ...

✅ Best parameters:
  stop_loss: 0.01 (1%)
  take_profit: 0.03 (3%)
  Sharpe Ratio: 2.1
```

---

## 9. Sistemi Durdurma ve Yönetme

### 9.1. Container'ları Durdurma

**Geçici durdurma (veriler kaybolmaz):**
```powershell
docker-compose stop
```

**Tekrar başlatma:**
```powershell
docker-compose start
```

---

### 9.2. Container'ları Tamamen Silme

**Container'ları sil (veriler kalır):**
```powershell
docker-compose down
```

**Container'ları + veriyi sil:**
```powershell
docker-compose down -v
```
⚠️ **DİKKAT:** Bu komut PostgreSQL ve Redis verilerini de siler!

---

### 9.3. Logları İzleme

**Tüm container logları:**
```powershell
docker-compose logs -f
```

**Sadece backend logları:**
```powershell
docker-compose logs -f backend
```

**Sadece celery worker:**
```powershell
docker-compose logs -f celery_worker
```

**Durdurma:** `Ctrl+C`

---

### 9.4. Container İçinde Komut Çalıştırma

**Backend shell:**
```powershell
docker-compose exec backend bash
```

**PostgreSQL shell:**
```powershell
docker-compose exec postgres psql -U sigma_user -d sigma_db
```

**Redis CLI:**
```powershell
docker-compose exec redis redis-cli
```

---

## 10. Sorun Giderme

### 10.1. "Port already in use" Hatası

**Hata:**
```
ERROR: for sigma_backend  Cannot start service backend: Ports are not available: listen tcp 0.0.0.0:8000: bind: An attempt was made to access a socket in a way forbidden by its access permissions.
```

**Çözüm:**
```powershell
# Port'u kullanan işlemi bulun:
netstat -ano | findstr :8000

# Çıktı:
#   TCP    0.0.0.0:8000    0.0.0.0:0    LISTENING    12345

# İşlemi öldürün:
taskkill /PID 12345 /F
```

---

### 10.2. Container Başlamıyor

**Kontrol:**
```powershell
docker-compose ps
```

**Eğer `Exit 1` görüyorsanız:**
```powershell
# Logları kontrol edin:
docker-compose logs backend
```

**Çözüm:**
- `.env` dosyasını kontrol edin (şifre/API key)
- `docker-compose restart` deneyin

---

### 10.3. GPU Tanınmıyor

**Kontrol:**
```powershell
docker-compose exec backend python -c "import torch; print(torch.cuda.is_available())"
```

**Eğer `False` ise:**
1. NVIDIA Driver güncel mi? → `nvidia-smi` kontrol edin
2. Docker Desktop → Settings → Resources → WSL Integration → Ubuntu açık mı?
3. NVIDIA Container Toolkit kurulu mu?

**NVIDIA Container Toolkit kurulumu (WSL içinde):**
```bash
# WSL terminal'de:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

### 10.4. PostgreSQL Bağlantı Hatası

**Hata:**
```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Çözüm:**
```powershell
# PostgreSQL container'ı çalışıyor mu?
docker-compose ps postgres

# Çalışmıyorsa:
docker-compose restart postgres

# Logları kontrol edin:
docker-compose logs postgres
```

---

### 10.5. API Anahtarı Geçersiz

**Hata:**
```
anthropic.AuthenticationError: API key is invalid
```

**Çözüm:**
1. `.env` dosyasını kontrol edin
2. API key doğru kopyalandı mı?
3. API key aktif mi? (Anthropic Console'da kontrol edin)
4. Container'ları yeniden başlatın:
   ```powershell
   docker-compose restart
   ```

---

### 10.6. Disk Doldu

**Docker image'ları çok yer kaplar.**

**Temizlik:**
```powershell
# Kullanılmayan image'ları sil:
docker image prune -a

# Kullanılmayan volume'ları sil:
docker volume prune

# Herşeyi temizle (DİKKAT!):
docker system prune -a --volumes
```

---

## 📚 Sık Kullanılan Komutlar (Cheat Sheet)

```powershell
# === Başlatma/Durdurma ===
docker-compose up -d          # Başlat (arka planda)
docker-compose stop           # Durdur
docker-compose start          # Devam et
docker-compose restart        # Yeniden başlat
docker-compose down           # Sil (veri kalır)
docker-compose down -v        # Sil (veri de silinir)

# === Durum Kontrol ===
docker-compose ps             # Container'lar
docker-compose logs -f        # Tüm loglar
docker-compose logs -f backend # Sadece backend

# === Container'a Bağlanma ===
docker-compose exec backend bash           # Backend shell
docker-compose exec postgres psql -U sigma_user -d sigma_db  # PostgreSQL
docker-compose exec redis redis-cli        # Redis

# === Analiz ===
docker-compose exec backend python -m backend.cli analyze --symbols BTCUSDT --mode oneshot
docker-compose exec backend python -m backend.cli monitor --symbols BTCUSDT --freq 15m

# === Backtest ===
docker-compose exec backend python -m backend.backtest.backtest_engine run --strategy ensemble --symbol BTCUSDT --start 2023-01-01 --end 2024-12-31

# === Model Eğitimi ===
docker-compose exec backend python -m backend.models.train --data data/features/BTCUSDT_1h_features.parquet --model ensemble --device cuda
```

---

## 🎯 Sonraki Adımlar

1. ✅ Docker kuruldu
2. ✅ Sistem çalışıyor
3. ✅ API anahtarları ayarlandı
4. ✅ Model eğitildi
5. ✅ Analiz yapıldı

**Şimdi ne yapabilirsiniz?**
- 🔄 **Monitor mode** başlatın (sürekli izleme)
- 📊 **Backtest** ile stratejinizi test edin
- 📚 **PDF RAG** ile trading kitaplarından öğretin
- 🎨 **Web dashboard** ekleyin (frontend klasöründe)

---

## 🆘 Yardım

**Hâlâ sorun mu var?**
- GitHub Issues: https://github.com/your-repo/issues
- Email: support@example.com
- Discord: https://discord.gg/your-server

---

**Made with 🧠 and 📊 for smarter crypto trading**
