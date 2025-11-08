"""
Multi-Everything Model Trainer
Trains models on all downloaded data (multi-coin, multi-timeframe, multi-market)

Usage:
    python scripts/train_all.py

Configuration:
    Edit the CONFIGS section below to customize your training
"""

import sys
import io
import os

# Fix Windows encoding issue (support emojis and unicode)
if os.name == "nt":  # Windows
    if hasattr(sys.stdout, "reconfigure"):
        # Python 3.7+ has reconfigure method
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    else:
        # Fallback for older Python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess
import time
import argparse
from datetime import datetime
from typing import List, Dict
import json
import glob

# ============================================
# CONFIGURATION
# ============================================

CONFIGS = {
    # Data directory (where parquet files are)
    "data_dir": "data/advanced",

    # Models to train
    # NOTE: Şu an sadece baseline PPO kullanılıyor (train_ppo.py)
    # train_ppo_hybrid.py ve train_multimodal_ppo.py var ama train_all.py'de kullanılmıyor
    "models": [
        "ppo",      # Reinforcement Learning (PPO) - Baseline PPO
        "ensemble", # XGBoost + LightGBM + CatBoost
        "lstm",     # Bidirectional LSTM
    ],

    # Update-epoch counts (model-specific)
    # PPO: n_epochs (how many times to iterate over each batch)
    # Ensemble: not used (uses early_stopping instead)
    # LSTM: training epochs
    "epochs": {
        "ppo": 5,          # SB3 n_epochs parameter (reduced for faster training)
        "ensemble": 1,     # Not used (early_stopping handles this)
        "lstm": 20,        # Reduced for faster training
    },

    # Device (cuda or cpu)
    "device": "cuda",

    # Train separate models per market?
    "separate_by_market": True,  # spot vs futures models

    # Train separate models per timeframe?
    "separate_by_timeframe": True,  # 1h vs 4h vs 1d models
    
    # Filter: Only train on specific timeframes (None = all)
    "timeframes": ["1d"],  # Only 1d timeframe (1 günlük mumlar)
    
    # Filter: Only train on specific markets (None = all)
    "markets": None,  # All markets (spot + futures)

    # Output directory for models
    "output_dir": "data/models",

    # ============================================
    # PPO HYPERPARAMETERS (Stable-Baselines3)
    # ============================================
    "ppo": {
        "total_timesteps": 50_000,       # Total training steps (reduced for faster training)
        "n_steps": 1024,                 # Rollout buffer size (reduced)
        "batch_size": 64,                # Mini-batch size (reduced)
        "learning_rate": 3e-4,           # Initial learning rate
        "days": 60,                      # Use last 60 days of data (1-2 months for 1d timeframe)
        "clip_range": 0.2,               # PPO clipping parameter
        "gamma": 0.995,                  # Discount factor
        "gae_lambda": 0.97,              # GAE lambda
        "ent_coef": 0.001,               # Entropy coefficient (exploration)
        "vf_coef": 0.5,                  # Value function coefficient
        "max_grad_norm": 0.5,            # Gradient clipping
        "normalize_advantage": True,     # Normalize advantages
        "target_kl": 0.02,               # Target KL divergence (early stop)
        "policy_kwargs": {
            "net_arch": [256, 256],      # Policy network architecture
            "activation_fn": "tanh",     # Activation function
        },
        "use_sde": False,                # State-dependent exploration
        "sde_sample_freq": -1,
        "normalize_obs": True,           # Normalize observations
        "normalize_reward": True,        # Normalize rewards
    },

    # ============================================
    # LSTM HYPERPARAMETERS
    # ============================================
    "lstm": {
        "seq_len": 10,                   # Sequence length (lookback window) - reduced for small datasets
        "hidden_size": 128,              # LSTM hidden size (reduced)
        "num_layers": 2,                 # Number of LSTM layers
        "dropout": 0.2,                  # Dropout rate
        "learning_rate": 1e-3,           # Initial learning rate
        "batch_size": 16,                # Reduced batch size for small datasets
        "grad_clip": 0.5,                # Gradient clipping
        "early_stopping": True,          # Enable early stopping
        "patience": 5,                   # Early stopping patience (reduced)
        "reduce_lr_patience": 3,         # ReduceLROnPlateau patience (reduced)
        "reduce_lr_factor": 0.5,         # LR reduction factor
        "min_lr": 1e-6,                  # Minimum learning rate
        "bidirectional": True,           # Bidirectional LSTM
        "batch_first": True,
        "days": 60,                      # Use last 60 days of data (1-2 months for 1d timeframe)
    },

    # ============================================
    # ENSEMBLE HYPERPARAMETERS (LightGBM/XGBoost/CatBoost)
    # ============================================
    "ensemble": {
        "models": ["xgboost"],  # Only XGBoost for faster training (remove lightgbm, catboost)
        "days": 60,             # Use last 60 days of data (1-2 months for 1d timeframe)

        # LightGBM params
        "lightgbm": {
            "n_estimators": 200,         # Reduced
            "learning_rate": 0.1,        # Increased for faster convergence
            "max_depth": 4,              # Reduced
            "num_leaves": 15,            # Reduced
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
            "min_child_samples": 20,
            "early_stopping_rounds": 50, # Reduced
            "verbose": -1,
        },

        # XGBoost params
        "xgboost": {
            "n_estimators": 200,         # Reduced from 1200
            "learning_rate": 0.1,        # Increased for faster convergence
            "max_depth": 4,              # Reduced
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
            "min_child_weight": 1,
            "early_stopping_rounds": 50, # Reduced
            "tree_method": "gpu_hist",   # GPU method (faster if GPU available)
        },

        # CatBoost params
        "catboost": {
            "iterations": 200,           # Reduced
            "learning_rate": 0.1,        # Increased
            "depth": 4,                  # Reduced
            "subsample": 0.8,
            "colsample_bylevel": 0.8,
            "reg_lambda": 0.1,
            "early_stopping_rounds": 50, # Reduced
            "task_type": "CPU",          # CPU for faster setup
            "verbose": False,
        },

        # Ensemble strategy
        "ensemble_method": "voting",
        "voting_weights": [1.0],
    },

    # ============================================
    # EVALUATION & MONITORING
    # ============================================
    "evaluation": {
        "eval_every": 50_000,            # Evaluate every N steps (PPO)
        "metrics": [
            "sharpe",                    # Sharpe ratio
            "calmar",                    # Calmar ratio
            "maxdd",                     # Maximum drawdown
            "sortino",                   # Sortino ratio
            "win_rate",                  # Win rate
            "profit_factor",             # Profit factor
        ],
        "early_stop_metric": "calmar",   # Metric for early stopping
        "early_stop_patience": 5,        # Patience for early stopping
        "save_best_only": True,          # Only save best model
        "test_size": 0.2,                # Test set size (validation)
        "walk_forward": True,            # Walk-forward validation
        "walk_forward_window": 180,      # Days per window
    },

    # ============================================
    # TRAINING SETTINGS
    # ============================================
    "seed": 42,                          # Random seed (reproducibility)
    "mixed_precision": True,             # AMP (faster GPU training)
    "num_workers": 4,                    # DataLoader workers
    "pin_memory": True,                  # Pin memory for faster GPU transfer
    "verbose": 1,                        # Logging verbosity (0-2)
}

