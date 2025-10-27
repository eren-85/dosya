# PyTorch GPU Optimizasyon Rehberi

## 🚀 İleri Seviye GPU Ayarları

Bu kılavuz PyTorch'un GPU performansını ve stabilitesini artırmak için environment variable'lar ve en iyi pratikleri içerir.

---

## 1️⃣ PYTORCH_CUDA_ALLOC_CONF (Memory Allocator)

### Nedir?

PyTorch'un CUDA memory allocator'ının davranışını kontrol eder.

### Tavsiye Edilen Ayar (RTX 4060 için):

```powershell
# Windows PowerShell
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True,max_split_size_mb:128"

# Linux/Mac Bash
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True,max_split_size_mb:128"

# Python içinde (script başında)
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True,max_split_size_mb:128'
```

### Parametreler:

#### `expandable_segments:True`

**Ne yapar?**
- Memory segment'leri dinamik olarak genişletir
- Fragmentation'ı azaltır
- OOM (Out of Memory) riskini düşürür

**Neden kullanmalı?**
- ✅ Daha az memory fragmentation
- ✅ Daha iyi memory utilization
- ✅ OOM hatalarını önler

**Trade-off:**
- ⚠️ İlk allocation biraz daha yavaş (~10ms)
- ✅ Ama training sırasında çok daha stabil

#### `max_split_size_mb:128`

**Ne yapar?**
- Memory block'larının maksimum split size'ı (MB)
- Küçük değer = daha az fragmentation
- Büyük değer = daha az overhead

**128 MB neden ideal?**
- ✅ RTX 4060 8GB için optimal
- ✅ Batch size 112-128 ile uyumlu
- ✅ Fragmentation vs overhead dengesi

**Diğer değerler:**
```
max_split_size_mb:64   → 6GB veya daha az VRAM için
max_split_size_mb:128  → 8GB VRAM için (ÖNERILIR)
max_split_size_mb:256  → 12GB+ VRAM için
max_split_size_mb:512  → 24GB+ VRAM için
```

---

## 2️⃣ Kalıcı Ayar (Windows)

### PowerShell Profile (.ps1):

```powershell
# PowerShell profilinizi açın
notepad $PROFILE

# Ekleyin:
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True,max_split_size_mb:128"

# Kaydedin ve yeni terminal açın
```

### System Environment Variables:

1. Windows Arama → "Environment Variables"
2. "New" → Variable name: `PYTORCH_CUDA_ALLOC_CONF`
3. Variable value: `expandable_segments:True,max_split_size_mb:128`
4. OK → Terminali yeniden başlat

---

## 3️⃣ Diğer Faydalı Environment Variables

### CUDA_LAUNCH_BLOCKING (Debug için)

```powershell
# Asynchronous CUDA operations'ı senkron yapar
# Sadece DEBUG için kullan (yavaşlatır!)
$env:CUDA_LAUNCH_BLOCKING = "1"
```

**Ne zaman kullanılır:**
- ❌ Training sırasında KULLANMA (çok yavaş)
- ✅ Error debug ederken kullan
- ✅ Hangi operation'da OOM olduğunu bulmak için

### PYTORCH_NO_CUDA_MEMORY_CACHING (Debug için)

```powershell
# Memory caching'i devre dışı bırakır
# Sadece DEBUG için!
$env:PYTORCH_NO_CUDA_MEMORY_CACHING = "1"
```

**Ne zaman kullanılır:**
- ❌ Asla normal training'de kullanma
- ✅ Memory leak debug için

---

## 4️⃣ DataLoader Optimizasyonları (Windows)

### Tavsiye Edilen Ayarlar:

```python
from torch.utils.data import DataLoader

loader = DataLoader(
    dataset,
    batch_size=112,  # RTX 4060 için optimal
    num_workers=2,   # Windows için 2-4 (spawn overhead)
    pin_memory=True, # GPU için MUTLAKA True
    persistent_workers=True,  # Workers'ı cache'le (daha hızlı)
)
```

### Parametreler:

#### `num_workers` (Windows için)

**Optimal değer: 2-4**

```python
# Windows spawn maliyeti yüksek
num_workers=0  # ❌ Yavaş (main process'te load)
num_workers=2  # ✅ İyi (2 parallel worker)
num_workers=4  # ✅ Optimal (4 parallel worker)
num_workers=8  # ⚠️ Overhead fazla (diminishing returns)
```

**Neden 2-4?**
- Windows multiprocessing `spawn` kullanır (Linux `fork` kullanır)
- Spawn daha yavaş (her worker full process copy)
- 4'ten fazla worker → overhead > benefit

#### `pin_memory=True` (GPU için MUTLAKA)

**Ne yapar?**
- CPU memory'yi pinned (page-locked) yapar
- GPU transfer 2-3x daha hızlı
- Özellikle büyük batch'lerde kritik

**Neden True olmalı?**
```python
pin_memory=False:
  CPU → GPU transfer: ~2.5 GB/s ❌

pin_memory=True:
  CPU → GPU transfer: ~6-8 GB/s ✅ (2.5x faster)
```

#### `persistent_workers=True` (PyTorch 1.7+)

