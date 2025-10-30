
# Background tasks for Sigma Analyst (patched)
# - Adds tolerant signatures (**kwargs) to avoid TypeError from extra kwargs
# - run_daily_analysis now accepts timeframes
# - collect_market_data accepts alias "timeframe" and "market" (spot/futures)
# - Consistent JSON-shaped results across tasks
# - Extra logging for easier debugging

import logging
from datetime import datetime, timezone

try:
    # When used inside the project package
    from .celery_app import celery_app
except Exception:
    # Allow standalone import for linting/tests (not used in production)
    from backend.tasks.celery_app import celery_app  # type: ignore

logger = logging.getLogger(__name__)

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

# ============================================
# DATA COLLECTION TASKS
# ============================================

@celery_app.task(name='backend.tasks.tasks.collect_market_data', bind=True)
def collect_market_data(self, symbols=None, interval='1h', timeframe=None, market='spot', **kwargs):
    """
    Collect market data from exchanges.

    Args:
        symbols (list[str]): Symbols like ['BTCUSDT', 'ETHUSDT'].
        interval (str): Timeframe alias kept for backward compat (e.g., '1h').
        timeframe (str|None): Preferred name for timeframe. If provided, overrides interval.
        market (str): 'spot' or 'futures' (informational for downstream collectors).

    Returns:
        dict: Collection results (placeholder, real collectors plug-in here).
    """
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT']

    tf = timeframe or interval
    logger.info("🔄 [collect_market_data] symbols=%s timeframe=%s market=%s kwargs=%s",
                symbols, tf, market, {k: v for k, v in kwargs.items() if k != 'ctx'})

    # TODO: Plug real collectors here
    result = {
        'status': 'success',
        'symbols': symbols,
        'timeframe': tf,
        'market': market,
        'timestamp': _now_iso(),
        'records': 0  # placeholder
    }
    logger.info("✅ [collect_market_data] completed: %s (%s)", symbols, tf)
    return result

# ============================================
# ANALYSIS TASKS
# ============================================

@celery_app.task(name='backend.tasks.tasks.run_daily_analysis', bind=True)
def run_daily_analysis(self, symbols=None, timeframes=None, **kwargs):
    """
    Run daily market analysis.

    Args:
        symbols (list[str]|None): Trading pairs to analyze.
        timeframes (list[str]|str|None): Optional TFs passed by some callers; accepted & logged.
        **kwargs: Tolerate extra args from older/newer CLIs.

    Returns:
        dict: Analysis results.
    """
    if symbols is None:
        symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']

    logger.info("📊 [run_daily_analysis] symbols=%s timeframes=%s kwargs=%s",
                symbols, timeframes, {k: v for k, v in kwargs.items() if k != 'ctx'})

    # TODO: Implement actual analysis
    result = {
        'status': 'success',
        'symbols': symbols,
        'timeframes': timeframes,
        'timestamp': _now_iso(),
        'analyses_count': len(symbols)
    }
    logger.info("✅ [run_daily_analysis] completed: %d symbols", len(symbols))
    return result


@celery_app.task(name='backend.tasks.tasks.run_backtest', bind=True)
def run_backtest(self, symbol, strategy, start_date, end_date, **kwargs):
    """
    Run backtest for a strategy.

    Args:
        symbol (str): Pair like 'BTCUSDT'.
        strategy (str): Strategy name.
        start_date (str): 'YYYY-MM-DD'
        end_date (str): 'YYYY-MM-DD'
        **kwargs: Tolerate extra args

    Returns:
        dict: Backtest results.
    """
    logger.info("🧪 [run_backtest] symbol=%s strategy=%s period=%s→%s kwargs=%s",
                symbol, strategy, start_date, end_date,
                {k: v for k, v in kwargs.items() if k != 'ctx'})

    # TODO: Implement backtest
    result = {
        'status': 'success',
        'symbol': symbol,
        'strategy': strategy,
        'period': f"{start_date} → {end_date}",
        'timestamp': _now_iso()
    }
    logger.info("✅ [run_backtest] completed: %s", symbol)
    return result

# ============================================
# MODEL TRAINING TASKS
# ============================================

@celery_app.task(name='backend.tasks.tasks.train_ensemble_model', bind=True)
def train_ensemble_model(self, symbol, timeframe='1h', **kwargs):
    """
    Train ensemble model (XGBoost + LightGBM + CatBoost).

    Args:
        symbol (str): Pair like 'BTCUSDT'.
        timeframe (str): TF string.
        **kwargs: Tolerate extra args (e.g., cv params).

    Returns:
        dict: Training results.
    """
    logger.info("🏋️ [train_ensemble_model] symbol=%s timeframe=%s kwargs=%s",
                symbol, timeframe, {k: v for k, v in kwargs.items() if k != 'ctx'})

    # TODO: Implement model training
    result = {
        'status': 'success',
        'symbol': symbol,
        'timeframe': timeframe,
        'timestamp': _now_iso()
    }
    logger.info("✅ [train_ensemble_model] completed: %s (%s)", symbol, timeframe)
    return result


@celery_app.task(name='backend.tasks.tasks.train_deep_learning_model', bind=True)
def train_deep_learning_model(self, symbol, model_type='lstm', timeframe='1h', **kwargs):
    """
    Train deep learning model (LSTM/Transformer).

    Args:
        symbol (str)
        model_type (str): 'lstm' or 'transformer'
        timeframe (str)
        **kwargs: Extra args tolerated.

    Returns:
        dict
    """
    logger.info("🧠 [train_deep_learning_model] symbol=%s model=%s timeframe=%s kwargs=%s",
                symbol, model_type, timeframe,
                {k: v for k, v in kwargs.items() if k != 'ctx'})

    # TODO: Implement DL training
    result = {
        'status': 'success',
        'symbol': symbol,
        'model_type': model_type,
        'timeframe': timeframe,
        'timestamp': _now_iso()
    }
    logger.info("✅ [train_deep_learning_model] completed: %s (%s)", symbol, model_type)
    return result

# ============================================
# UTILITY TASKS
# ============================================

@celery_app.task(name='backend.tasks.tasks.health_check', bind=True)
def health_check(self, **kwargs):
    """Health check task for monitoring."""
    return {
        'status': 'healthy',
        'timestamp': _now_iso(),
        'service': 'celery_worker'
    }


@celery_app.task(name='backend.tasks.tasks.cleanup_old_data', bind=True)
def cleanup_old_data(self, days=30, **kwargs):
    """
    Cleanup old data files (placeholder).

    Args:
        days (int): Keep data newer than N days.
        **kwargs: Extra args tolerated.

    Returns:
        dict
    """
    logger.info("🧹 [cleanup_old_data] days=%d kwargs=%s", days,
                {k: v for k, v in kwargs.items() if k != 'ctx'})
    # TODO: Implement cleanup
    result = {
        'status': 'success',
        'days': days,
        'deleted_files': 0,
        'timestamp': _now_iso()
    }
    logger.info("✅ [cleanup_old_data] completed")
    return result
