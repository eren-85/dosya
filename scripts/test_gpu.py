"""
Test GPU availability and CUDA setup
Run this before training to verify everything works
"""

import sys

print("🔍 Testing GPU Setup...\n")

# Test 1: PyTorch
try:
    import torch
    print(f"✅ PyTorch: {torch.__version__}")

    if torch.cuda.is_available():
        print(f"✅ CUDA available: True")
        print(f"✅ CUDA version: {torch.version.cuda}")
        print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
        print(f"✅ VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

        # Test tensor on GPU
        x = torch.randn(1000, 1000).cuda()
        y = torch.randn(1000, 1000).cuda()
        z = torch.matmul(x, y)
        print(f"✅ GPU computation test: PASSED")

    else:
        print("❌ CUDA not available")
        print("   Install CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
        print("   Install GPU drivers: https://www.nvidia.com/Download/index.aspx")
        sys.exit(1)

except ImportError:
    print("❌ PyTorch not installed")
    print("   Install with: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    sys.exit(1)

# Test 2: Stable Baselines3
try:
    import stable_baselines3
    print(f"\n✅ Stable Baselines3: {stable_baselines3.__version__}")
except ImportError:
    print("\n⚠️  Stable Baselines3 not installed")
    print("   Install with: pip install stable-baselines3[extra]")

# Test 3: XGBoost GPU
try:
    import xgboost as xgb
    print(f"✅ XGBoost: {xgb.__version__}")

    # Test GPU support
    dmatrix = xgb.DMatrix([[1, 2], [3, 4]], label=[1, 0])
    params = {'tree_method': 'hist', 'device': 'cuda'}
    xgb.train(params, dmatrix, num_boost_round=1)
    print(f"✅ XGBoost GPU: AVAILABLE")

except Exception as e:
    print(f"⚠️  XGBoost GPU: Not available (will use CPU)")

# Test 4: LightGBM
try:
    import lightgbm as lgb
    print(f"✅ LightGBM: {lgb.__version__}")
except ImportError:
    print("⚠️  LightGBM not installed")

# Test 5: CatBoost
try:
    import catboost
    print(f"✅ CatBoost: {catboost.__version__}")
except ImportError:
    print("⚠️  CatBoost not installed")

print("\n" + "="*50)
print("🎉 GPU Setup Complete!")
print("="*50)
print("\nReady to train models with GPU acceleration! 🚀")