**Ne yapar?**
- Worker process'leri epoch arası cache'ler
- Her epoch'ta worker spawn etmez
- Windows'ta özellikle faydalı (spawn maliyeti)

**Performans:**
```python
persistent_workers=False:
  Epoch 1: 65s (worker spawn dahil)
  Epoch 2: 65s (worker spawn dahil) ❌

persistent_workers=True:
  Epoch 1: 65s (ilk spawn)
  Epoch 2: 60s (spawn yok) ✅
```

---

## 5️⃣ Memory Cleanup Best Practices

### Training Loop İçinde:

```python
from backend.config.compute_config import get_compute

compute = get_compute()

# Training loop
for epoch in range(num_epochs):
    # Epoch başında peak stats reset
    compute.reset_peak_memory_stats()

    # Training...
    for batch in train_loader:
        # Forward/backward
        loss.backward()
        optimizer.step()

    # Epoch sonunda cleanup
    compute.cleanup_after_training()

    # Memory stats log
    if epoch % 10 == 0:
        compute.log_memory_stats()
```

### Model Switching:

```python
# Model 1 training
model1.train()
# ...

# Model değiştirmeden önce cleanup
del model1
compute.cleanup_after_training()

# Model 2 training
model2 = MyModel().to(device)
```

### Large Operation Sonrası:

```python
# Büyük tensor işlemi
large_output = model(large_input)

# İşlem bittikten sonra cleanup
del large_output
compute.optimize_memory(aggressive=True)
```

---

## 6️⃣ Performans Monitoring

### VRAM Kullanımını İzle:

```python
compute = get_compute()

# Anlık kullanım
used, reserved = compute.vram_usage_gib()
print(f"Used: {used} GiB, Reserved: {reserved} GiB")

# Detaylı stats
stats = compute.get_memory_stats()
print(f"Utilization: {stats['utilization_percent']}%")
print(f"Peak: {stats['max_allocated_gib']} GiB")
```

### nvidia-smi ile Real-time Monitoring:

```powershell
# Terminal 1: Training
python train.py

# Terminal 2: Monitoring (1 saniye refresh)
nvidia-smi -l 1
```

**İdeal kullanım (RTX 4060 8GB):**
```
GPU Utilization: 90-100%  ✅
Memory Usage: 6-7.5 GiB   ✅ (margin var)
Temperature: <80°C        ✅
Power: 80-100W            ✅
```

---

## 7️⃣ Troubleshooting

### OOM (Out of Memory) Hatası

**Çözümler (öncelik sırasıyla):**

1. **Batch size azalt:**
   ```python
   batch_size = compute.suggest_batch_size(vram_usage_multiplier=0.75)
   ```

2. **Gradient accumulation kullan:**
   ```python
   accumulation_steps = 2
   effective_batch_size = batch_size * accumulation_steps
   ```

3. **Mixed precision kullan (zaten aktif):**
   ```python
   # BF16 zaten aktif
   # Eğer FP32 kullanıyorsan → BF16'ya geç
   ```

4. **Memory allocator ayarla:**
   ```powershell
   $env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True,max_split_size_mb:64"
   ```

### Yavaş Data Loading

**Çözümler:**

1. **num_workers artır:**
   ```python
   num_workers=4  # 2'den 4'e çıkar
   ```

2. **persistent_workers kullan:**
   ```python
   persistent_workers=True
   ```

3. **pin_memory aktif mi kontrol et:**
   ```python
   pin_memory=True  # GPU için mutlaka
   ```

### Fragmentation

**Çözüm:**
```powershell
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True,max_split_size_mb:128"
```

---

## 8️⃣ Özet: RTX 4060 için Optimal Ayarlar

### Environment Variables (.ps1 profile):

```powershell
# Memory allocator
$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True,max_split_size_mb:128"
```

### Python Config:

```python
from backend.config.compute_config import get_compute, initialize_compute

# Hybrid mode başlat
compute = initialize_compute(mode='hybrid')

# DataLoader ayarları
loader = DataLoader(
    dataset,
    batch_size=112,           # RTX 4060 için güvenli
    num_workers=2,            # Windows optimal
    pin_memory=True,          # GPU transfer hızı
    persistent_workers=True,  # Worker cache
)

# Training loop
for epoch in range(epochs):
    compute.reset_peak_memory_stats()

    # Training...

    compute.cleanup_after_training()
```

### Beklenen Performans:

```
VRAM: 7-7.5 GiB / 8 GiB (margin: 0.5-1 GiB) ✅
GPU Util: 90-100%                          ✅
Throughput: ~780 samples/sec (batch 112)   ✅
OOM Risk: <5%                              ✅
```

---

## 📚 Referanslar

- [PyTorch CUDA Semantics](https://pytorch.org/docs/stable/notes/cuda.html)
- [PyTorch DataLoader](https://pytorch.org/docs/stable/data.html)
- [CUDA Memory Management](https://pytorch.org/docs/stable/notes/cuda.html#memory-management)

---

**Notlar:**
- Bu ayarlar RTX 4060 8GB için optimize edilmiştir
- Farklı GPU'lar için parametreleri ayarlayın
- Production'da her zaman test edin
