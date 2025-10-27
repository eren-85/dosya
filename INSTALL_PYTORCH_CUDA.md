# PyTorch CUDA Kurulum Kılavuzu - RTX 4060

## 🎯 Sistem Gereksinimlerini Kontrol Edin

### 1. NVIDIA Sürücü ve CUDA Kontrolü

Terminalinizde şunu çalıştırın:

```powershell
nvidia-smi
```

**Beklenen çıktı:**
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 581.08                 Driver Version: 581.08         CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |
|   0  NVIDIA GeForce RTX 4060 ...  WDDM  |   00000000:01:00.0  On |                  N/A |
```

✅ **Önemli:** `CUDA Version` görünüyor mu? Evet ise devam edebilirsiniz.

---

## 📦 PyTorch CUDA Kurulumu

### Adım 1: Mevcut PyTorch'u Kaldırın (Varsa)

```powershell
pip uninstall -y torch torchvision torchaudio
```

### Adım 2: CUDA 12.4 ile PyTorch Kurulumu (ÖNERİLİR)

**RTX 4060 için en iyi seçenek: CUDA 12.4**

```powershell
pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

### Alternatif: CUDA 12.1 ile PyTorch

CUDA 12.4'te sorun yaşarsanız:

```powershell
pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

### Adım 3: Kurulumu Doğrulayın

```powershell
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda); print('Device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"
```

**Beklenen çıktı:**
```
PyTorch version: 2.5.1+cu124
CUDA available: True
CUDA version: 12.4
Device name: NVIDIA GeForce RTX 4060 Laptop GPU
```

✅ **CUDA available: True** görmeli ve GPU adınız doğru olmalı!

---

## 🔧 Detaylı Test (Opsiyonel)

Sigma Analyst kurulumu yaptıysanız, detaylı GPU testi çalıştırın:

```powershell
python -m backend.config.compute_config
```

**Beklenen çıktı:**
```
======================================================================
🔧 GPU Setup Test - Sigma Analyst
======================================================================

1️⃣  PyTorch Installation:
   PyTorch Version: 2.5.1+cu124
   CUDA Available: True
   CUDA Version: 12.4
   cuDNN Version: 90100
   Device Count: 1
   Device Name: NVIDIA GeForce RTX 4060 Laptop GPU
   VRAM: 8.0 GB
   Compute Capability: 8.9
   BF16 Support: ✅ Yes
   TF32 Support: ✅ Yes

2️⃣  Compute Manager Test:
============================================================
🖥️  Compute Mode: HYBRID
============================================================

🎮 GPU Information:
   Name: NVIDIA GeForce RTX 4060 Laptop GPU
   VRAM: 8.0 GB
   Compute Capability: 8.9
   CUDA Version: 12.4
   cuDNN Version: 90100

📊 Workload Distribution:
   • Deep Learning (LSTM/Transformer): CUDA
   • ML Tree Models (XGBoost/CatBoost): CPU
   • RL Training (PPO): CUDA
   • Technical Analysis: CPU
   • Backtest Engine: CPU

⚙️  GPU Settings:
   • Batch Size: 128
   • Mixed Precision: torch.bfloat16
   • TF32 Enabled: True
   • BF16 Support: ✅ (Better stability than FP16)

✅ TF32 enabled for matrix operations
✅ Float32 matmul precision set to 'high'
✅ cuDNN benchmark enabled

3️⃣  Memory Test:
   Test allocation: 0.00 GB
   Free VRAM: 8.00 GB
   ✅ Memory test passed

4️⃣  BF16/FP16 Test:
   Using: torch.bfloat16
   ✅ Mixed precision test passed

======================================================================
✅ Setup test complete!
======================================================================
```

---

## ❌ Sorun Giderme

### Problem 1: "torch.cuda.is_available() = False"

**Çözüm 1: CUDA versiyonunu kontrol edin**

```powershell
# nvidia-smi çıktısındaki CUDA Version'a bakın
nvidia-smi

# CUDA 12.x ise:
pip install --index-url https://download.pytorch.org/whl/cu124 torch torchvision torchaudio

# CUDA 11.x ise (eski sürücü):
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision torchaudio
```

**Çözüm 2: NVIDIA sürücüsünü güncelleyin**

https://www.nvidia.com/Download/index.aspx adresinden en güncel sürücüyü indirin.

### Problem 2: "RuntimeError: CUDA out of memory"

**Çözüm: Batch size'ı azaltın**

```python
from backend.config.compute_config import get_compute

compute = get_compute()
batch_size = compute.suggest_batch_size(vram_usage_multiplier=0.5)  # Half VRAM
print(f"Reduced batch size: {batch_size}")
```

### Problem 3: "Could not load dynamic library 'cudnn64_8.dll'"

**Çözüm: cuDNN otomatik yüklenir**

PyTorch 2.5.1 cuDNN'i içerir. Ayrı kurulum gerekmez. Sorun devam ederse:

```powershell
pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

---

## 📊 PyTorch CUDA Versiyonları

### Hangi CUDA Versiyonunu Seçmeliyim?

| GPU | Önerilen CUDA | Kurulum Komutu |
|-----|---------------|----------------|
| RTX 40xx (4090, 4080, 4070, **4060**) | **CUDA 12.4** | `--index-url https://download.pytorch.org/whl/cu124` |
| RTX 30xx (3090, 3080, 3070, 3060) | CUDA 12.1 | `--index-url https://download.pytorch.org/whl/cu121` |
| RTX 20xx (2080, 2070, 2060) | CUDA 11.8 | `--index-url https://download.pytorch.org/whl/cu118` |
| GTX 16xx (1660, 1650) | CUDA 11.8 | `--index-url https://download.pytorch.org/whl/cu118` |

**Notlar:**
- RTX 40xx için CUDA 12.4 **en iyi performansı** sağlar
- CUDA 12.1 de çalışır ama biraz daha yavaş olabilir
- Daha eski CUDA versiyonları (11.x) RTX 40xx'te **BF16 ve TF32 desteği** vermez

---

## ✅ Kurulum Tamamlandı!

PyTorch CUDA kurulumu tamamlandıysa, geri kalan paketleri kurun:

```powershell
# requirements.txt'teki diğer paketler
pip install -r requirements.txt

# TA-Lib (opsiyonel, Windows için binary wheel)
# https://github.com/cgohlke/talib-build/releases
pip install ta_lib-0.6.8-cp312-cp312-win_amd64.whl
```

**Test edin:**

```powershell
python -m backend.config.compute_config
```

---

## 🚀 Performans Beklentileri (RTX 4060 8GB)

CUDA 12.4 + BF16 + TF32 ile:

| Model | CPU (12 cores) | GPU (RTX 4060) | Speedup |
|-------|----------------|----------------|---------|
| LSTM (100 epochs) | ~2000s (33 dk) | ~80s (1.3 dk) | **25x** |
| Transformer (100 epochs) | ~5000s (83 dk) | ~100s (1.7 dk) | **50x** |
| RL Training (100k steps) | ~1200s (20 dk) | ~120s (2 dk) | **10x** |
| XGBoost (10k samples) | ~5s | ~5s | 1x (CPU zaten hızlı) |
| Technical Analysis | ~0.5s | N/A (CPU'da çalışır) | - |
| Backtest (10k bars) | ~0.1s | N/A (CPU'da çalışır) | - |

**Total Pipeline:** 8200s (2.3 saat) → 480s (8 dakika) = **17x speedup**

---

## 📚 Ek Kaynaklar

- [PyTorch Resmi Dokümantasyon](https://pytorch.org/get-started/locally/)
- [NVIDIA CUDA Downloads](https://developer.nvidia.com/cuda-downloads)
- [RTX 4060 Specs](https://www.nvidia.com/en-us/geforce/graphics-cards/40-series/rtx-4060-4060ti/)
- [Sigma Analyst GPU Usage Guide](./docs/GPU_USAGE_GUIDE.md)

---

## 💡 İpuçları

1. **Her zaman CUDA 12.4 kullanın** (RTX 4060 için)
2. **BF16 otomatik aktif** olacak (FP16'dan daha stabil)
3. **TF32 otomatik aktif** olacak (+%10-30 hız)
4. **Batch size otomatik ayarlanacak** (VRAM'e göre)
5. **Tree modeller CPU'da kalacak** (küçük data için daha hızlı)

---

Kurulumda sorun yaşarsanız:
- GitHub Issues: https://github.com/your-repo/issues
- GPU test: `python -m backend.config.compute_config`
- VRAM monitoring: `nvidia-smi -l 1` (1 saniye refresh)
