# GPU/CPU Usage Guide - Sigma Analyst

## RTX 4060 8GB Optimizasyon Kılavuzu

Bu kılavuz, Sigma Analyst AI Financial Analysis sisteminin RTX 4060 8GB VRAM ile optimal performans için nasıl yapılandırılacağını açıklar.

---

## 🎯 Önerilen Yapılandırma: HYBRID MODE

**RTX 4060 için en iyi seçenek:** `HYBRID` modu

```bash
# .env dosyasına ekleyin
COMPUTE_MODE=hybrid
```

### Hybrid Mode Nedir?

Hybrid mode, her iş tipine göre en uygun cihazı otomatik seçer:

| İş Tipi | Cihaz | Neden? |
|---------|-------|--------|
| **Technical Analysis** (pandas-ta, TA-Lib) | **CPU** | NumPy/pandas CPU için optimize edilmiş |
| **ML Tree Models** (XGBoost, LightGBM, CatBoost) | **CPU** | Küçük-orta veri setleri için CPU daha hızlı |
| **Deep Learning** (LSTM, Transformer) | **GPU** | 10-50x hız artışı (RTX 4060 ile) |
| **RL Training** (PPO, Decision Transformer) | **GPU** | Paralel ortam + GPU = maksimum hız |
| **Backtest** (pandas işlemleri) | **CPU** | Vektörize pandas işlemleri |

---

## 📊 Performans Karşılaştırması

### RTX 4060 8GB ile Beklenen Hızlanma:

```
Technical Analysis (200+ indicators):
  CPU: ~0.5s per 10k bars ✅
  GPU: ~0.5s per 10k bars (aynı, çünkü CPU zaten hızlı)
  ➡️ Sonuç: CPU kullan (kaynakları GPU modellerine ayır)

XGBoost/LightGBM/CatBoost:
  CPU (12 cores): ~5s training ✅
  GPU (RTX 4060): ~8s training (overhead yüzünden yavaş)
  ➡️ Sonuç: CPU kullan (küçük-orta veri setleri için)

LSTM Model (100 epochs):
  CPU: ~2000s (33 dakika) ❌
  GPU (RTX 4060): ~80s (1.3 dakika) ✅
  ➡️ Speedup: 25x

Transformer Model (100 epochs):
  CPU: ~5000s (83 dakika) ❌
  GPU (RTX 4060 + FP16): ~100s (1.7 dakika) ✅
  ➡️ Speedup: 50x

RL Training (100k timesteps):
  CPU: ~1200s (20 dakika) ❌
  GPU (RTX 4060): ~120s (2 dakika) ✅
  ➡️ Speedup: 10x

Backtest (10k bars):
  CPU (vectorized): ~0.1s ✅
  GPU: N/A (pandas operations)
  ➡️ Sonuç: CPU kullan
```

---

## 🚀 Kullanım Örnekleri

### 1. Compute Manager Başlatma

```python
from backend.config.compute_config import initialize_compute, get_compute

# Hybrid mode (ÖNERILIR)
compute = initialize_compute(mode='hybrid')

# Veya environment variable ile
# COMPUTE_MODE=hybrid python app.py
```

### 2. Ensemble ML Model (CPU)

```python
from backend.models.ensemble_model import EnsembleModel

# Otomatik olarak CPU kullanacak (hybrid modda)
model = EnsembleModel(task='regression')
model.fit(X_train, y_train, eval_set=(X_val, y_val))

# Çıktı:
# 🖥️  Ensemble using CPU for tree models
#   XGBoost: hist
#   LightGBM: cpu
#   CatBoost: CPU
```

### 3. Deep Learning (GPU)

```python
from backend.models.deep_learning import DeepLearningTrainer

# Otomatik olarak GPU kullanacak (hybrid modda)
trainer = DeepLearningTrainer(model_type='lstm')
trainer.build_model(input_size=50, seq_len=60)
trainer.fit(X_train, y_train, X_val, y_val)

# Çıktı:
# 🚀 Deep Learning Trainer (LSTM)
#    Device: cuda
#    Batch Size: 128
#    Mixed Precision (FP16): True
```

### 4. RL Agent (GPU)

```python
from backend.models.rl_agent import RLAgent

env_config = {
    'df': market_data,
    'initial_balance': 100000.0,
    'lookback_window': 60,
}

# Otomatik olarak GPU kullanacak (hybrid modda)
agent = RLAgent(env_config, n_envs=8)
agent.train(total_timesteps=100000)

# Çıktı:
# 🤖 RL Agent (PPO)
#    Device: CUDA
#    Parallel Environments: 8
```