# ============================================
# TRAINING LOGIC
# ============================================

def find_data_files(data_dir: str, timeframes: List[str] = None, markets: List[str] = None) -> Dict[str, List[str]]:
    """
    Find all parquet files and group by market and timeframe
    
    Args:
        data_dir: Directory to search
        timeframes: List of timeframes to filter (e.g., ['1d']). None = all
        markets: List of markets to filter (e.g., ['futures']). None = all

    Returns:
        dict with structure:
        {
            'spot_1h': ['BTCUSDT_1h_spot_multi.parquet', ...],
            'futures_1h': ['BTCUSDT_1h_futures_multi.parquet', ...],
            ...
        }
    """
    data_dir = Path(data_dir)
    files = {}

    for parquet_file in data_dir.glob("*_multi.parquet"):
        # Parse filename: SYMBOL_TF_MARKET_multi.parquet
        parts = parquet_file.stem.split('_')

        if len(parts) >= 3:
            symbol = parts[0]
            timeframe = parts[1]
            market = parts[2]

            # Filter by timeframe if specified
            if timeframes is not None and timeframe not in timeframes:
                continue
            
            # Filter by market if specified
            if markets is not None and market not in markets:
                continue

            key = f"{market}_{timeframe}"

            if key not in files:
                files[key] = []

            files[key].append(str(parquet_file))

    return files


