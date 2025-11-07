"""
Quick Ensemble Training (XGBoost + LightGBM + CatBoost)
Predict next price movement for trading decisions
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor
import pickle
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_prediction_data(df: pd.DataFrame, prediction_horizon: int = 1):
    """
    Prepare data for price prediction

    Args:
        df: DataFrame with OHLCV + indicators
        prediction_horizon: Number of steps ahead to predict (1 = next candle)

    Returns:
        X (features), y (target price change)
    """
    logger.info(f"Preparing prediction data (horizon={prediction_horizon})...")

    # Target: future price change percentage
    df['target'] = df['close'].pct_change(prediction_horizon).shift(-prediction_horizon)

    # Drop NaN
    df_clean = df.dropna()

    # Features (exclude OHLCV and metadata)
    feature_cols = [col for col in df_clean.columns if col not in [
        'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'quote_asset_volume',
        'trades', 'taker_base', 'taker_quote', 'ignore',
        'target'
    ]]

    X = df_clean[feature_cols]
    y = df_clean['target']

    logger.info(f"Features: {len(feature_cols)}")
    logger.info(f"Samples: {len(X)}")

    return X, y


def train_xgboost(X_train, y_train, X_test, y_test, hyperparams=None):
    """Train XGBoost model"""
    logger.info("\n🌲 Training XGBoost...")

    if hyperparams is None:
        hyperparams = {}

    model = xgb.XGBRegressor(
        n_estimators=hyperparams.get('n_estimators', 100),
        max_depth=hyperparams.get('max_depth', 6),
        learning_rate=hyperparams.get('learning_rate', 0.05),
        subsample=hyperparams.get('subsample', 0.8),
        colsample_bytree=hyperparams.get('colsample_bytree', 0.8),
        reg_alpha=hyperparams.get('reg_alpha', 0.1),
        reg_lambda=hyperparams.get('reg_lambda', 0.1),
        min_child_weight=hyperparams.get('min_child_weight', 1),
        random_state=42,
        tree_method=hyperparams.get('tree_method', 'gpu_hist')  # GPU by default
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_mae = mean_absolute_error(y_test, test_pred)
    test_r2 = r2_score(y_test, test_pred)

    logger.info(f"   Train RMSE: {train_rmse:.6f}")
    logger.info(f"   Test RMSE:  {test_rmse:.6f}")
    logger.info(f"   Test MAE:   {test_mae:.6f}")
    logger.info(f"   Test R²:    {test_r2:.6f}")

    return model, test_rmse


def train_lightgbm(X_train, y_train, X_test, y_test, hyperparams=None):
    """Train LightGBM model"""
    logger.info("\n💡 Training LightGBM...")

    if hyperparams is None:
        hyperparams = {}

    model = lgb.LGBMRegressor(
        n_estimators=hyperparams.get('n_estimators', 1200),
        max_depth=hyperparams.get('max_depth', 6),
        num_leaves=hyperparams.get('num_leaves', 63),
        learning_rate=hyperparams.get('learning_rate', 0.05),
        subsample=hyperparams.get('subsample', 0.8),
        colsample_bytree=hyperparams.get('colsample_bytree', 0.8),
        reg_alpha=hyperparams.get('reg_alpha', 0.1),
        reg_lambda=hyperparams.get('reg_lambda', 0.1),
        min_child_samples=hyperparams.get('min_child_samples', 20),
        random_state=42,
        verbose=hyperparams.get('verbose', -1)
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        callbacks=[lgb.early_stopping(10), lgb.log_evaluation(0)]
    )

    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_mae = mean_absolute_error(y_test, test_pred)
    test_r2 = r2_score(y_test, test_pred)

    logger.info(f"   Train RMSE: {train_rmse:.6f}")
    logger.info(f"   Test RMSE:  {test_rmse:.6f}")
    logger.info(f"   Test MAE:   {test_mae:.6f}")
    logger.info(f"   Test R²:    {test_r2:.6f}")

    return model, test_rmse


def train_catboost(X_train, y_train, X_test, y_test, hyperparams=None):
    """Train CatBoost model"""
    logger.info("\n🐱 Training CatBoost...")

    if hyperparams is None:
        hyperparams = {}

    model = CatBoostRegressor(
        iterations=hyperparams.get('iterations', 1200),
        depth=hyperparams.get('depth', 6),
        learning_rate=hyperparams.get('learning_rate', 0.05),
        subsample=hyperparams.get('subsample', 0.8),
        colsample_bylevel=hyperparams.get('colsample_bylevel', 0.8),
        reg_lambda=hyperparams.get('reg_lambda', 0.1),
        task_type=hyperparams.get('task_type', 'GPU'),
        random_state=42,
        verbose=hyperparams.get('verbose', False)
    )

    model.fit(X_train, y_train, eval_set=(X_test, y_test))

    # Evaluate
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)

    train_rmse = np.sqrt(mean_squared_error(y_train, train_pred))
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_mae = mean_absolute_error(y_test, test_pred)
    test_r2 = r2_score(y_test, test_pred)

    logger.info(f"   Train RMSE: {train_rmse:.6f}")
    logger.info(f"   Test RMSE:  {test_rmse:.6f}")
    logger.info(f"   Test MAE:   {test_mae:.6f}")
    logger.info(f"   Test R²:    {test_r2:.6f}")

    return model, test_rmse


def train_ensemble(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    market_type: str = "futures",
    save_dir: str = "/home/user/dosya/backend/models/saved",
    use_advanced: bool = True
):
    """
    Train ensemble of models (XGBoost + LightGBM + CatBoost)

    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        market_type: 'spot' or 'futures'
        save_dir: Directory to save trained models
        use_advanced: Use advanced multi-exchange features if available
    """

    logger.info("🤖 Starting Ensemble Training")
    logger.info(f"   Symbol: {symbol} {timeframe} {market_type}")
    logger.info(f"   Advanced mode: {use_advanced}")

    # Load and prepare data (will auto-detect advanced data)
    from backend.training.prepare_rl_data import prepare_training_data

    df = prepare_training_data(
        symbol=symbol,
        timeframe=timeframe,
        market_type=market_type,
        use_advanced=use_advanced
    )
    logger.info(f"   Loaded {len(df)} candles with {len(df.columns)} features")

    # Prepare prediction data
    X, y = prepare_prediction_data(df, prediction_horizon=1)

    # Train/test split (time-series aware)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"   Train: {len(X_train)} samples")
    logger.info(f"   Test:  {len(X_test)} samples")

    # Train models
    models = {}
    scores = {}

    # Extract hyperparameters if provided
    hyperparams = use_advanced if isinstance(use_advanced, dict) else {}

    xgb_params = hyperparams.get('xgboost', {})
    lgb_params = hyperparams.get('lightgbm', {})
    cat_params = hyperparams.get('catboost', {})

    xgb_model, xgb_score = train_xgboost(X_train, y_train, X_test, y_test, xgb_params)
    models['xgboost'] = xgb_model
    scores['xgboost'] = xgb_score

    lgb_model, lgb_score = train_lightgbm(X_train, y_train, X_test, y_test, lgb_params)
    models['lightgbm'] = lgb_model
    scores['lightgbm'] = lgb_score

    cat_model, cat_score = train_catboost(X_train, y_train, X_test, y_test, cat_params)
    models['catboost'] = cat_model
    scores['catboost'] = cat_score

    # Ensemble prediction (weighted average)
    logger.info("\n🔮 Ensemble Prediction...")

    # Inverse weights (better model = higher weight)
    weights = {name: 1/score for name, score in scores.items()}
    total_weight = sum(weights.values())
    weights = {name: w/total_weight for name, w in weights.items()}

    logger.info(f"   Weights: {weights}")

    # Ensemble prediction
    ensemble_pred = (
        weights['xgboost'] * xgb_model.predict(X_test) +
        weights['lightgbm'] * lgb_model.predict(X_test) +
        weights['catboost'] * cat_model.predict(X_test)
    )

    ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
    ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
    ensemble_r2 = r2_score(y_test, ensemble_pred)

    logger.info(f"   Ensemble RMSE: {ensemble_rmse:.6f}")
    logger.info(f"   Ensemble MAE:  {ensemble_mae:.6f}")
    logger.info(f"   Ensemble R²:   {ensemble_r2:.6f}")

    # Save models
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)

    for name, model in models.items():
        model_file = save_path / f"{name}_{symbol.lower()}_{timeframe}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"   Saved: {model_file}")

    # Save weights
    weights_file = save_path / f"ensemble_weights_{symbol.lower()}_{timeframe}.pkl"
    with open(weights_file, 'wb') as f:
        pickle.dump(weights, f)
    logger.info(f"   Saved: {weights_file}")

    # Save feature names
    features_file = save_path / f"feature_names_{symbol.lower()}_{timeframe}.pkl"
    with open(features_file, 'wb') as f:
        pickle.dump(list(X.columns), f)
    logger.info(f"   Saved: {features_file}")

    logger.info("\n✅ Ensemble training complete!")

    return models, weights


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description='Train Ensemble Models (Batch Mode)')

    # Batch training parameters
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet file paths')
    parser.add_argument('--epochs', type=int, default=1, help='Not used for ensemble (uses early_stopping)')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'], help='Training device')
    parser.add_argument('--output-name', type=str, required=True, help='Output model name (e.g., spot_1h_ensemble)')
    parser.add_argument('--hyperparams', type=str, required=True, help='Path to hyperparameters JSON file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--eval-config', type=str, help='Path to evaluation config JSON file')

    # Legacy parameters (for backward compatibility)
    parser.add_argument('--symbol', type=str, help='Trading symbol (legacy mode)')
    parser.add_argument('--timeframe', type=str, help='Candle timeframe (legacy mode)')
    parser.add_argument('--market', type=str, help='spot or futures (legacy mode)')
    parser.add_argument('--no-advanced', action='store_true', help='Disable advanced features (legacy mode)')

    args = parser.parse_args()

    # Set random seed
    np.random.seed(args.seed)
    import random
    random.seed(args.seed)

    # Load hyperparameters
    with open(args.hyperparams, 'r') as f:
        hyperparams = json.load(f)

    logger.info(f"🤖 Starting Ensemble Batch Training")
    logger.info(f"   Output: {args.output_name}")
    logger.info(f"   Device: {args.device}")
    logger.info(f"   Seed: {args.seed}")
    logger.info(f"   Models: {', '.join(hyperparams.get('models', ['lightgbm', 'xgboost', 'catboost']))}")

    # Load data files
    data_file_paths = args.data_files.split(',')
    logger.info(f"   Loading {len(data_file_paths)} data files...")

    dfs = []
    for file_path in data_file_paths:
        df = pd.read_parquet(file_path.strip())
        logger.info(f"      - {Path(file_path).name}: {len(df)} rows")
        dfs.append(df)

    # Concatenate all data
    df_combined = pd.concat(dfs, ignore_index=True).sort_values('open_time').reset_index(drop=True)
    logger.info(f"   Combined data: {len(df_combined)} rows")

    # Prepare prediction data
    X, y = prepare_prediction_data(df_combined, prediction_horizon=1)

    # Train/test split (time-series aware)
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"   Train: {len(X_train)} samples")
    logger.info(f"   Test:  {len(X_test)} samples")

    # Train models
    models = {}
    scores = {}

    xgb_params = hyperparams.get('xgboost', {})
    lgb_params = hyperparams.get('lightgbm', {})
    cat_params = hyperparams.get('catboost', {})

    xgb_model, xgb_score = train_xgboost(X_train, y_train, X_test, y_test, xgb_params)
    models['xgboost'] = xgb_model
    scores['xgboost'] = xgb_score

    lgb_model, lgb_score = train_lightgbm(X_train, y_train, X_test, y_test, lgb_params)
    models['lightgbm'] = lgb_model
    scores['lightgbm'] = lgb_score

    cat_model, cat_score = train_catboost(X_train, y_train, X_test, y_test, cat_params)
    models['catboost'] = cat_model
    scores['catboost'] = cat_score

    # Ensemble prediction (weighted average)
    logger.info("\n🔮 Ensemble Prediction...")

    # Inverse weights (better model = higher weight)
    weights = {name: 1/score for name, score in scores.items()}
    total_weight = sum(weights.values())
    weights = {name: w/total_weight for name, w in weights.items()}

    logger.info(f"   Weights: {weights}")

    # Ensemble prediction
    ensemble_pred = (
        weights['xgboost'] * xgb_model.predict(X_test) +
        weights['lightgbm'] * lgb_model.predict(X_test) +
        weights['catboost'] * cat_model.predict(X_test)
    )

    ensemble_rmse = np.sqrt(mean_squared_error(y_test, ensemble_pred))
    ensemble_mae = mean_absolute_error(y_test, ensemble_pred)
    ensemble_r2 = r2_score(y_test, ensemble_pred)

    logger.info(f"   Ensemble RMSE: {ensemble_rmse:.6f}")
    logger.info(f"   Ensemble MAE:  {ensemble_mae:.6f}")
    logger.info(f"   Ensemble R²:   {ensemble_r2:.6f}")

    # Save models
    save_path = Path("data/models")
    save_path.mkdir(parents=True, exist_ok=True)

    for name, model in models.items():
        model_file = save_path / f"{args.output_name}_{name}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        logger.info(f"   Saved: {model_file}")

    # Save weights
    weights_file = save_path / f"{args.output_name}_weights.pkl"
    with open(weights_file, 'wb') as f:
        pickle.dump(weights, f)
    logger.info(f"   Saved: {weights_file}")

    # Save feature names
    features_file = save_path / f"{args.output_name}_features.pkl"
    with open(features_file, 'wb') as f:
        pickle.dump(list(X.columns), f)
    logger.info(f"   Saved: {features_file}")

    logger.info("\n✅ Ensemble training complete!")