### 5. Backtest Engine (CPU)

```python
from backend.backtest.backtest_engine import BacktestEngine, BacktestConfig

config = BacktestConfig(
    initial_capital=100000.0,
    commission=0.001,
    stop_loss=0.02,
)

# Otomatik olarak CPU kullanacak (hybrid modda)
engine = BacktestEngine(config)
results = engine.run(data, signals, strategy_name="My Strategy")

# Çıktı:
# 📊 Backtest Engine
#    Device: CPU
#    Parallel: True
#    Workers: All CPUs
```

---

## ⚙️ Compute Mode Seçenekleri

### 1. HYBRID Mode (ÖNERILIR)

```python
initialize_compute(mode='hybrid')
```

**Avantajlar:**
- En iyi performans
- Her iş tipi için optimal cihaz
- GPU'yu yoğun işler için ayırır
- CPU'yu hafif işler için kullanır

**RTX 4060 için ideal!**

### 2. AUTO Mode

```python
initialize_compute(mode='auto')
```

**Davranış:**
- GPU varsa → HYBRID mode
- GPU yoksa → CPU mode

### 3. CPU Mode

```python
initialize_compute(mode='cpu')
```

**Kullanım durumları:**
- GPU yoksa
- Test amaçlı
- GPU'yu başka işlere ayırmak istiyorsanız

### 4. GPU Mode

```python
initialize_compute(mode='gpu')
```

**Dikkat:** Tree-based modeller (XGBoost, CatBoost) CPU'da daha hızlı olabilir!

**Kullanım durumları:**
- Sadece Deep Learning/RL kullanıyorsanız
- Büyük veri setleri (>1M samples)

---

## 🧠 Memory Optimization (RTX 4060 8GB)

### Mixed Precision (FP16)

Hybrid modda **otomatik aktif**:

```python
compute = get_compute()
print(compute.config.use_mixed_precision)  # True (GPU'da)
```

**Faydaları:**
- 2x daha az VRAM kullanımı
- 1.5-2x daha hızlı eğitim
- RTX 4060 Tensor Core'ları kullanır

### Batch Size Optimization

RTX 4060 8GB için **otomatik optimize ediliyor**:

```python
compute = get_compute()
print(compute.config.dl_batch_size)  # 128 (RTX 4060 için)
```

**VRAM'e göre otomatik ayar:**
- 8GB+ VRAM → Batch size 128
- 6-8GB VRAM → Batch size 64
- <6GB VRAM → Batch size 32

### Memory Cleanup

```python
compute = get_compute()
compute.optimize_memory()  # GPU cache'i temizle
```

**Otomatik çalışır:**
- Model eğitimi sonrası
- Büyük işlem bitiminde

### Memory Statistics

```python
compute = get_compute()
stats = compute.get_memory_stats()

print(f"Total VRAM: {stats['total_gb']:.1f} GB")
print(f"Used VRAM: {stats['allocated_gb']:.1f} GB")
print(f"Free VRAM: {stats['free_gb']:.1f} GB")
print(f"Utilization: {stats['utilization_percent']:.1f}%")

# Örnek çıktı:
# Total VRAM: 8.0 GB
# Used VRAM: 3.2 GB
# Free VRAM: 4.8 GB
# Utilization: 40.0%
```

---

## 🔧 Environment Variables

`.env` dosyasına ekleyebilirsiniz:

```bash
# Compute mode
COMPUTE_MODE=hybrid  # hybrid, auto, cpu, gpu

# Logging
LOG_LEVEL=INFO
```

---

## 📈 RTX 4060 için Best Practices

### ✅ Yapılması Gerekenler:

1. **Hybrid mode kullan** - En iyi performans
2. **Mixed precision aktif** - Otomatik (FP16)
3. **Batch size optimize** - Otomatik (128)
4. **Memory cleanup** - Otomatik
5. **Parallel environments (RL)** - 8 env optimal

### ❌ Yapılmaması Gerekenler:

1. **Tree models GPU'da çalıştırma** - CPU daha hızlı (küçük data)
2. **Çok büyük batch size** - VRAM taşması
3. **Multiple models aynı anda GPU'da** - VRAM tükenir
4. **Technical analysis GPU'da** - CPU zaten hızlı

---

## 🎯 Örnek Workflow

### Tam Analiz Pipeline (Hybrid Mode)

