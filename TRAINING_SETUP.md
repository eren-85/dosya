# Crypto Trading Bot - Local Training Setup
# Windows + RTX 4060 (8GB VRAM)

## Prerequisites

- Python 3.11
- CUDA 12.1+ (for GPU)
- Git

## Installation

### 1. Create Virtual Environment

```bash
cd C:\path\to\dosya
python -m venv venv
venv\Scripts\activate
```

### 2. Install PyTorch (GPU)

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3. Install Dependencies

```bash
pip install -r requirements_training.txt
```

### 4. Test GPU

```bash
python scripts/test_gpu.py
```

Expected output:
```
✅ PyTorch: 2.x.x
✅ CUDA available: True
✅ GPU: NVIDIA GeForce RTX 4060
✅ VRAM: 8192 MB
```

---

## Training Workflow

### Step 1: Prepare Data

```bash
python backend/training/prepare_rl_data.py
```

Output: `backend/data/prepared/BTCUSDT_1d_futures_prepared.parquet`

### Step 2: Train Ensemble Models (Fast: 5-10 min)

```bash
python backend/training/train_ensemble_quick.py
```

Output:
- `backend/models/saved/xgboost_btcusdt_1d.pkl`
- `backend/models/saved/lightgbm_btcusdt_1d.pkl`
- `backend/models/saved/catboost_btcusdt_1d.pkl`
- `backend/models/saved/ensemble_weights.pkl`

### Step 3: Train PPO Agent (Moderate: 30-60 min)

```bash
python backend/training/quick_train_ppo.py --timesteps 100000
```

Output: `backend/models/saved/ppo_btcusdt_1d.zip`

### Step 4: Train LSTM (Optional: 20-30 min)

```bash
python backend/training/train_lstm_quick.py --epochs 50
```

Output: `backend/models/saved/lstm_btcusdt_1d.pth`

---

## Testing Decision Engine

```bash
python backend/models/decision_engine.py --symbol BTCUSDT --test
```

---

## Starting Backend (with trained models)

```bash
cd backend
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

Visit: http://localhost:5173 (frontend already running)

---

## GPU Memory Management

If you get OOM (Out of Memory) errors:

### Reduce batch size:
```python
# In training scripts
batch_size = 32  # instead of 64
```

### Use mixed precision:
```python
# Already enabled in LSTM script
scaler = torch.cuda.amp.GradScaler()
```

### Monitor VRAM:
```bash
nvidia-smi
```

---

## Troubleshooting

### CUDA not available
- Install NVIDIA drivers: https://www.nvidia.com/Download/index.aspx
- Install CUDA Toolkit 12.1: https://developer.nvidia.com/cuda-downloads

### Import errors
```bash
pip install --upgrade -r requirements_training.txt
```

### Training too slow
- Check GPU usage: `nvidia-smi`
- Enable GPU in scripts (already done)
- Close other GPU apps (browsers, Discord, etc.)

---

## File Structure After Training

```
backend/
  models/
    saved/
      ├── xgboost_btcusdt_1d.pkl
      ├── lightgbm_btcusdt_1d.pkl
      ├── catboost_btcusdt_1d.pkl
      ├── ensemble_weights.pkl
      ├── ppo_btcusdt_1d.zip
      └── lstm_btcusdt_1d.pth
  data/
    prepared/
      └── BTCUSDT_1d_futures_prepared.parquet
```

---

## Next Steps

1. ✅ Train models locally (this guide)
2. ✅ Models saved to `backend/models/saved/`
3. ✅ Backend automatically loads models
4. ✅ Frontend Analysis page shows real predictions
5. ✅ Test with live BTC price

---

## Notes

- Training on RTX 4060 is **fast** (much faster than CPU)
- Ensemble models don't need GPU (CPU is fine)
- PPO and LSTM benefit from GPU
- 8GB VRAM is enough for all models
- Quantization (int4) not needed for training, only inference
