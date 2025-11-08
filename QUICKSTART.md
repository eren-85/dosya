# Quick Start - Copy-Paste Installation

## Windows 11 + Python 3.12.3 + RTX 4060

```powershell
# ============================================================================
# STEP 1: Upgrade pip
# ============================================================================
python -m pip install -U pip setuptools wheel

# ============================================================================
# STEP 2: Install PyTorch with CUDA 12.4 (CRITICAL - DO THIS FIRST!)
# ============================================================================
python -m pip uninstall -y torch torchvision torchaudio
python -m pip cache purge
python -m pip install --index-url https://download.pytorch.org/whl/cu124 --no-cache-dir --force-reinstall torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1

# ============================================================================
# STEP 3: Verify GPU support
# ============================================================================
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else None}')"

# Expected output: CUDA: True, GPU: NVIDIA GeForce RTX 4060

# ============================================================================
# STEP 4: Lock NumPy 2.x stack
# ============================================================================
python -m pip install numpy==2.2.6 pandas==2.3.3 scipy==1.14.1

# ============================================================================
# STEP 5: Install all requirements
# ============================================================================
python -m pip install -r requirements.txt

# ============================================================================
# STEP 6: Verify installation
# ============================================================================
python -c "import torch, transformers, stable_baselines3, gymnasium; print('✅ All core packages installed!')"

# ============================================================================
# DONE! Now you can use the system:
# ============================================================================

# Download market data
python scripts/download_all.py

# Collect advanced features
python scripts/collect_all.py

# Train models
python scripts/train_all.py

# Or train multi-modal PPO (with vision)
python -m backend.training.train_multimodal_ppo --symbol BTCUSDT --timeframe 1h --market futures --use-visual

# Run backend
python -m backend.main

# Run frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## Alternative: CUDA 12.1

```powershell
# If you have CUDA 12.1 instead of 12.4, use this in STEP 2:
python -m pip install --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir --force-reinstall torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

## Troubleshooting

### PyTorch installs CPU version instead of GPU

```powershell
# Force uninstall everything
pip uninstall -y torch torchvision torchaudio

# Clear pip cache completely
pip cache purge

# Re-install with CUDA (with --no-cache-dir to prevent using cached CPU wheel)
python -m pip install --index-url https://download.pytorch.org/whl/cu124 --no-cache-dir --force-reinstall torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1
```

### NumPy version conflicts after installing vision packages

```powershell
# Uninstall problematic packages
pip uninstall -y ultralytics paddleocr paddlepaddle layoutparser

# Force reinstall NumPy 2.x
pip uninstall -y numpy
pip install "numpy==2.2.6" --no-cache-dir --force-reinstall

# Reinstall requirements (will skip Windows-incompatible packages)
pip install -r requirements.txt
```

### Training fails with UTF-8 encoding errors

This is already fixed in all training scripts. If you still get errors, ensure:
- Console encoding is UTF-8
- Run: \`chcp 65001\` in PowerShell before training

### Multi-modal PPO fails with "backend.vision module not found"

```powershell
# Install vision dependencies
pip install ultralytics opencv-python layoutparser pillow matplotlib plotly

# For Qwen2.5-VL (VLM)
pip install transformers accelerate einops sentencepiece
```
