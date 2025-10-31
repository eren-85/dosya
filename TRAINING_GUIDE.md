# 🎓 SİGMA ANALYST - ML MODEL EĞİTİM KILAVUZU

Bu kılavuz, Sigma Analyst sistemindeki tüm ML modellerini sıfırdan nasıl eğiteceğinizi adım adım anlatır.

---

## 📋 İÇİNDEKİLER

1. [Sistem Gereksinimleri](#1-sistem-gereksinimleri)
2. [Veri Hazırlama](#2-veri-hazırlama)
3. [LSTM Eğitimi](#3-lstm-eğitimi)
4. [XGBoost Eğitimi](#4-xgboost-eğitimi)
5. [PPO (RL) Eğitimi](#5-ppo-rl-eğitimi)
6. [Model Değerlendirme](#6-model-değerlendirme)
7. [Production'a Alma](#7-productiona-alma)

---

## 1. SİSTEM GEREKSİNİMLERİ

### Donanım
- **Minimum**: 16GB RAM, 4 core CPU
- **Önerilen**: 32GB RAM, 8 core CPU, NVIDIA GPU (4GB+ VRAM)

### Yazılım
```bash
# Python paketleri
pip install torch torchvision  # PyTorch
pip install pandas numpy scikit-learn
pip install xgboost lightgbm
pip install stable-baselines3  # RL için
pip install ta-lib pandas-ta  # Teknik indikatörler
pip install tqdm joblib
```

---

## 2. VERİ HAZIR

LAMA

### 2.1 Geçmiş Veri İndirme

```bash
# Tek sembol
python download_data.py BTCUSDT 1h futures

# Çoklu sembol
python download_data.py BTCUSDT,ETHUSDT,BNBUSDT 1h futures

# Farklı timeframe'ler
python download_data.py BTCUSDT 1h futures
python download_data.py BTCUSDT 4h futures
python download_data.py BTCUSDT 1d futures
```

**Sonuç**: `data/historical/` klasöründe `.parquet` dosyaları oluşur.

### 2.2 Veri Kalitesi Kontrolü

```bash
# Veri kontrolü
python -m backend.tools.check_data --symbol BTCUSDT --timeframe 1h
```

**Kontrol edilen:**
- Eksik veri (gaps)
- Outlier'lar (anormal mumlar)
- Veri tutarlılığı

---

## 3. LSTM EĞİTİMİ

### 3.1 Temel Eğitim (Başlangıç)

```bash
# 100 epoch ile basit eğitim
python -m backend.training.train_lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --epochs 100 \
    --batch-size 32 \
    --seq-length 60
```

**Beklenen çıktı**:
```
📂 Loading data from data/historical/BTCUSDT_1h_futures.parquet
✅ Loaded 50,000 candles
🔧 Calculating technical indicators...
📊 Using 45 features
🔄 Creating sequences (lookback=60)...
✅ Created 49,940 sequences

🚀 Starting training for 100 epochs...
Epoch  10/100 | Train Loss: 0.6521 Acc: 0.612 | Val Loss: 0.6489 Acc: 0.608
Epoch  20/100 | Train Loss: 0.6012 Acc: 0.658 | Val Loss: 0.6145 Acc: 0.649
...
Epoch 100/100 | Train Loss: 0.4823 Acc: 0.765 | Val Loss: 0.5234 Acc: 0.741

✅ Training complete! Best val loss: 0.5234
💾 Model saved: models/trained/lstm_BTCUSDT_1h_20250131_143022.pt
```

### 3.2 İleri Düzey Eğitim

```bash
# Daha büyük model, daha fazla epoch
python -m backend.training.train_lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --epochs 200 \
    --batch-size 64 \
    --seq-length 120 \
    --hidden-size 256 \
    --num-layers 3 \
    --lr 0.0005
```

**Ne zaman kullanılır**:
- Daha fazla veri varsa (100k+ candle)
- GPU varsa
- Daha yüksek accuracy istiyorsanız

### 3.3 Hyperparameter Tuning

```bash
# Grid search ile en iyi parametreleri bul
python -m backend.training.tune_lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --trials 50
```

**Optimize edilen parametreler**:
- `hidden_size`: [64, 128, 256, 512]
- `num_layers`: [1, 2, 3, 4]
- `dropout`: [0.1, 0.2, 0.3, 0.5]
- `learning_rate`: [0.0001, 0.0005, 0.001, 0.01]
- `seq_length`: [30, 60, 120, 240]

---

## 4. XGBOOST EĞİTİMİ

### 4.1 Pattern Classification

```bash
# Pattern tanıma için XGBoost
python -m backend.training.train_xgboost \
    --symbol BTCUSDT \
    --timeframe 1h \
    --task pattern_classification \
    --n-estimators 500
```

**Öğrenilen pattern'ler**:
- Head & Shoulders
- Double Top/Bottom
- Triangles
- Flags & Pennants
- Engulfing candles

### 4.2 Trend Classification

```bash
# Trend sınıflandırma (uptrend/downtrend/sideways)
python -m backend.training.train_xgboost \
    --symbol BTCUSDT \
    --timeframe 4h \
    --task trend_classification \
    --n-estimators 300
```

---

## 5. PPO (RL) EĞİTİMİ

### 5.1 Temel RL Eğitimi

```bash
# Reinforcement Learning agent
python -m backend.training.train_ppo \
    --symbol BTCUSDT \
    --timeframe 1h \
    --total-timesteps 100000 \
    --learning-rate 0.0003
```

**Eğitim süreci**:
```
Episode 100 | Reward: +12.4 | Equity: $10,240
Episode 200 | Reward: +24.8 | Equity: $10,520
Episode 500 | Reward: +58.2 | Equity: $11,180
...
Episode 5000 | Reward: +456.7 | Equity: $15,670

✅ Training complete!
💾 Model saved: models/trained/ppo_BTCUSDT_1h_20250131.zip
```

### 5.2 Reward Shaping

```python
# Custom reward function
# backend/training/train_ppo.py içinde düzenle

def calculate_reward(self, action, prev_equity, curr_equity):
    """
    Custom reward function
    """
    # 1. PnL reward
    pnl = (curr_equity - prev_equity) / prev_equity
    pnl_reward = pnl * 100

    # 2. Risk penalty
    if self.drawdown > 0.15:  # 15% DD
        risk_penalty = -10
    else:
        risk_penalty = 0

    # 3. Trade frequency penalty (avoid overtrading)
    if self.trades_today > 5:
        freq_penalty = -5
    else:
        freq_penalty = 0

    # 4. Sharpe ratio bonus
    if self.sharpe_ratio > 2.0:
        sharpe_bonus = +5
    else:
        sharpe_bonus = 0

    # Total reward
    total_reward = pnl_reward + risk_penalty + freq_penalty + sharpe_bonus

    return total_reward
```

---

## 6. MODEL DEĞERLENDİRME

### 6.1 Backtest

```bash
# Eğitilmiş modeli backtest et
python -m backend.backtest.run_backtest \
    --model models/trained/lstm_BTCUSDT_1h.pt \
    --start-date 2024-01-01 \
    --end-date 2025-01-01 \
    --initial-capital 10000
```

**Çıktı**:
```
📊 BACKTEST RESULTS
=====================================
Period: 2024-01-01 to 2025-01-01
Initial Capital: $10,000
Final Equity: $15,670

Performance Metrics:
  Total Return: +56.7%
  Max Drawdown: -12.3%
  Sharpe Ratio: 2.14
  Win Rate: 64.5%
  Profit Factor: 2.31
  Total Trades: 247
  Avg Trade Duration: 14.2 hours

✅ Model performance: EXCELLENT
```

### 6.2 Walk-Forward Analysis

```bash
# Gerçekçi test (overfit kontrolü)
python -m backend.backtest.walk_forward \
    --model-type lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --train-window 180 \  # 180 gün train
    --test-window 30      # 30 gün test
```

**Walk-Forward nasıl çalışır**:
```
Train: Day 1-180   → Test: Day 181-210
Train: Day 31-210  → Test: Day 211-240
Train: Day 61-240  → Test: Day 241-270
...

Ortalama Test Performance:
  Return: +42.3%
  Sharpe: 1.89
  Win Rate: 61.2%

✅ Model stabil ve güvenilir
```

---

## 7. PRODUCTION'A ALMA

### 7.1 Model Deploy

```bash
# Modeli production klasörüne kopyala
cp models/trained/lstm_BTCUSDT_1h_20250131.pt \
   models/production/lstm_btc_1h.pt

# Backend'i restart et
docker-compose restart backend
```

### 7.2 API Test

```bash
# Prediction API'yi test et
curl -X POST http://localhost:8000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "model": "lstm"
  }'
```

**Beklenen response**:
```json
{
  "signal": "LONG",
  "confidence": 0.78,
  "probability": 0.78,
  "entry_price": 43250.50,
  "stop_loss": 42100.00,
  "take_profit": 44500.00,
  "risk_reward": 2.5,
  "reasoning": "LSTM uptrend probability 78%, RSI oversold (32), Price at Fibonacci 0.618 support"
}
```

---

## 8. SORUN GİDERME

### 8.1 Düşük Accuracy

**Sorun**: Model accuracy %50-55 civarında (şans seviyesi)

**Çözümler**:
1. **Daha fazla veri**: 50k+ candle kullan
2. **Daha fazla feature**: Daha çok indikatör ekle
3. **Daha uzun sequence**: `--seq-length 120` dene
4. **Hyperparameter tuning**: Grid search çalıştır
5. **Ensemble**: Birden fazla model kombine et

### 8.2 Overfitting

**Sorun**: Train acc %90, Val acc %55

**Çözümler**:
1. **Dropout artır**: `--dropout 0.3` veya `0.5`
2. **Regularization**: L2 penalty ekle
3. **Early stopping**: Validation loss artarsa dur
4. **Daha az layer**: `--num-layers 2` yerine `1`
5. **Data augmentation**: Add noise to training data

### 8.3 Yavaş Eğitim

**Sorun**: 1 epoch 30+ dakika sürüyor

**Çözümler**:
1. **GPU kullan**: CUDA etkinleştir
2. **Batch size artır**: `--batch-size 128`
3. **Veri azalt**: Son 1 yıl yerine 6 ay kullan
4. **Model küçült**: `--hidden-size 64`

---

## 9. İLERİ SEVİYE

### 9.1 Multi-Timeframe Model

```bash
# Aynı anda 3 timeframe'den öğren
python -m backend.training.train_multi_timeframe \
    --symbol BTCUSDT \
    --timeframes 1h,4h,1d \
    --epochs 150
```

### 9.2 Multi-Asset Model

```bash
# 5 farklı coin'den öğren
python -m backend.training.train_multi_asset \
    --symbols BTCUSDT,ETHUSDT,BNBUSDT,SOLUSDT,ADAUSDT \
    --timeframe 1h \
    --epochs 200
```

### 9.3 Transfer Learning

```bash
# BTC'den öğrenileni ETH'ye transfer et
python -m backend.training.transfer_learning \
    --source-model models/trained/lstm_BTCUSDT_1h.pt \
    --target-symbol ETHUSDT \
    --timeframe 1h \
    --epochs 50  # Fine-tuning için az epoch yeter
```

---

## 10. BEST PRACTICES

### ✅ Yapılması Gerekenler

1. **Veriyi split et**: Train/Val/Test (70/15/15)
2. **Shuffle YAPMA**: Time series için sıra önemli
3. **Scale et**: StandardScaler veya MinMaxScaler kullan
4. **Cross-validation**: Walk-forward kullan
5. **Log tut**: Her eğitimi kaydet
6. **Version control**: Modelleri git'te takip et
7. **Monitor et**: TensorBoard kullan

### ❌ Yapılmaması Gerekenler

1. **Overfit etme**: Validation izle
2. **Future data leak etme**: Shift doğru kullan
3. **Aşırı optimize etme**: Backtest'te mükemmel ama live'da kötü
4. **Tek metric izleme**: Accuracy + Sharpe + DD kombine bak
5. **Random seed unutma**: Reproducible results için seed fix et

---

## 11. ÖNERİLEN EĞİTİM TAKVİMİ

### Gün 1: Veri Hazırlama
- ✅ Historical data indir (1-2 yıl)
- ✅ Veri kalitesi kontrol et
- ✅ Feature engineering yap

### Gün 2-3: LSTM Eğitimi
- ✅ Baseline model eğit (100 epoch)
- ✅ Hyperparameter tune et
- ✅ En iyi modeli seç

### Gün 4: XGBoost Eğitimi
- ✅ Pattern classification
- ✅ Trend classification
- ✅ Feature importance analiz et

### Gün 5-7: PPO (RL) Eğitimi
- ✅ Environment kur
- ✅ Reward function ayarla
- ✅ 100k timestep eğit
- ✅ Backtest et

### Gün 8: Ensemble & Integration
- ✅ Tüm modelleri kombine et
- ✅ Voting/Stacking yap
- ✅ Son backtest

### Gün 9: Production Deploy
- ✅ API entegrasyonu
- ✅ Live test (paper trading)
- ✅ Monitoring kur

### Gün 10: Monitoring & Improvement
- ✅ Live performance izle
- ✅ A/B testing
- ✅ Retrain planla

---

## 12. YARDIM & DESTEK

### Loglar
```bash
# Training log
tail -f logs/training.log

# Error log
tail -f logs/error.log
```

### Debug Mode
```bash
# Verbose output ile çalıştır
python -m backend.training.train_lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --epochs 10 \
    --verbose
```

### Test Mode
```bash
# Küçük veri ile hızlı test
python -m backend.training.train_lstm \
    --symbol BTCUSDT \
    --timeframe 1h \
    --epochs 5 \
    --test-mode
```

---

## 📞 İLETİŞİM

Sorunlar için:
- GitHub Issues: https://github.com/your-repo/issues
- Discord: https://discord.gg/your-channel
- Email: support@sigmaanalyst.com

---

## 🎉 BAŞARILAR!

Artık Sigma Analyst'ı kendi verilerinle eğitmeye hazırsın!

İyi eğitimler! 🚀
