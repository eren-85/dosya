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


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost model"""
    logger.info("\n🌲 Training XGBoost...")

    model = xgb.XGBRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        tree_method='hist'  # CPU-friendly
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


def train_lightgbm(X_train, y_train, X_test, y_test):
    """Train LightGBM model"""
    logger.info("\n💡 Training LightGBM...")

    model = lgb.LGBMRegressor(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1
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


def train_catboost(X_train, y_train, X_test, y_test):
    """Train CatBoost model"""
    logger.info("\n🐱 Training CatBoost...")

    model = CatBoostRegressor(
        iterations=100,
        depth=5,
        learning_rate=0.1,
        random_state=42,
        verbose=False
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

    xgb_model, xgb_score = train_xgboost(X_train, y_train, X_test, y_test)
    models['xgboost'] = xgb_model
    scores['xgboost'] = xgb_score

    lgb_model, lgb_score = train_lightgbm(X_train, y_train, X_test, y_test)
    models['lightgbm'] = lgb_model
    scores['lightgbm'] = lgb_score

    cat_model, cat_score = train_catboost(X_train, y_train, X_test, y_test)
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

    parser = argparse.ArgumentParser(description='Train Ensemble Models')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1d', help='Candle timeframe')
    parser.add_argument('--market', type=str, default='futures', help='spot or futures')
    parser.add_argument('--no-advanced', action='store_true', help='Disable advanced features')
    args = parser.parse_args()

    models, weights = train_ensemble(
        symbol=args.symbol,
        timeframe=args.timeframe,
        market_type=args.market,
        use_advanced=not args.no_advanced
    )
