# Vision Stack Installation Guide

## Windows 11 + Python 3.12.3 + RTX 4060

This guide helps you install the complete Sigma Analyst system including Vision/VLM capabilities on Windows.

### Prerequisites

- Python 3.12.3 installed
- NVIDIA RTX 4060 (or compatible GPU)
- CUDA 12.4 runtime installed
- Git installed
- Conda environment activated (recommended)

---

## Step-by-Step Installation

### 1. Create Fresh Conda Environment (Recommended)

```bash
conda create -n sigma python=3.12.3 -y
conda activate sigma
```

### 2. Upgrade pip, setuptools, wheel

```bash
python -m pip install -U pip setuptools wheel
```

### 3. Install PyTorch with CUDA Support (CRITICAL FIRST STEP)

**For CUDA 12.4:**
```bash
pip install --index-url https://download.pytorch.org/whl/cu124 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

**For CUDA 12.1:**
```bash
pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

**Verify GPU support:**
```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"
```

Expected output:
```
CUDA Available: True
GPU: NVIDIA GeForce RTX 4060
```

### 4. Install NumPy 2.x Stack (Lock Versions)

```bash
pip install numpy==2.2.6 pandas==2.3.3 scipy==1.14.1
```

### 5. Install Main Requirements

```bash
pip install -r requirements.txt
```

**Note:** Windows incompatible packages will be skipped automatically:
- `bitsandbytes` (Linux only)
- `paddleocr` (Linux only)
- `paddlepaddle` (Linux only)

### 6. Optional: Install Windows OCR Alternative

If you need OCR on Windows (instead of PaddleOCR):

```bash
pip install rapidocr-onnxruntime onnxruntime-gpu
```

### 7. Optional: Install TA-Lib (Advanced Indicators)

Download precompiled wheel from [cgohlke/talib-build](https://github.com/cgohlke/talib-build/releases):

```bash
# Download ta_lib-0.6.8-cp312-cp312-win_amd64.whl
pip install ta_lib-0.6.8-cp312-cp312-win_amd64.whl
```

---

## Verification

### Test Core Training Pipeline

```bash
# Test XGBoost training
python -m backend.training.train_xgboost --symbol BTCUSDT --timeframe 1h --task pattern_classification --data-dir data/advanced --output-dir data/models

# Test LSTM training
python -m backend.training.train_lstm --symbol BTCUSDT --timeframe 1h --market futures --epochs 5 --data-dir data/advanced --output-dir data/models

# Test PPO training
python -m backend.training.train_ppo --symbol BTCUSDT --timeframe 1h --market futures --total-timesteps 10000 --data-dir data/advanced --output-dir data/models
```

### Test Vision Capabilities

```python
# Test Ultralytics YOLOv8
import torch
from ultralytics import YOLO

print(f"PyTorch CUDA: {torch.cuda.is_available()}")
model = YOLO('yolov8n.pt')
print("YOLOv8 loaded successfully!")

# Test Transformers (VLM)
from transformers import AutoModel
print("Transformers ready!")
```

---

## Troubleshooting

### Issue: NumPy Version Conflicts

**Symptom:** After installing vision packages, NumPy upgrades to incompatible version

**Solution:**
```bash
# Uninstall problematic packages
pip uninstall -y ultralytics paddleocr paddlepaddle layoutparser bitsandbytes

# Force reinstall NumPy 2.x stack
pip uninstall -y numpy
pip install "numpy==2.2.6" --no-cache-dir --force-reinstall
pip install --no-cache-dir --force-reinstall pandas==2.3.3 scipy==1.14.1

# Reinstall vision packages (will skip Linux-only packages on Windows)
pip install -r requirements.txt
```

### Issue: Training Scripts Fail with Encoding Errors

**Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character`

**Solution:** Already fixed in all training scripts with UTF-8 encoding wrappers. If still occurs, ensure:
```python
import io, sys
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

### Issue: `bitsandbytes` Installation Fails on Windows

**Solution:** This is expected and normal. The package is marked for Linux-only via environment markers:
```
bitsandbytes>=0.43.0 ; sys_platform != 'win32'
```

You don't need it on Windows for basic VLM inference.

### Issue: CUDA Out of Memory

**Solution:** For RTX 4060 (8GB VRAM), use 4-bit quantization:

```python
# For Qwen2.5-VL-7B
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    load_in_4bit=True,  # Requires bitsandbytes on Linux
    device_map="auto"
)
```

On Windows without bitsandbytes, use smaller models or CPU offloading.

---

## Package Summary

### ✅ Installed on Windows:
- PyTorch (CUDA 12.4)
- Ultralytics (YOLOv8)
- OpenCV
- LayoutParser
- Transformers, Accelerate
- All core ML packages (XGBoost, LightGBM, CatBoost, scikit-learn)
- All RL packages (stable-baselines3, gymnasium)

### ⏭️ Skipped on Windows (Linux only):
- bitsandbytes (4-bit quantization)
- PaddleOCR / PaddlePaddle (use rapidocr-onnxruntime instead)
- detectron2 (install manually on Linux if needed)

---

## What's Next?

1. **Download Market Data:**
   ```bash
   python scripts/download_all.py
   ```

2. **Collect Advanced Features:**
   ```bash
   python scripts/collect_all.py
   ```

3. **Train Models:**
   ```bash
   python scripts/train_all.py
   ```

4. **Run UI:**
   ```bash
   # Backend
   python -m backend.main

   # Frontend (separate terminal)
   cd frontend
   npm install
   npm run dev
   ```

Enjoy your AI-powered trading bot! 🚀
