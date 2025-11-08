#!/usr/bin/env python3
"""
XGBoost Model Training Script

Usage:
    python -m backend.training.train_xgboost --symbol BTCUSDT --timeframe 1h --task pattern_classification
    python -m backend.training.train_xgboost --symbol BTCUSDT --timeframe 4h --task trend_classification

Features:
    - Pattern classification (Head & Shoulders, Double Top/Bottom, Triangles, etc.)
    - Trend classification (Uptrend, Downtrend, Sideways)
    - Feature importance analysis
    - Hyperparameter optimization
    - Model persistence
"""

import os
import sys
import io

# Fix Windows encoding issue (support emojis)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import xgboost as xgb
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import json
import pickle

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def calculate_indicators(df):
    """Calculate technical indicators for features"""

    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

    # Moving averages
    for period in [7, 14, 21, 50, 100, 200]:
        df[f'sma_{period}'] = df['close'].rolling(period).mean()
        df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(14).mean()

    # Volume indicators
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']

    # Momentum
    df['momentum'] = df['close'] - df['close'].shift(10)
    df['roc'] = ((df['close'] - df['close'].shift(12)) / df['close'].shift(12)) * 100

    # Price position
    df['price_position'] = (df['close'] - df['low'].rolling(14).min()) / (
        df['high'].rolling(14).max() - df['low'].rolling(14).min()
    )

    # Stochastic Oscillator
    low_14 = df['low'].rolling(14).min()
    high_14 = df['high'].rolling(14).max()
    df['stoch_k'] = 100 * (df['close'] - low_14) / (high_14 - low_14)
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()

    # CCI (Commodity Channel Index)
    tp = (df['high'] + df['low'] + df['close']) / 3
    df['cci'] = (tp - tp.rolling(20).mean()) / (0.015 * tp.rolling(20).std())

    # Williams %R
    df['williams_r'] = -100 * (high_14 - df['close']) / (high_14 - low_14)

    # ADX (Average Directional Index)
    plus_dm = df['high'].diff()
    minus_dm = df['low'].diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr14 = true_range.rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr14)
    minus_di = 100 * (abs(minus_dm).rolling(14).sum() / tr14)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(14).mean()

    # NOTE: Don't drop NaN rows here - let prepare_features handle it robustly
    # Dropping rows here causes too much data loss (e.g., 54k -> 1 sample)
    return df


def detect_patterns(df):
    """
    Detect chart patterns and label them

    Returns:
        pattern_labels: Array of pattern types
    """
    patterns = []

    for i in range(20, len(df) - 20):
        window = df.iloc[i-20:i+20]

        pattern_type = 'none'

        # Head and Shoulders detection
        if detect_head_and_shoulders(window):
            pattern_type = 'head_and_shoulders'

        # Double Top detection
        elif detect_double_top(window):
            pattern_type = 'double_top'

        # Double Bottom detection
        elif detect_double_bottom(window):
            pattern_type = 'double_bottom'

        # Triangle detection
        elif detect_triangle(window):
            pattern_type = 'triangle'

        # Flag/Pennant detection
        elif detect_flag(window):
            pattern_type = 'flag'

        patterns.append(pattern_type)

    # Add padding for windows at start/end
    patterns = ['none'] * 20 + patterns + ['none'] * 20

    return np.array(patterns[:len(df)])


def detect_head_and_shoulders(window):
    """Detect Head and Shoulders pattern"""
    highs = window['high'].values

    # Find local maxima
    peaks = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            peaks.append((i, highs[i]))

    if len(peaks) < 3:
        return False

    # Check if middle peak is highest (head)
    peaks = sorted(peaks, key=lambda x: x[1], reverse=True)
    head = peaks[0]
    shoulders = peaks[1:3]

    # Shoulders should be at similar height (within 5%)
    if len(shoulders) == 2:
        h1, h2 = shoulders[0][1], shoulders[1][1]
        if abs(h1 - h2) / max(h1, h2) < 0.05:
            # Head should be significantly higher
            if head[1] > max(h1, h2) * 1.1:
                return True

    return False


