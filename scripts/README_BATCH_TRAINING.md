# Multi-Everything Batch Training System

Bu sistem sayesinde **toplu veri indirme** ve **toplu model eğitimi** yapabilirsiniz.

## 🎯 Özellikler

- ✅ **Multi-Coin**: 10+ coin aynı anda
- ✅ **Multi-Timeframe**: 1h, 4h, 1d
- ✅ **Multi-Market**: Spot + Futures
- ✅ **Multi-Exchange**: Binance + Bybit
- ✅ **Multi-Model**: PPO, Ensemble, LSTM
- ✅ **Auto-Parallel**: Her task paralel çalışır
- ✅ **Progress Tracking**: Her adımda progress

## 📦 Dosyalar

```
scripts/
├── download_all.py          # Toplu veri indirme
├── train_all.py             # Toplu model eğitimi
├── config_example.json      # Örnek config
└── README_BATCH_TRAINING.md # Bu dosya
```

## 🚀 Kullanım

### 1. Toplu Veri İndirme

```bash
# Docker içinde çalıştır
docker-compose exec backend python scripts/download_all.py
```

**Ne yapar?**
- Tüm coin'leri indirir (BTCUSDT, ETHUSDT, BNBUSDT, etc.)
- Tüm timeframe'leri indirir (1h, 4h, 1d)
- Tüm market type'ları indirir (spot, futures)
- Paralel download (3 worker)
- Progress gösterir
- Summary raporu verir

**Çıktı:**
```
data/advanced/
├── BTCUSDT_1h_spot_multi.parquet
├── BTCUSDT_1h_futures_multi.parquet
├── BTCUSDT_4h_spot_multi.parquet
├── BTCUSDT_4h_futures_multi.parquet
├── ETHUSDT_1h_spot_multi.parquet
├── ETHUSDT_1h_futures_multi.parquet
└── ...
```

### 2. Toplu Model Eğitimi

```bash
# Docker içinde çalıştır
docker-compose exec backend python scripts/train_all.py
```

**Ne yapar?**
- Tüm indirilen veriyi bulur
- Her market için ayrı model eğitir (spot vs futures)
- Her timeframe için ayrı model eğitir (1h vs 4h vs 1d)
- Her model type'ı eğitir (PPO, Ensemble, LSTM)
- GPU kullanır (CUDA)
- Progress gösterir
- Model karşılaştırma raporu verir

**Çıktı:**
```
data/models/
├── spot_1h_ppo.pkl
├── spot_1h_ensemble.pkl
├── spot_1h_lstm.pkl
├── futures_1h_ppo.pkl
├── futures_1h_ensemble.pkl
├── futures_1h_lstm.pkl
└── ...
```

## ⚙️ Konfigürasyon

### download_all.py İçinde Düzenle

```python
CONFIGS = {
    "symbols": [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        # Daha fazla ekle...
    ],

    "timeframes": [
        "1h",
        "4h",
        "1d",
    ],

    "markets": [
        "spot",
        "futures",
    ],

    "exchanges": ["binance", "bybit"],

    "start_date": "auto",  # veya "2024-01-01"

    "max_workers": 3,  # Paralel download worker sayısı
}
```

### train_all.py İçinde Düzenle

```python
CONFIGS = {
    "models": [
        "ppo",      # Reinforcement Learning
        "ensemble", # XGBoost + LightGBM + CatBoost
        "lstm",     # Bidirectional LSTM
    ],

    "epochs": {
        "ppo": 100,
        "ensemble": 100,
        "lstm": 50,
    },

    "device": "cuda",  # veya "cpu"

    # Her market için ayrı model? (spot vs futures)
    "separate_by_market": True,

    # Her timeframe için ayrı model? (1h vs 4h vs 1d)
    "separate_by_timeframe": True,
}
```

## 📊 Örnek Workflow

### Hızlı Test (3 coin, 1 timeframe)

