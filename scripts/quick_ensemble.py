"""
Quick Ensemble Model Generator
Creates a minimal XGBoost model for multi-modal PPO testing
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import warnings
warnings.filterwarnings('ignore')

# Paths
DATA_DIR = Path("data/advanced")
OUT_DIR = Path("data/models")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def find_data_file():
    """Find BTCUSDT 1h futures data"""
    patterns = [
        "BTCUSDT_1h_futures_binance.parquet",
        "BTCUSDT_1h_futures_multi.parquet",
        "BTCUSDT_1h_futures.parquet",
    ]

    for pattern in patterns:
        filepath = DATA_DIR / pattern
        if filepath.exists():
            return filepath

    raise FileNotFoundError(f"No BTCUSDT 1h futures data found in {DATA_DIR}")

def prepare_data(df):
    """Prepare numeric features and target"""
    # Exclude non-feature columns
    excluded_cols = ['open', 'high', 'low', 'close', 'volume', 'open_time', 'close_time', 'timestamp', 'target']

    # Get numeric columns only
    feature_cols = [
        col for col in df.columns
        if col not in excluded_cols
        and pd.api.types.is_numeric_dtype(df[col])
    ]

    if not feature_cols:
        raise ValueError("No numeric features found!")

    print(f"✅ Found {len(feature_cols)} numeric features")

    # Create simple target: price goes up = 1, down = 0
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df.dropna(inplace=True)

    # Extract features
    X = df[feature_cols].values.astype(np.float32)
    y = df['target'].values

    # Handle NaN/Inf
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    return X, y, feature_cols

def main():
    print("="*80)
    print("🚀 QUICK ENSEMBLE MODEL GENERATOR")
    print("="*80)

    # Find data
    data_file = find_data_file()
    print(f"📂 Using: {data_file}")

    # Load data
    df = pd.read_parquet(data_file)
    print(f"✅ Loaded {len(df)} candles")

    # Prepare features
    X, y, feature_cols = prepare_data(df)
    print(f"📊 X shape: {X.shape}, y shape: {y.shape}")

    # Train XGBoost
    print("🎓 Training XGBoost (200 trees, GPU)...")
    clf = XGBClassifier(
        tree_method='gpu_hist',
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        random_state=42,
        verbosity=0
    )

    clf.fit(X, y)
    print("✅ Training complete!")

    # Save model
    output_path = OUT_DIR / "BTCUSDT_1h_futures_xgb_sanity.json"
    clf.get_booster().save_model(str(output_path))
    print(f"💾 Model saved: {output_path}")
    print("="*80)
    print("✅ SUCCESS! You can now run multi-modal PPO training.")
    print("="*80)

if __name__ == '__main__':
    main()
