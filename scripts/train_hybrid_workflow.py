"""
Hybrid Training Workflow
Trains models in optimal sequence for hybrid RL system

Workflow:
    1. Train Ensemble (XGBoost + LightGBM + CatBoost) → Supervised Learning
    2. Train Hybrid PPO (uses Ensemble predictions) → Reinforcement Learning
    3. (Optional) Train LSTM → Deep Learning

This creates a powerful ensemble of models where PPO benefits from
Ensemble's predictions while learning optimal timing and risk management.

Usage:
    python scripts/train_hybrid_workflow.py

Configuration:
    Edit CONFIGS below to customize
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import time
from datetime import datetime
from typing import List, Dict
import json
from glob import glob

# ============================================
# CONFIGURATION
# ============================================

CONFIGS = {
    # Data directory
    "data_dir": "data/advanced",

    # Symbols to train (leave empty for ALL downloaded symbols)
    "symbols": [],  # e.g., ["BTCUSDT", "ETHUSDT"] or [] for all

    # Timeframes to train (leave empty for ALL)
    "timeframes": [],  # e.g., ["5m", "1h"] or [] for all

    # Markets
    "markets": ["futures"],  # spot, futures, or both

    # Which models to train
    "train_ensemble": True,
    "train_hybrid_ppo": True,
    "train_lstm": False,  # Optional

    # Training parameters
    "device": "cuda",  # cuda or cpu
    "ensemble_market": "futures",  # Train Ensemble on futures data

    # PPO parameters (for hybrid)
    "ppo_total_timesteps": 100000,
    "ppo_learning_rate": 0.0003,

    # LSTM parameters
    "lstm_epochs": 50,

    # Output directory
    "output_dir": "data/models",
}


def find_parquet_files(data_dir: str, symbols: List[str] = None,
                       timeframes: List[str] = None, markets: List[str] = None) -> Dict:
    """
    Find all parquet files matching criteria

    Returns:
        dict grouped by symbol_timeframe_market
    """
    data_dir = Path(data_dir)
    files = {}

    # Get all parquet files
    pattern = "*_binance.parquet"
    all_files = list(data_dir.glob(pattern))

    print(f"📂 Found {len(all_files)} parquet files in {data_dir}")

    for filepath in all_files:
        # Parse filename: SYMBOL_TIMEFRAME_MARKET_binance.parquet
        parts = filepath.stem.replace('_binance', '').split('_')

        if len(parts) < 3:
            continue

        symbol = parts[0]
        timeframe = parts[1]
        market = parts[2]

        # Filter by criteria
        if symbols and symbol not in symbols:
            continue
        if timeframes and timeframe not in timeframes:
            continue
        if markets and market not in markets:
            continue

        key = f"{symbol}_{timeframe}_{market}"

        files[key] = str(filepath)

    print(f"✅ Selected {len(files)} files matching criteria")
    return files


def train_ensemble_model(symbol: str, timeframe: str, market: str, data_file: str, device: str, output_dir: str) -> str:
    """
    Train Ensemble model (XGBoost)

    Returns:
        Path to trained model
    """
    print("\n" + "="*80)
    print(f"🎓 TRAINING ENSEMBLE: {symbol} {timeframe} {market}")
    print("="*80)

    output_name = f"{symbol}_{timeframe}_{market}_xgb_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    model_path = Path(output_dir) / f"{output_name}.json"

    # Use CLI train command
    cmd = [
        "python", "-m", "backend.cli",
        "train",
        "--symbols", symbol,
        "--timeframes", timeframe,
        "--model-type", "ensemble",
        "--device", device,
        "--market", market,
    ]

    print(f"🚀 Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ Ensemble training complete in {elapsed/60:.1f} minutes")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

            # Find the actual model file
            pattern = f"{symbol}_{timeframe}_{market}_*xgb*.json"
            models = list(Path(output_dir).glob(pattern))

            if models:
                model_path = sorted(models, key=lambda p: p.stat().st_mtime)[-1]
                print(f"📊 Model saved: {model_path}")
                return str(model_path)
            else:
                print(f"⚠️  Model file not found, using expected path: {model_path}")
                return str(model_path)
        else:
            print(f"❌ Ensemble training failed!")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"❌ Training timed out after {elapsed/60:.1f} minutes")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def train_hybrid_ppo(symbol: str, timeframe: str, market: str, data_file: str,
                     ensemble_model: str, total_timesteps: int, learning_rate: float,
                     device: str, output_dir: str) -> str:
    """
    Train Hybrid PPO (uses Ensemble predictions)

    Returns:
        Path to trained model
    """
    print("\n" + "="*80)
    print(f"🤖 TRAINING HYBRID PPO: {symbol} {timeframe} {market}")
    print("="*80)
    print(f"   Using Ensemble: {ensemble_model}")

    cmd = [
        "python", "-m", "backend.training.train_ppo_hybrid",
        "--symbol", symbol,
        "--timeframe", timeframe,
        "--market", market,
        "--ensemble-model", ensemble_model,
        "--total-timesteps", str(total_timesteps),
        "--learning-rate", str(learning_rate),
        "--data-dir", Path(data_file).parent,
        "--output-dir", output_dir,
    ]

    print(f"🚀 Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ Hybrid PPO training complete in {elapsed/60:.1f} minutes")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

            # Find model file
            pattern = f"{symbol}_{timeframe}_{market}_ppo_hybrid_*.zip"
            models = list(Path(output_dir).glob(pattern))

            if models:
                model_path = sorted(models, key=lambda p: p.stat().st_mtime)[-1]
                print(f"📊 Model saved: {model_path}")
                return str(model_path)
            else:
                return None
        else:
            print(f"❌ Hybrid PPO training failed!")
            print(f"STDERR: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"❌ Training timed out after {elapsed/60:.1f} minutes")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def train_lstm_model(symbol: str, timeframe: str, market: str, data_file: str,
                     epochs: int, device: str, output_dir: str) -> str:
    """Train LSTM model"""
    print("\n" + "="*80)
    print(f"🧠 TRAINING LSTM: {symbol} {timeframe} {market}")
    print("="*80)

    cmd = [
        "python", "-m", "backend.cli",
        "train",
        "--symbols", symbol,
        "--timeframes", timeframe,
        "--model-type", "lstm",
        "--epochs", str(epochs),
        "--device", device,
        "--market", market,
    ]

    print(f"🚀 Running: {' '.join(cmd)}")
    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200  # 2 hour timeout
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ LSTM training complete in {elapsed/60:.1f} minutes")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            return "success"
        else:
            print(f"❌ LSTM training failed!")
            print(f"STDERR: {result.stderr}")
            return None

    except subprocess.TimeoutExpired:
        print(f"❌ Training timed out")
        return None


def main():
    print("\n" + "="*80)
    print("🚀 HYBRID TRAINING WORKFLOW")
    print("="*80)
    print()
    print("This workflow trains models in optimal sequence:")
    print("  1. Ensemble (XGBoost) - Supervised learning baseline")
    print("  2. Hybrid PPO - RL agent using Ensemble predictions")
    print("  3. LSTM (optional) - Deep learning model")
    print()
    print("="*80)
    print()

    # Find data files
    files = find_parquet_files(
        data_dir=CONFIGS['data_dir'],
        symbols=CONFIGS['symbols'] if CONFIGS['symbols'] else None,
        timeframes=CONFIGS['timeframes'] if CONFIGS['timeframes'] else None,
        markets=CONFIGS['markets']
    )

    if not files:
        print("❌ No data files found! Run download_all.py first.")
        return

    print(f"\n📋 Training plan: {len(files)} combinations")
    for key in files:
        print(f"   - {key}")

    input("\nPress ENTER to start training...")

    # Training results
    results = {
        'ensemble': {},
        'hybrid_ppo': {},
        'lstm': {}
    }

    total_start = time.time()

    # Train each combination
    for key, data_file in files.items():
        symbol, timeframe, market = key.split('_')

        print(f"\n\n{'#'*80}")
        print(f"📊 TRAINING: {symbol} {timeframe} {market}")
        print(f"{'#'*80}")

        # 1. Train Ensemble
        ensemble_model = None
        if CONFIGS['train_ensemble']:
            ensemble_model = train_ensemble_model(
                symbol=symbol,
                timeframe=timeframe,
                market=market,
                data_file=data_file,
                device=CONFIGS['device'],
                output_dir=CONFIGS['output_dir']
            )
            results['ensemble'][key] = ensemble_model

        # 2. Train Hybrid PPO (requires Ensemble)
        if CONFIGS['train_hybrid_ppo']:
            if not ensemble_model:
                print("⚠️  Skipping Hybrid PPO (no Ensemble model)")
            else:
                hybrid_ppo_model = train_hybrid_ppo(
                    symbol=symbol,
                    timeframe=timeframe,
                    market=market,
                    data_file=data_file,
                    ensemble_model=ensemble_model,
                    total_timesteps=CONFIGS['ppo_total_timesteps'],
                    learning_rate=CONFIGS['ppo_learning_rate'],
                    device=CONFIGS['device'],
                    output_dir=CONFIGS['output_dir']
                )
                results['hybrid_ppo'][key] = hybrid_ppo_model

        # 3. Train LSTM (optional)
        if CONFIGS['train_lstm']:
            lstm_model = train_lstm_model(
                symbol=symbol,
                timeframe=timeframe,
                market=market,
                data_file=data_file,
                epochs=CONFIGS['lstm_epochs'],
                device=CONFIGS['device'],
                output_dir=CONFIGS['output_dir']
            )
            results['lstm'][key] = lstm_model

    total_elapsed = time.time() - total_start

    # Print summary
    print("\n\n" + "="*80)
    print("📊 TRAINING SUMMARY")
    print("="*80)
    print(f"⏱️  Total time: {total_elapsed/60:.1f} minutes")
    print()

    print("✅ Ensemble models:")
    for key, path in results['ensemble'].items():
        status = "✅" if path else "❌"
        print(f"   {status} {key}: {path}")

    print("\n🤖 Hybrid PPO models:")
    for key, path in results['hybrid_ppo'].items():
        status = "✅" if path else "❌"
        print(f"   {status} {key}: {path}")

    if results['lstm']:
        print("\n🧠 LSTM models:")
        for key, path in results['lstm'].items():
            status = "✅" if path else "❌"
            print(f"   {status} {key}")

    print("\n" + "="*80)
    print("🎉 HYBRID TRAINING WORKFLOW COMPLETE!")
    print("="*80)
    print()
    print("🎯 Next steps:")
    print("   1. Test models with scripts/test_live_trading.py")
    print("   2. Compare model performance")
    print("   3. Use best model for live trading")
    print()

    # Save results
    results_file = Path(CONFIGS['output_dir']) / f"hybrid_training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"💾 Results saved: {results_file}")


if __name__ == "__main__":
    main()