def train_model(model_type: str, data_files: List[str], output_name: str,
                epochs: int, device: str, hyperparams: Dict) -> Dict:
    """
    Train a single model

    Args:
        model_type: 'ppo', 'ensemble', or 'lstm'
        data_files: List of parquet file paths
        output_name: Output model name (e.g., 'spot_1h_ppo')
        epochs: Number of training epochs (model-specific)
        device: 'cuda' or 'cpu'
        hyperparams: Model-specific hyperparameters from CONFIGS

    Returns:
        dict with status and metrics
    """
    start_time = time.time()

    print(f"\n{'='*80}")
    print(f"🎓 Training {model_type.upper()}: {output_name}")
    print(f"{'='*80}")
    print(f"📊 Data files: {len(data_files)}")
    print(f"⚙️  Epochs/Steps: {epochs}")
    print(f"🖥️  Device: {device}")

    # Print key hyperparameters
    if model_type == "ppo":
        print(f"🎯 Total timesteps: {hyperparams.get('total_timesteps', '?'):,}")
        print(f"🎯 Batch size: {hyperparams.get('batch_size', '?')}")
        print(f"🎯 Learning rate: {hyperparams.get('learning_rate', '?')}")
    elif model_type == "lstm":
        print(f"🎯 Sequence length: {hyperparams.get('seq_len', '?')}")
        print(f"🎯 Hidden size: {hyperparams.get('hidden_size', '?')}")
    elif model_type == "ensemble":
        print(f"🎯 Models: {', '.join(hyperparams.get('models', []))}")
        print(f"🎯 N estimators: {hyperparams.get('lightgbm', {}).get('n_estimators', '?')}")

    # Select training script based on model type
    if model_type == "ppo":
        script = "backend/training/quick_train_ppo.py"
    elif model_type == "ensemble":
        script = "backend/training/train_ensemble_quick.py"
    elif model_type == "lstm":
        script = "backend/training/train_lstm_quick.py"
    else:
        return {"status": "error", "error": f"Unknown model type: {model_type}"}

    # Save hyperparameters to temp JSON file
    hyperparams_file = Path(CONFIGS['output_dir']) / f"{output_name}_hyperparams.json"
    hyperparams_file.parent.mkdir(parents=True, exist_ok=True)

    with open(hyperparams_file, 'w') as f:
        json.dump(hyperparams, f, indent=2)

    # Build command
    cmd = [
        "python", script,
        "--data-files", ",".join(data_files),
        "--epochs", str(epochs),
        "--device", device,
        "--output-name", output_name,
        "--hyperparams", str(hyperparams_file),  # Pass hyperparams file
        "--seed", str(CONFIGS.get('seed', 42)),
    ]

    # Add evaluation config if available
    if 'evaluation' in CONFIGS:
        eval_config_file = Path(CONFIGS['output_dir']) / f"{output_name}_eval_config.json"
        with open(eval_config_file, 'w') as f:
            json.dump(CONFIGS['evaluation'], f, indent=2)
        cmd.extend(["--eval-config", str(eval_config_file)])

    try:
        # Get project root directory (parent of scripts/)
        project_root = Path(__file__).parent.parent
        
        # Print command for debugging
        print(f"   Command: {' '.join(cmd[:3])} ... (truncated)")
        
        # For PPO training, use real-time output to see progress
        # For other models, we can still capture output
        use_real_time = model_type == "ppo"
        
        if use_real_time:
            # Real-time output for PPO (to see environment creation progress)
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                stderr=subprocess.PIPE,  # Still capture stderr for errors
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=7200
            )
            # Print stderr if there are errors
            if result.stderr and result.returncode != 0:
                print(f"\n⚠️  Errors:")
                print(result.stderr[:1000])  # First 1000 chars
        else:
            # Capture output for other models
            result = subprocess.run(
                cmd,
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=7200
            )
            # Print last 50 lines of output for debugging
            if result.stdout:
                lines = result.stdout.split('\n')
                if len(lines) > 50:
                    print('\n'.join(lines[-50:]))
                else:
                    print(result.stdout)

        elapsed = time.time() - start_time

        if result.returncode == 0:
            print(f"✅ Training complete in {elapsed/60:.1f} minutes")

            # Try to parse metrics from output (if available)
            metrics = {}
            output = result.stdout if hasattr(result, 'stdout') and result.stdout else ""
            if output:
                for line in output.split('\n'):
                    if 'accuracy' in line.lower() or 'loss' in line.lower() or 'reward' in line.lower():
                        # Basic metric parsing (can be improved)
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) == 2:
                                key = parts[0].strip()
                                try:
                                    value = float(parts[1].strip().split()[0])
                                    metrics[key] = value
                                except:
                                    pass

            return {
                "status": "success",
                "elapsed": elapsed,
                "model_type": model_type,
                "output_name": output_name,
                "metrics": metrics,
            }
        else:
            error_msg = (result.stderr[:1000] if result.stderr else "Unknown error") if hasattr(result, 'stderr') else "Unknown error"
            print(f"❌ Training failed: {error_msg}")
            return {
                "status": "failed",
                "elapsed": elapsed,
                "model_type": model_type,
                "output_name": output_name,
                "error": error_msg,
            }

    except subprocess.TimeoutExpired:
        print(f"⏰ Training timeout after 2 hours")
        return {
            "status": "timeout",
            "elapsed": time.time() - start_time,
            "model_type": model_type,
            "output_name": output_name,
        }
    except Exception as e:
        print(f"❌ Training error: {str(e)}")
        return {
            "status": "error",
            "elapsed": time.time() - start_time,
            "model_type": model_type,
            "output_name": output_name,
            "error": str(e),
        }