```python
# download_all.py içinde:
CONFIGS = {
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    "timeframes": ["1h"],
    "markets": ["futures"],
    "start_date": "2024-01-01",  # Son 1 yıl
}
```

**Süre:** ~15-20 dakika

### Orta Test (5 coin, 2 timeframe)

```python
CONFIGS = {
    "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"],
    "timeframes": ["1h", "4h"],
    "markets": ["spot", "futures"],
    "start_date": "auto",  # Tüm tarihsel veri
}
```

**Süre:** ~1-2 saat

### Full Test (10 coin, 3 timeframe, 2 market)

```python
CONFIGS = {
    "symbols": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
        "XRPUSDT", "DOGEUSDT", "MATICUSDT", "DOTUSDT", "AVAXUSDT"
    ],
    "timeframes": ["1h", "4h", "1d"],
    "markets": ["spot", "futures"],
    "start_date": "auto",
}
```

**Süre:** ~3-5 saat (download) + 10-20 saat (training)

## 🎓 Eğitim Stratejileri

### Strateji 1: Market-Specific Models

```python
# train_all.py içinde:
CONFIGS = {
    "separate_by_market": True,    # spot vs futures ayrı
    "separate_by_timeframe": False, # timeframe'ler birlikte
}
```

**Sonuç:**
- `spot_ppo.pkl` (tüm spot data)
- `futures_ppo.pkl` (tüm futures data)

### Strateji 2: Timeframe-Specific Models

```python
CONFIGS = {
    "separate_by_market": False,   # market'ler birlikte
    "separate_by_timeframe": True, # timeframe'ler ayrı
}
```

**Sonuç:**
- `1h_ppo.pkl` (tüm 1h data)
- `4h_ppo.pkl` (tüm 4h data)

### Strateji 3: Hyper-Specific Models (Recommended)

```python
CONFIGS = {
    "separate_by_market": True,    # her şey ayrı
    "separate_by_timeframe": True,
}
```

**Sonuç:**
- `spot_1h_ppo.pkl`
- `spot_4h_ppo.pkl`
- `futures_1h_ppo.pkl`
- `futures_4h_ppo.pkl`
- ...

**Avantaj:** Her use case için optimize model!

## 📈 Progress Monitoring

### Download Progress

```
================================================================================
📥 Downloading: BTCUSDT, ETHUSDT, BNBUSDT | 1h | FUTURES
================================================================================
⚡ Parallel mode enabled (3 workers)...
✅ BTCUSDT complete! (54,043 rows)
✅ ETHUSDT complete! (52,133 rows)
✅ BNBUSDT complete! (48,921 rows)
✅ SUCCESS in 234.5s - 3/3 symbols
```

### Training Progress

```
================================================================================
🎓 Training PPO: futures_1h_ppo
================================================================================
📊 Data files: 5
⚙️  Epochs: 100
🖥️  Device: cuda
✅ Training complete in 45.2 minutes
```

## 🐛 Troubleshooting

### Problem: Download çok yavaş

**Çözüm:**
```python
CONFIGS = {
    "max_workers": 5,  # 3'ten 5'e çıkar
}
```

### Problem: GPU memory error

**Çözüm:**
```python
CONFIGS = {
    "device": "cpu",  # CPU kullan
    # veya
    "epochs": {"ppo": 50},  # Epoch sayısını azalt
}
```

### Problem: Timeout error

**Çözüm:**
```python
# download_all.py içinde timeout artır:
result = subprocess.run(cmd, timeout=7200)  # 2 saat
```

## 📝 Log Files

Her çalıştırma sonucu kaydedilir:

```
data/advanced/download_results_20251107_143022.json
data/models/training_results_20251107_183045.json
```

## 🎉 Sonuç

Bu sistem ile:
- ✅ 10 coin x 3 timeframe x 2 market = **60 dataset**
- ✅ 60 dataset x 3 model = **180 model** eğitebilirsin!
- ✅ Hepsi otomatik, paralel, progress tracked!

**Enjoy!** 🚀
