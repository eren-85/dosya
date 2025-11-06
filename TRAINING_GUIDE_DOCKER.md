# Crypto Trading Bot - Training Guide
# Docker + GPU (RTX 4060)

## Sistem Mimarisi

✅ **Docker Compose** ile çalışıyoruz
✅ **UI'dan** ya da **Terminal'den** eğitim yapabilirsin
✅ **GPU (NVIDIA RTX 4060)** Docker'a passthrough edilecek

---

## 1. Docker + GPU Setup

### A) NVIDIA Docker Runtime Kurulumu

```bash
# 1. NVIDIA Container Toolkit kur (Windows WSL2)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 2. Test
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### B) docker-compose.yml Güncelle

Ekle:
```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
```

---

## 2. Training Yöntemleri

### YÖNTEM 1: UI'dan Eğitim (Kolay) ✅

1. Frontend aç: `http://localhost:5173`
2. **Training** sayfasına git
3. Ayarları seç:
   - Model: `Ensemble`, `LSTM`, `PPO`, veya `All`
   - Symbols: `BTCUSDT,ETHUSDT`
   - Timeframes: `1h,4h,1d`
   - Market: `Spot` veya `Futures`
   - GPU: ✅ Enable
   - Epochs: `50-100`
4. **Start Training** tıkla
5. Real-time log'ları izle

**Avantajlar:**
- ✅ Görsel interface
- ✅ Real-time progress
- ✅ Kolay kullanım

---

### YÖNTEM 2: Terminal'den Eğitim (Manuel)

#### A) Docker Container'a Gir

```bash
docker exec -it dosya-backend-1 bash
```

#### B) Data Hazırla

```bash
python backend/training/prepare_rl_data.py
```

#### C) Ensemble Eğit (CPU, 5-10 dk)

```bash
python backend/training/train_ensemble_quick.py
```

Output:
```
🌲 Training XGBoost...
   Test RMSE: 0.023145
💡 Training LightGBM...
   Test RMSE: 0.021876
🐱 Training CatBoost...
   Test RMSE: 0.022340
✅ Ensemble training complete!
```

#### D) PPO Eğit (GPU, 30-60 dk)

```bash
python backend/training/quick_train_ppo.py --timesteps 100000
```

#### E) LSTM Eğit (GPU, 20-30 dk)

```bash
python backend/training/train_lstm_quick.py --epochs 50
```

---

## 3. GPU Kontrolü

### Docker İçinde GPU Test

```bash
docker exec -it dosya-backend-1 python scripts/test_gpu.py
```

Beklenen çıktı:
```
✅ PyTorch: 2.x.x
✅ CUDA available: True
✅ GPU: NVIDIA GeForce RTX 4060
✅ VRAM: 8.00 GB
✅ GPU computation test: PASSED
```

### VRAM Monitoring

```bash
# Host'ta çalıştır
watch -n 1 nvidia-smi
```

---

## 4. Training Sonrası

### Modeller Nerede?

```
backend/models/saved/
├── xgboost_btcusdt_1d.pkl
├── lightgbm_btcusdt_1d.pkl
├── catboost_btcusdt_1d.pkl
├── ensemble_weights.pkl
├── ppo_btcusdt_1d.zip
└── lstm_btcusdt_1d.pth
```

### Backend Otomatik Yükler

Backend restart edildiğinde Decision Engine modelleri otomatik yükler:

```bash
docker-compose restart backend
```

Log'da göreceksin:
```
🧠 Initializing Decision Engine...
   ✅ XGBoost loaded
   ✅ LightGBM loaded
   ✅ CatBoost loaded
   ✅ PPO loaded
   ✅ LSTM loaded
✅ Decision Engine ready!
```

---

## 5. API Test

### Decision Endpoint

```bash
curl http://localhost:8000/api/decision?symbol=BTCUSDT&timeframe=1d
```

Response:
```json
{
  "status": "success",
  "decision": {
    "action": "LONG",
    "confidence": 0.85,
    "entry": 68500,
    "stop_loss": 67000,
    "take_profit": 72000,
    "reasoning": "Ensemble: +2.5%, RSI oversold, MACD bullish"
  }
}
```

---

## 6. Dockerfile Güncellemesi

Backend Dockerfile'a PyTorch ekle:

```dockerfile
FROM python:3.11-slim

# NVIDIA CUDA base (optional, for GPU)
# FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install PyTorch with CUDA
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install training dependencies
COPY requirements_training.txt .
RUN pip install -r requirements_training.txt

# Copy code
COPY . /app
WORKDIR /app

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 7. Docker Compose Full Example

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - ./data:/app/data
      - ./models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - CUDA_VISIBLE_DEVICES=0
    command: uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    command: npm run dev
```

---

## 8. Training Workflow (UI)

```
1. Frontend → Training Page
     ↓
2. Seç: Model Type, Symbols, GPU
     ↓
3. Click: Start Training
     ↓
4. Backend → /api/ops/train endpoint
     ↓
5. Docker Container → Training script çalıştır
     ↓
6. GPU → Model training
     ↓
7. Model saved → backend/models/saved/
     ↓
8. Frontend → Real-time logs
     ↓
9. Training complete!
     ↓
10. Backend restart → Models auto-load
     ↓
11. Analysis Page → Real predictions!
```

---

## 9. Troubleshooting

### GPU not found
```bash
# WSL2'de NVIDIA driver kur
# https://docs.nvidia.com/cuda/wsl-user-guide/index.html

# Docker GPU access test
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

### Out of Memory (OOM)
```python
# Batch size küçült
batch_size = 16  # yerine 32
```

### Training çok yavaş
```bash
# GPU kullanıldığını kontrol et
docker exec -it dosya-backend-1 python -c "import torch; print(torch.cuda.is_available())"

# VRAM kullanımına bak
nvidia-smi
```

---

## 10. Özet

| Yöntem | Kullanım | Avantaj |
|--------|----------|---------|
| **UI** | Frontend Training Page | ✅ Kolay, görsel, progress bar |
| **Terminal** | `docker exec` + script | ✅ Detaylı kontrol, debug |

**Her iki yöntem de aynı sonucu verir!**

---

## Sonraki Adımlar

1. ✅ Docker Compose'u GPU ile güncelle
2. ✅ Backend Dockerfile'a PyTorch ekle
3. ✅ UI'dan training yap (kolay)
4. ✅ Models kaydedilir
5. ✅ Decision Engine otomatik yükler
6. ✅ Analysis page'de gerçek sinyaller!

🚀 **HAZIR!**
