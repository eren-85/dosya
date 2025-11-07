#!/usr/bin/env python3
"""
Quick Test Training Script
Simple XGBoost model to predict next candle direction (up/down)

Usage:
    python -m backend.training.quick_test_train --symbol BTCUSDT --timeframe 1h --market futures
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import xgboost as xgb
import argparse
from datetime import datetime

def prepare_features(df):
    """Prepare features from dataframe"""

    # Target: Next candle direction (1 = up, 0 = down)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)

    # Select feature columns (exclude non-numeric and target)
    exclude_cols = ['open_time', 'close_time', 'close_time_ms', 'ignore',
                    'quote_asset_volume', 'taker_buy_quote', 'target',
                    'cvd_src', 'session_label', 'ob_phase', 'ob_source',
                    'has_binance', 'has_ob', 'is_kz_asia', 'is_kz_london',
                    'is_kz_ny_am', 'is_kz_ny_pm', 'timestamp', 'funding_ts']

    feature_cols = [col for col in df.columns if col not in exclude_cols]

    # Remove rows with NaN in features or target
    df_clean = df[feature_cols + ['target']].dropna()

    X = df_clean[feature_cols]
    y = df_clean['target']

    print(f"\n📊 Feature Engineering:")
    print(f"   Total features: {len(feature_cols)}")
    print(f"   Total samples: {len(df_clean)}")
    print(f"   Features: {', '.join(feature_cols[:10])}...")

    return X, y, feature_cols

def train_model(X_train, y_train, X_test, y_test):
    """Train XGBoost model"""

    print(f"\n🧠 Training XGBoost Model...")

    # XGBoost parameters
    params = {
        'objective': 'binary:logistic',
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'random_state': 42,
        'eval_metric': 'logloss'
    }

    model = xgb.XGBClassifier(**params)

    # Train
    start_time = datetime.now()
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )
    train_time = (datetime.now() - start_time).total_seconds()

    print(f"   ✅ Training complete in {train_time:.1f}s")

    return model

def evaluate_model(model, X_train, y_train, X_test, y_test, feature_cols):
    """Evaluate model performance"""

    print(f"\n📈 Model Evaluation:")

    # Train accuracy
    y_train_pred = model.predict(X_train)
    train_acc = accuracy_score(y_train, y_train_pred)
    print(f"   Train Accuracy: {train_acc*100:.2f}%")

    # Test accuracy
    y_test_pred = model.predict(X_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    print(f"   Test Accuracy:  {test_acc*100:.2f}%")

    # Classification report
    print(f"\n📋 Classification Report:")
    print(classification_report(y_test, y_test_pred, target_names=['Down', 'Up']))

    # Confusion matrix
    cm = confusion_matrix(y_test, y_test_pred)
    print(f"\n🔢 Confusion Matrix:")
    print(f"                Predicted")
    print(f"               Down    Up")
    print(f"   Actual Down  {cm[0,0]:4d}  {cm[0,1]:4d}")
    print(f"          Up    {cm[1,0]:4d}  {cm[1,1]:4d}")

    # Feature importance (top 10)
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n🎯 Top 10 Most Important Features:")
    for idx, row in feature_importance.head(10).iterrows():
        print(f"   {row['feature']:20s}: {row['importance']:.4f}")

    return test_acc

def main():
    parser = argparse.ArgumentParser(description='Quick Test Training')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Symbol (e.g., BTCUSDT)')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (e.g., 1h)')
    parser.add_argument('--market', type=str, default='futures', choices=['spot', 'futures'], help='Market type')

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"🚀 Quick Test Training: {args.symbol} {args.timeframe} {args.market.upper()}")
    print(f"{'='*60}")

    # Load data
    data_path = f"data/advanced/{args.symbol}_{args.timeframe}_{args.market}_multi.parquet"

    print(f"\n📂 Loading data from: {data_path}")

    try:
        df = pd.read_parquet(data_path)
        print(f"   ✅ Loaded {len(df)} rows, {len(df.columns)} columns")
    except FileNotFoundError:
        print(f"   ❌ File not found: {data_path}")
        print(f"   💡 Run data collection first:")
        print(f"      python -m backend.data.advanced_collector --symbols {args.symbol} --timeframe {args.timeframe} --market {args.market}")
        return

    # Prepare features
    X, y, feature_cols = prepare_features(df)

    # Train/test split (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False  # Don't shuffle time series
    )

    print(f"\n📦 Data Split:")
    print(f"   Train set: {len(X_train)} samples")
    print(f"   Test set:  {len(X_test)} samples")

    # Train model
    model = train_model(X_train, y_train, X_test, y_test)

    # Evaluate
    test_acc = evaluate_model(model, X_train, y_train, X_test, y_test, feature_cols)

    # Save model
    model_dir = Path("data/models")
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / f"{args.symbol}_{args.timeframe}_{args.market}_xgb_test.json"
    model.save_model(str(model_path))

    print(f"\n💾 Model saved to: {model_path}")

    print(f"\n{'='*60}")
    print(f"✅ Training Complete!")
    print(f"   Final Test Accuracy: {test_acc*100:.2f}%")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