```python
from backend.config.compute_config import initialize_compute
from backend.models.ensemble_model import EnsembleModel
from backend.models.deep_learning import DeepLearningTrainer
from backend.models.rl_agent import RLAgent
from backend.backtest.backtest_engine import BacktestEngine

# 1. Initialize compute
compute = initialize_compute(mode='hybrid')

# 2. Technical Analysis (CPU - pandas-ta)
# 200+ indicators calculated on CPU (fast)
indicators = calculate_indicators(data)  # ~0.5s for 10k bars

# 3. ML Ensemble (CPU - XGBoost, LightGBM, CatBoost)
# Tree models trained on CPU (faster for medium data)
ml_model = EnsembleModel()
ml_model.fit(X_train, y_train)  # ~5s training

# 4. Deep Learning (GPU - LSTM)
# LSTM trained on GPU with FP16 (50x faster)
dl_trainer = DeepLearningTrainer(model_type='lstm')
dl_trainer.build_model(input_size=50)
dl_trainer.fit(X_train, y_train, X_val, y_val)  # ~80s (vs 2000s CPU)

# 5. RL Training (GPU - PPO)
# RL agent trained on GPU (10x faster)
rl_agent = RLAgent(env_config, n_envs=8)
rl_agent.train(total_timesteps=100000)  # ~120s (vs 1200s CPU)

# 6. Backtest (CPU - vectorized pandas)
# Backtest runs on CPU (optimized for pandas)
engine = BacktestEngine()
results = engine.run(data, signals)  # ~0.1s for 10k bars

# Total time: ~210s (CPU-only: ~3600s)
# Speedup: 17x
```

---

## 📊 Performans İzleme

### TensorBoard (Deep Learning)

```bash
tensorboard --logdir=./logs/tensorboard/
```

### GPU Monitoring

```bash
# Terminal 1: Training script
python train.py

# Terminal 2: GPU monitoring
nvidia-smi -l 1  # 1 saniye refresh
```

**İdeal RTX 4060 kullanımı:**
- GPU Utilization: 90-100%
- Memory Usage: 60-80% (4-6GB/8GB)
- Temperature: <80°C
- Power: 80-100W (100W TDP)

---

## 🆘 Troubleshooting

### Problem 1: CUDA Out of Memory

**Çözüm:**
```python
# Batch size'ı azalt
trainer.config.batch_size = 64  # 128 yerine

# Veya model boyutunu küçült
model = LSTMModel(hidden_size=128)  # 256 yerine
```

### Problem 2: GPU kullanılmıyor

**Kontrol:**
```python
import torch
print(torch.cuda.is_available())  # True olmalı
print(torch.cuda.get_device_name(0))  # "NVIDIA GeForce RTX 4060 ..."
```

**Çözüm:**
- CUDA 13.0 kurulu mu kontrol et
- PyTorch GPU version mu kontrol et: `pip install torch --index-url https://download.pytorch.org/whl/cu121`

### Problem 3: Yavaş eğitim

**Kontrol:**
```python
compute = get_compute()
print(compute.config.use_mixed_precision)  # True olmalı
print(compute.config.dl_batch_size)  # 128 olmalı (RTX 4060)
```

---

## 📚 İleri Seviye

### Custom Device Selection

```python
from backend.config.compute_config import get_compute

compute = get_compute()

# Deep Learning için GPU
dl_device = compute.get_torch_device('dl')  # cuda

# ML için CPU
ml_device = compute.get_torch_device('ml')  # cpu

# XGBoost parametreleri
xgb_params = compute.get_xgboost_params()
# {'tree_method': 'hist', 'n_jobs': -1}

# CatBoost parametreleri
cat_params = compute.get_catboost_params()
# {'task_type': 'CPU', 'thread_count': None}
```

### Multiple GPU Support (gelecek)

Şu an tek GPU destekleniyor (RTX 4060). Multi-GPU desteği gelecek versiyonlarda eklenecek.

---

## 🎓 Sonuç

**RTX 4060 8GB için en iyi yapılandırma:**

```python
# .env
COMPUTE_MODE=hybrid

# Python
from backend.config.compute_config import initialize_compute
compute = initialize_compute(mode='hybrid')
```

**Bu yapılandırma ile:**
- ✅ Technical Analysis → CPU (hızlı)
- ✅ ML Tree Models → CPU (optimal)
- ✅ Deep Learning → GPU + FP16 (25-50x hızlanma)
- ✅ RL Training → GPU (10x hızlanma)
- ✅ Backtest → CPU (vektörize)

**Toplam performans artışı:** 15-20x (CPU-only'ye göre)

**VRAM kullanımı:** 3-6GB (8GB içinde güvenli)

---

## 📞 Destek

Sorularınız için:
- GitHub Issues
- Dokümantasyon: `/docs`
- Örnekler: `/examples`