def detect_double_top(window):
    """Detect Double Top pattern"""
    highs = window['high'].values

    # Find two highest peaks
    peaks = []
    for i in range(1, len(highs) - 1):
        if highs[i] > highs[i-1] and highs[i] > highs[i+1]:
            peaks.append((i, highs[i]))

    if len(peaks) < 2:
        return False

    # Get two highest peaks
    peaks = sorted(peaks, key=lambda x: x[1], reverse=True)[:2]

    # Peaks should be at similar height (within 3%)
    if abs(peaks[0][1] - peaks[1][1]) / max(peaks[0][1], peaks[1][1]) < 0.03:
        return True

    return False


def detect_double_bottom(window):
    """Detect Double Bottom pattern"""
    lows = window['low'].values

    # Find two lowest troughs
    troughs = []
    for i in range(1, len(lows) - 1):
        if lows[i] < lows[i-1] and lows[i] < lows[i+1]:
            troughs.append((i, lows[i]))

    if len(troughs) < 2:
        return False

    # Get two lowest troughs
    troughs = sorted(troughs, key=lambda x: x[1])[:2]

    # Troughs should be at similar depth (within 3%)
    if abs(troughs[0][1] - troughs[1][1]) / min(troughs[0][1], troughs[1][1]) < 0.03:
        return True

    return False


def detect_triangle(window):
    """Detect Triangle pattern (consolidation)"""
    highs = window['high'].values
    lows = window['low'].values

    # Calculate range compression
    early_range = np.mean(highs[:10]) - np.mean(lows[:10])
    late_range = np.mean(highs[-10:]) - np.mean(lows[-10:])

    # Triangle has decreasing range
    if late_range < early_range * 0.6:
        return True

    return False


def detect_flag(window):
    """Detect Flag/Pennant pattern"""
    closes = window['close'].values

    # Strong move followed by consolidation
    early_move = (closes[5] - closes[0]) / closes[0]
    late_range = np.std(closes[-10:]) / np.mean(closes[-10:])

    # Strong initial move (>3%) and low volatility after (<1%)
    if abs(early_move) > 0.03 and late_range < 0.01:
        return True

    return False


def classify_trend(df):
    """
    Classify trend for each candle

    Returns:
        trend_labels: 0=Downtrend, 1=Sideways, 2=Uptrend
    """
    trends = []

    for i in range(50, len(df)):
        window = df.iloc[i-50:i]

        # Calculate trend using linear regression
        x = np.arange(len(window))
        y = window['close'].values

        # Fit line
        slope = np.polyfit(x, y, 1)[0]

        # Normalize slope by price
        normalized_slope = slope / window['close'].mean()

        # Classify trend
        if normalized_slope > 0.001:  # Uptrend threshold
            trend = 2
        elif normalized_slope < -0.001:  # Downtrend threshold
            trend = 0
        else:
            trend = 1  # Sideways

        trends.append(trend)

    # Pad for early candles
    trends = [1] * 50 + trends

    return np.array(trends[:len(df)])


def load_data(symbol, timeframe, market='futures', data_dir='data/advanced', days=None, limit=None):
    """
    Load historical data from Parquet
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe (e.g., '1h', '1d')
        market: Market type ('futures' or 'spot')
        data_dir: Data directory
        days: Load only last N days of data (faster training)
        limit: Load only last N candles (alternative to days)
    """

    # Try multiple file patterns in order
    patterns = [
        f"{symbol}_{timeframe}_{market}_binance.parquet",  # Advanced collector format
        f"{symbol}_{timeframe}_{market}_multi.parquet",     # Multi-file format
        f"{symbol}_{timeframe}_{market}.parquet",            # Basic format
    ]

    for filename in patterns:
        filepath = Path(data_dir) / filename
        if filepath.exists():
            print(f"📂 Loading data from {filepath}")
            df = pd.read_parquet(filepath)

            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Data must have columns: {required_cols}")

            # Filter by date if requested
            if days is not None:
                # Get timestamp column
                timestamp_col = None
                if 'close_time' in df.columns:
                    timestamp_col = 'close_time'
                elif 'open_time' in df.columns:
                    timestamp_col = 'open_time'
                elif 'timestamp' in df.columns:
                    timestamp_col = 'timestamp'
                
                if timestamp_col:
                    # Convert to datetime if needed
                    if not pd.api.types.is_datetime64_any_dtype(df[timestamp_col]):
                        df[timestamp_col] = pd.to_datetime(df[timestamp_col], unit='ms', errors='coerce')
                    
                    # Get last N days
                    cutoff_date = df[timestamp_col].max() - pd.Timedelta(days=days)
                    df = df[df[timestamp_col] >= cutoff_date].copy()
                    print(f"   Filtered to last {days} days")
            
            # Or filter by limit (last N candles)
            elif limit is not None:
                df = df.tail(limit).copy()
                print(f"   Using last {limit} candles")
            
            # Sort by time (ensure chronological order)
            if 'close_time' in df.columns or 'open_time' in df.columns or 'timestamp' in df.columns:
                ts_col = timestamp_col if 'timestamp_col' in locals() and timestamp_col else ('close_time' if 'close_time' in df.columns else ('open_time' if 'open_time' in df.columns else 'timestamp'))
                if ts_col in df.columns:
                    df = df.sort_values(ts_col).reset_index(drop=True)

            print(f"✅ Loaded {len(df)} candles")
            return df

    # If none found, raise error
    raise FileNotFoundError(
        f"Data file not found for {symbol}_{timeframe}_{market} in {data_dir}. "
        f"Tried patterns: {patterns}"
    )


