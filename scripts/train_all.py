#!/usr/bin/env python3
"""
Multi-Everything Model Trainer
Trains models on all downloaded data (multi-coin, multi-timeframe, multi-market)

Usage:
    python scripts/train_all.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import time
from datetime import datetime
from typing import List, Dict
import json

# ============================================
# CONFIGURATION
# ============================================

CONFIGS = {
    # Data directory
    "data_dir": "data/advanced",

    # Models to train
    "models": ["xgboost"],  # Start with just xgboost for testing

    # Epochs
    "epochs": {
        "ppo": 5,
        "ensemble": 1,
        "lstm": 20,
    },

    # Device
    "device": "cpu",  # Use CPU for compatibility

    # Separate models
    "separate_by_market": True,
    "separate_by_timeframe": True,

    # Filters
    "timeframes": ["1d"],  # Only 1d for now
    "markets": None,  # All markets

    # Output
    "output_dir": "data/models",

    # Model-specific hyperparameters
    "ppo": {
        "total_timesteps": 50_000,
        "batch_size": 64,
        "learning_rate": 3e-4,
        "days": 60,
    },

    "lstm": {
        "seq_len": 30,
        "hidden_size": 128,
        "num_layers": 2,
        "learning_rate": 1e-3,
        "days": 60,
    },

    "ensemble": {
        "models": ["xgboost"],
        "days": 60,
        "xgboost": {
            "n_estimators": 200,
            "learning_rate": 0.1,
            "max_depth": 4,
            "tree_method": "auto",
        },
    },

    "seed": 42,
}


def find_data_files(data_dir: str, timeframes: List[str] = None, markets: List[str] = None) -> Dict[str, List[str]]:
    """
    Find all parquet files and group by market and timeframe

    Returns:
        dict: {'spot_1d': ['file1.parquet', ...], ...}
    """
    data_dir = Path(data_dir)
    files = {}

    for parquet_file in data_dir.glob("*_multi.parquet"):
        # Parse: SYMBOL_TF_MARKET_multi.parquet
        parts = parquet_file.stem.split('_')

        if len(parts) >= 3:
            symbol = parts[0]
            timeframe = parts[1]
            market = parts[2]

            # Apply filters
            if timeframes and timeframe not in timeframes:
                continue
            if markets and market not in markets:
                continue

            key = f"{market}_{timeframe}"
            if key not in files:
                files[key] = []
            files[key].append(str(parquet_file))

    return files


def train_model(model_type: str, data_files: List[str], output_name: str,
                epochs: int, device: str, hyperparams: Dict) -> Dict:
    """Train a single model"""
    start_time = time.time()

    print(f"\n{'='*80}")
    print(f"🎓 Training {model_type.upper()}: {output_name}")
    print(f"{'='*80}")
    print(f"📊 Data files: {len(data_files)}")
    print(f"⚙️  Epochs/Steps: {epochs}")
    print(f"🖥️  Device: {device}")

    # Select wrapper script
    if model_type == "ppo":
        script = "backend/training/quick_train_ppo.py"
    elif model_type == "ensemble" or model_type == "xgboost":
        script = "backend/training/train_ensemble_quick.py"
    elif model_type == "lstm":
        script = "backend/training/train_lstm_quick.py"
    else:
        return {"status": "error", "error": f"Unknown model: {model_type}"}

    # Save hyperparams
    hyperparams_file = Path(CONFIGS['output_dir']) / f"{output_name}_hyperparams.json"
    hyperparams_file.parent.mkdir(parents=True, exist_ok=True)

    with open(hyperparams_file, 'w') as f:
        json.dump(hyperparams, f, indent=2)

    # Build command
    cmd = [
        sys.executable, script,
        "--data-files", ",".join(data_files),
        "--epochs", str(epochs),
        "--device", device,
        "--output-name", output_name,
        "--hyperparams", str(hyperparams_file),
        "--seed", str(CONFIGS.get('seed', 42)),
    ]

    try:
        project_root = Path(__file__).parent.parent

        print(f"\n🚀 Starting training...")

        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=7200
        )

        # Print output (last 50 lines)
        if result.stdout:
            lines = result.stdout.split('\n')
            print('\n'.join(lines[-50:]))

        if result.stderr and result.returncode != 0:
            print("\nErrors:")
            print(result.stderr[:1000])

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ Training complete in {elapsed/60:.1f} minutes")
            return {
                "status": "success",
                "elapsed": elapsed,
                "model_type": model_type,
                "output_name": output_name,
            }
        else:
            error_msg = result.stderr[:1000] if result.stderr else "Unknown error"
            print(f"\n❌ Training failed")
            return {
                "status": "failed",
                "elapsed": elapsed,
                "error": error_msg,
            }

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {
            "status": "error",
            "elapsed": time.time() - start_time,
            "error": str(e),
        }


def main():
    """Main training orchestrator"""

    print("\n" + "="*80)
    print("🎓 MULTI-EVERYTHING MODEL TRAINER")
    print("="*80)

    # Find data files
    print(f"\n📁 Scanning {CONFIGS['data_dir']} for parquet files...")

    timeframes = CONFIGS.get('timeframes')
    markets = CONFIGS.get('markets')

    if timeframes:
        print(f"   ⏱️  Filtering timeframes: {timeframes}")

    data_groups = find_data_files(CONFIGS['data_dir'], timeframes, markets)

    if not data_groups:
        print(f"\n❌ No parquet files found in {CONFIGS['data_dir']}")
        print(f"   Make sure you have files like: BTCUSDT_1d_futures_multi.parquet")
        return False

    print(f"\n✅ Found {len(data_groups)} data groups:")
    for group_name, files in data_groups.items():
        print(f"   - {group_name}: {len(files)} files")

    # Create training tasks
    training_tasks = []
    for group_name, files in data_groups.items():
        for model_type in CONFIGS['models']:
            training_tasks.append({
                'group_name': group_name,
                'model_type': model_type,
                'files': files,
            })

    print(f"\n📋 Total training tasks: {len(training_tasks)}")
    print(f"🖥️  Device: {CONFIGS['device']}")

    for i, task in enumerate(training_tasks, 1):
        print(f"\n   Task {i}: {task['model_type'].upper()} on {task['group_name']} ({len(task['files'])} files)")

    input("\nPress ENTER to start training...")

    # Train models with progress bar
    results = []
    start_time = time.time()

    # Progress bar for tasks
    try:
        from tqdm import tqdm
        task_pbar = tqdm(enumerate(training_tasks, 1), total=len(training_tasks),
                        desc="📋 Overall Progress", unit="task", ncols=100)
    except ImportError:
        task_pbar = enumerate(training_tasks, 1)

    for i, task in task_pbar:
        if hasattr(task_pbar, 'set_description'):
            task_pbar.set_description(f"📋 Task {i}/{len(training_tasks)}: {task['model_type'].upper()} ({task['group_name']})")

        print(f"\n{'='*80}")
        print(f"📊 TASK {i}/{len(training_tasks)}")
        print(f"{'='*80}")

        output_name = f"{task['group_name']}_{task['model_type']}"
        epochs = CONFIGS['epochs'].get(task['model_type'], 100)

        result = train_model(
            model_type=task['model_type'],
            data_files=task['files'],
            output_name=output_name,
            epochs=epochs,
            device=CONFIGS['device'],
            hyperparams=CONFIGS[task['model_type']],
        )

        results.append(result)

        # Update progress bar
        if hasattr(task_pbar, 'set_postfix'):
            status_icon = "✅" if result['status'] == 'success' else "❌"
            task_pbar.set_postfix({
                'status': status_icon,
                'time': f"{result['elapsed']/60:.1f}m"
            })

    if hasattr(task_pbar, 'close'):
        task_pbar.close()

    # Summary
    total_elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("📊 TRAINING SUMMARY")
    print("="*80)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    print(f"✅ Success: {success_count}/{len(training_tasks)}")
    print(f"❌ Failed: {failed_count}/{len(training_tasks)}")
    print(f"⏱️  Total time: {total_elapsed/60:.1f} minutes")

    # Save results
    results_file = Path(CONFIGS['output_dir']) / f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(results_file, 'w') as f:
        json.dump({
            'config': CONFIGS,
            'total_elapsed': total_elapsed,
            'results': results,
        }, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")
    print(f"\n{'='*80}")
    print("🎉 TRAINING COMPLETE!")
    print(f"{'='*80}\n")

    return success_count == len(training_tasks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