def main():
    """Main training orchestrator"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Train all models on downloaded data')
    parser.add_argument('--only-model', type=str, help='Only train this model type (ppo, ensemble, lstm)')
    parser.add_argument('--only-group', type=str, help='Only train on this data group (e.g., futures_1d)')
    args = parser.parse_args()

    print("\n" + "="*80)
    print("🎓 MULTI-EVERYTHING MODEL TRAINER")
    print("="*80)

    # Find data files (with filters)
    print(f"\n📁 Scanning {CONFIGS['data_dir']} for parquet files...")
    timeframes = CONFIGS.get('timeframes', None)
    markets = CONFIGS.get('markets', None)
    
    if timeframes:
        print(f"   ⏱️  Filtering timeframes: {timeframes}")
    if markets:
        print(f"   📊 Filtering markets: {markets}")
    
    data_groups = find_data_files(CONFIGS['data_dir'], timeframes=timeframes, markets=markets)

    if not data_groups:
        print(f"❌ No parquet files found in {CONFIGS['data_dir']}")
        if timeframes or markets:
            print(f"   Filters: timeframes={timeframes}, markets={markets}")
        print(f"   Run download_all.py first!")
        return False

    print(f"\n✅ Found {len(data_groups)} data groups:")
    for group_name, files in data_groups.items():
        print(f"   - {group_name}: {len(files)} files")

    # Filter models if --only-model is specified
    models_to_train = CONFIGS['models']
    if args.only_model:
        if args.only_model.lower() not in ['ppo', 'ensemble', 'lstm']:
            print(f"❌ Invalid model type: {args.only_model}")
            print(f"   Valid options: ppo, ensemble, lstm")
            return False
        models_to_train = [args.only_model.lower()]
        print(f"🎯 Filtering to model: {models_to_train[0]}")

    # Calculate training tasks
    if CONFIGS['separate_by_market'] and CONFIGS['separate_by_timeframe']:
        # Train separate model for each market+timeframe+model_type combo
        training_tasks = []
        for group_name, files in data_groups.items():
            # Filter by group if --only-group is specified
            if args.only_group and group_name != args.only_group:
                continue
            for model_type in models_to_train:
                training_tasks.append({
                    'group_name': group_name,
                    'model_type': model_type,
                    'files': files,
                })
    elif CONFIGS['separate_by_market']:
        # Train separate model for each market+model_type (combine timeframes)
        market_files = {}
        for group_name, files in data_groups.items():
            market = group_name.split('_')[0]
            if market not in market_files:
                market_files[market] = []
            market_files[market].extend(files)

        training_tasks = []
        for market, files in market_files.items():
            # Filter by group if --only-group is specified
            if args.only_group and market != args.only_group:
                continue
            for model_type in models_to_train:
                training_tasks.append({
                    'group_name': market,
                    'model_type': model_type,
                    'files': files,
                })
    else:
        # Train one model per model_type (combine all data)
        all_files = []
        for group_name, files in data_groups.items():
            # Filter by group if --only-group is specified
            if args.only_group and group_name != args.only_group:
                continue
            all_files.extend(files)

        training_tasks = []
        for model_type in models_to_train:
            training_tasks.append({
                'group_name': 'all',
                'model_type': model_type,
                'files': all_files,
            })

    print(f"\n📋 Total training tasks: {len(training_tasks)}")
    print(f"🖥️  Device: {CONFIGS['device']}")

    for i, task in enumerate(training_tasks, 1):
        print(f"\n   Task {i}: {task['model_type'].upper()} on {task['group_name']} ({len(task['files'])} files)")

    # Only prompt if running interactively (stdin is available)
    if sys.stdin.isatty():
        try:
            input("\nPress ENTER to start training...")
        except (EOFError, KeyboardInterrupt):
            print("\n⚠️  Skipping prompt (non-interactive mode)")
    else:
        print("\n⚠️  Running in non-interactive mode, starting training immediately...")

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
            hyperparams=CONFIGS[task['model_type']],  # Pass model-specific hyperparams
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

    # Final summary
    total_elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("📊 TRAINING SUMMARY")
    print("="*80)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    print(f"✅ Success: {success_count}/{len(training_tasks)}")
    print(f"❌ Failed: {failed_count}/{len(training_tasks)}")
    print(f"⏱️  Total time: {total_elapsed/60:.1f} minutes ({total_elapsed/3600:.1f} hours)")

    # Detailed results
    print(f"\n{'='*80}")
    print("DETAILED RESULTS:")
    print(f"{'='*80}")

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'success' else "❌"
        elapsed_min = result['elapsed'] / 60
        print(f"{status_icon} Task {i}: {result['model_type'].upper()} | {result['output_name']} | "
              f"{elapsed_min:.1f}m | {result['status']}")

        if result.get('metrics'):
            print(f"     Metrics: {result['metrics']}")

    # Save results to JSON
    results_file = Path(CONFIGS['output_dir']) / f"training_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump({
            'config': CONFIGS,
            'data_groups': {k: len(v) for k, v in data_groups.items()},
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