def prepare_features(df, task='pattern_classification'):
    """
    Prepare features and target for training
    ROBUST CLEANING: column-based instead of row-based to preserve samples
    """

    print("🔧 Calculating technical indicators...")
    df = calculate_indicators(df)

    # --- ROBUST CLEANING: satır atma yok; NaN/Inf -> 0 ---
    excluded = {"open", "high", "low", "close", "volume",
                "open_time", "close_time", "timestamp", "target"}

    # Objeleri ve tamamı-NaN kolonları at
    object_cols = df.select_dtypes(include=["object"]).columns.tolist()
    if object_cols:
        print(f"🗑️  Dropping {len(object_cols)} object columns")
        df = df.drop(columns=object_cols, errors="ignore")
    
    # Tamamı-NaN kolonları at
    nan_cols = df.columns[df.isna().all()].tolist()
    if nan_cols:
        print(f"🗑️  Dropping {len(nan_cols)} fully NaN columns")
        df = df.drop(columns=nan_cols)

    # Sadece numerik feature'lar
    feature_cols = [c for c in df.columns
                    if c not in excluded and pd.api.types.is_numeric_dtype(df[c])]
    
    if not feature_cols:
        raise ValueError("No numeric features after cleaning.")

    print(f"📊 Using {len(feature_cols)} features")

    # NaN/±Inf => 0 (satır ELENMEYECEK)
    X = df[feature_cols].astype("float32").replace([np.inf, -np.inf], np.nan).fillna(0.0)
    Xv = np.nan_to_num(X.values, nan=0.0, posinf=0.0, neginf=0.0)

    # Create target based on task
    if task == 'pattern_classification':
        print("🔍 Detecting patterns...")
        y_raw = detect_patterns(df)
        # Convert string patterns to numeric labels
        unique_patterns = np.unique(y_raw)
        pattern_to_label = {p: i for i, p in enumerate(unique_patterns)}
        y = np.array([pattern_to_label[p] for p in y_raw])
        print(f"   Found {len(unique_patterns)} pattern types: {unique_patterns}")

    elif task == 'trend_classification':
        print("📈 Classifying trends...")
        y = classify_trend(df)
        print(f"   Trend distribution: {np.bincount(y)}")
    else:
        raise ValueError(f"Unknown task: {task}")

    # y zaten üretildi; sadece NaN olmayanları al
    y_series = pd.Series(y, index=df.index)
    mask = y_series.notna().values
    Xv_clean = Xv[mask]
    y_clean = y_series[mask].astype("int32", errors="ignore").values

    # Örnek azsa fallback: next-bar sign
    MIN_SAMPLES = 1000
    if len(y_clean) < MIN_SAMPLES:
        print(f"⚠️  Only {len(y_clean)} samples found, using fallback label (next-bar sign)")
        # Create simple binary label: next bar goes up (1) or down (0)
        diff = df["close"].shift(-1) - df["close"]
        y_fb = (diff > 0).astype("int32")
        # Fill NaN values (using modern pandas syntax)
        y_fb = y_fb.ffill().bfill().fillna(0)
        # Apply same mask
        y_clean = y_fb[mask].values.astype("int32")
        print(f"   [fallback] Using next-bar sign label -> samples: {len(y_clean)}")
    
    Xv, y = Xv_clean, y_clean

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(Xv)

    # Train/valid böl (küçük datada valid'i küçült)
    if len(y) < 40:
        X_train, y_train = X_scaled, y
        X_val, y_val = X_train[:0], y_train[:0]
        print(f"⚠️  Too few samples ({len(y)}), skipping validation split")
    else:
        test_size = 0.2 if len(y) >= 1000 else (0.1 if len(y) >= 200 else 0.05)
        X_train, X_val, y_train, y_val = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, shuffle=True
        )

    print(f"✅ Prepared data: X_train={X_train.shape}, X_val={X_val.shape}, y={len(y)} samples")
    print(f"   Train: {len(X_train)}, Val: {len(X_val)}")

    return X_train, X_val, y_train, y_val, scaler, feature_cols


def train_model(X_train, y_train, X_val, y_val, n_estimators=500, max_depth=6, learning_rate=0.1, tree_method='auto'):
    """Train XGBoost model"""

    print(f"\n🚀 Starting XGBoost training...")
    print(f"   Estimators: {n_estimators}")
    print(f"   Max depth: {max_depth}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Tree method: {tree_method}")
    print("-" * 60)

    # Convert to DMatrix for XGBoost
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)

    # Auto-detect GPU if tree_method is 'auto'
    if tree_method == 'auto':
        try:
            import torch
            if torch.cuda.is_available():
                tree_method = 'gpu_hist'
                print(f"   ✅ GPU detected, using gpu_hist")
            else:
                tree_method = 'hist'
                print(f"   ⚠️  No GPU detected, using hist (CPU)")
        except ImportError:
            tree_method = 'hist'
            print(f"   ⚠️  PyTorch not available, using hist (CPU)")

    # XGBoost parameters
    params = {
        'objective': 'multi:softmax',
        'num_class': len(np.unique(y_train)),
        'max_depth': max_depth,
        'learning_rate': learning_rate,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'gamma': 0,
        'eval_metric': 'mlogloss',
        'tree_method': tree_method,
    }

    # Training with early stopping and progress bar
    # Only use validation set if it's not empty
    if len(X_val) > 0:
        evals = [(dtrain, 'train'), (dval, 'val')]
        early_stopping_rounds = 50
    else:
        evals = [(dtrain, 'train')]
        early_stopping_rounds = None
        print("   ⚠️  No validation set, skipping early stopping")
    
    # Create progress bar
    try:
        from tqdm import tqdm
        
        # Custom callback class for XGBoost
        class ProgressCallback(xgb.callback.TrainingCallback):
            def __init__(self, total_rounds):
                self.pbar = tqdm(total=total_rounds, desc="🌳 XGBoost Training", unit="tree", ncols=100)
                self.total_rounds = total_rounds
                
            def after_iteration(self, model, epoch, evals_log):
                self.pbar.update(1)
                # Update progress bar with metrics
                if evals_log:
                    train_log = evals_log.get('train', {})
                    if train_log:
                        # Get last metric value
                        metric_key = list(train_log.keys())[0] if train_log else 'mlogloss'
                        train_metric = train_log[metric_key][-1] if metric_key in train_log else 0
                        postfix = {'train_loss': f'{train_metric:.4f}'}
                        
                        # Add validation metric if available
                        val_log = evals_log.get('val', {})
                        if val_log and metric_key in val_log:
                            val_metric = val_log[metric_key][-1]
                            postfix['val_loss'] = f'{val_metric:.4f}'
                        
                        self.pbar.set_postfix(postfix)
                return False  # Continue training
            
            def after_training(self, model):
                self.pbar.close()
                return model
        
        progress_callback = ProgressCallback(n_estimators)
        callbacks = [progress_callback]
        
        model = xgb.train(
            params,
            dtrain,
            num_boost_round=n_estimators,
            evals=evals,
            early_stopping_rounds=early_stopping_rounds,
            callbacks=callbacks,
            verbose_eval=False  # Disable default verbose to use progress bar
        )
    except (ImportError, AttributeError):
        # Fallback if tqdm not available or callback API changed
        try:
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=n_estimators,
                evals=evals,
                early_stopping_rounds=50,
                verbose_eval=10  # Show progress every 10 iterations
            )
        except Exception as e:
            # Final fallback
            print(f"⚠️  Progress bar not available, using basic verbose output")
            model = xgb.train(
                params,
                dtrain,
                num_boost_round=n_estimators,
                evals=evals,
                early_stopping_rounds=50,
                verbose_eval=50
            )

    # Evaluate
    train_pred = model.predict(dtrain)
    train_acc = accuracy_score(y_train, train_pred)
    
    print("-" * 60)
    print(f"✅ Training complete!")
    print(f"   Train accuracy: {train_acc:.3f}")
    
    # Validation evaluation (only if validation set exists)
    if len(X_val) > 0:
        val_pred = model.predict(dval)
        val_acc = accuracy_score(y_val, val_pred)
        print(f"   Val accuracy: {val_acc:.3f}")
        
        # Classification report
        print("\n📊 Validation Classification Report:")
        print(classification_report(y_val, val_pred))
    else:
        val_acc = float('nan')
        print(f"   Val accuracy: N/A (no validation set)")
    
    return model, train_acc, val_acc


def main():
    parser = argparse.ArgumentParser(description='Train XGBoost model')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (e.g., 1h, 4h)')
    parser.add_argument('--market', type=str, default='futures', help='Market type (spot or futures)')
    parser.add_argument('--task', type=str, default='pattern_classification',
                       choices=['pattern_classification', 'trend_classification'],
                       help='Classification task')
    parser.add_argument('--n-estimators', type=int, default=500, help='Number of trees')
    parser.add_argument('--max-depth', type=int, default=6, help='Maximum tree depth')
    parser.add_argument('--lr', type=float, default=0.1, help='Learning rate')
    parser.add_argument('--tree-method', type=str, default='auto', 
                       choices=['auto', 'hist', 'gpu_hist', 'approx'],
                       help='Tree construction method (auto=detect GPU, hist=CPU, gpu_hist=GPU)')
    parser.add_argument('--data-dir', type=str, default='data/advanced', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='data/models', help='Output directory')
    parser.add_argument('--days', type=int, default=None, help='Load only last N days of data (faster training)')
    parser.add_argument('--limit', type=int, default=None, help='Load only last N candles (alternative to --days)')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🤖 XGBOOST MODEL - TRAINING SCRIPT")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Task: {args.task}")
    print(f"N estimators: {args.n_estimators}")
    print(f"Max depth: {args.max_depth}")
    print(f"Learning rate: {args.lr}")
    print("=" * 60)
    print()

    # 1. Load data
    df = load_data(args.symbol, args.timeframe, args.market, args.data_dir, 
                   days=args.days, limit=args.limit)

    # 2. Prepare features (now includes train/val split internally)
    X_train, X_val, y_train, y_val, scaler, feature_cols = prepare_features(df, args.task)

    print(f"\n📊 Data split:")
    print(f"   Train: {len(X_train)} samples")
    print(f"   Val: {len(X_val)} samples")

    # 4. Train model
    model, train_acc, val_acc = train_model(
        X_train, y_train, X_val, y_val,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.lr,
        tree_method=args.tree_method
    )

    # 5. Feature importance
    print("\n🔍 Top 10 Most Important Features:")
    importance = model.get_score(importance_type='gain')
    importance_sorted = sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]

    for i, (feat_idx, score) in enumerate(importance_sorted, 1):
        # XGBoost uses f0, f1, ... naming
        feat_name = feature_cols[int(feat_idx[1:])]
        print(f"   {i:2d}. {feat_name:20s} : {score:.2f}")

    # 6. Save model and metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"xgboost_{args.task}_{args.symbol}_{args.timeframe}_{timestamp}"

    model_path = output_dir / f"{model_name}.json"
    scaler_path = output_dir / f"{model_name}_scaler.pkl"
    metadata_path = output_dir / f"{model_name}_metadata.json"

    # Save model (XGBoost native format)
    model.save_model(str(model_path))

    # Save scaler
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)

    # Save metadata
    metadata = {
        'model_name': model_name,
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'task': args.task,
        'trained_at': timestamp,
        'train_accuracy': float(train_acc),
        'val_accuracy': float(val_acc),
        'n_estimators': args.n_estimators,
        'max_depth': args.max_depth,
        'learning_rate': args.lr,
        'feature_count': len(feature_cols),
        'feature_names': feature_cols
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Model saved:")
    print(f"   Model: {model_path}")
    print(f"   Scaler: {scaler_path}")
    print(f"   Metadata: {metadata_path}")
    print()
    print("=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print()
    print("🎯 Next steps:")
    print("   1. Test the model with new data")
    print("   2. Integrate into prediction pipeline")
    print("   3. Monitor performance in production")
    print()


if __name__ == '__main__':
    main()
