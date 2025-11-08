#!/usr/bin/env python3
"""
Quick Ensemble Training Wrapper
Wraps train_xgboost.py for ensemble training

Usage:
    python backend/training/train_ensemble_quick.py --data-files file1.parquet,file2.parquet --epochs 1 --device cuda
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json


def main():
    parser = argparse.ArgumentParser(description='Quick Ensemble Training Wrapper')
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet files')
    parser.add_argument('--epochs', type=int, default=1, help='Training epochs (not used for ensemble)')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--output-name', type=str, required=True)
    parser.add_argument('--hyperparams', type=str, help='Hyperparameters JSON file')
    parser.add_argument('--eval-config', type=str, help='Evaluation config JSON file')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    # Load hyperparams
    hyperparams = {}
    if args.hyperparams and Path(args.hyperparams).exists():
        with open(args.hyperparams, 'r') as f:
            hyperparams = json.load(f)

    # Parse data files
    data_files = [f.strip() for f in args.data_files.split(',')]

    if not data_files:
        print("[ERROR] No data files provided")
        return 1

    # For multi-file training, use the first file's symbol/timeframe/market
    first_file = Path(data_files[0])
    parts = first_file.stem.split('_')

    if len(parts) < 3:
        print(f"[ERROR] Invalid filename format: {first_file.stem}")
        print("   Expected: SYMBOL_TF_MARKET_multi.parquet")
        return 1

    symbol = parts[0]
    timeframe = parts[1]
    market = parts[2]

    print(f"\n[*] Training Ensemble on: {symbol} {timeframe} {market}")
    print(f"[*] Using {len(data_files)} data file(s)")
    print(f"[*] Output: {args.output_name}")
    print(f"[*] Models: XGBoost (standalone)")

    # Build command for XGBoost training
    n_estimators = hyperparams.get('xgboost', {}).get('n_estimators', 200)
    max_depth = hyperparams.get('xgboost', {}).get('max_depth', 4)
    learning_rate = hyperparams.get('xgboost', {}).get('learning_rate', 0.1)
    tree_method = hyperparams.get('xgboost', {}).get('tree_method', 'auto')
    days = hyperparams.get('days', None)

    cmd = [
        sys.executable, '-m', 'backend.training.train_xgboost',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--market', market,
        '--task', 'pattern_classification',
        '--n-estimators', str(n_estimators),
        '--max-depth', str(max_depth),
        '--lr', str(learning_rate),
        '--data-dir', 'data/advanced',
        '--output-dir', 'data/models',
    ]

    if days is not None:
        cmd.extend(['--days', str(days)])
        print(f"   [!] Using last {days} days of data for faster training")

    # Run training
    print(f"\n[>>] Starting ensemble training...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    # Print output for debugging (limit to avoid spam)
    if result.stdout:
        lines = result.stdout.split('\n')
        if len(lines) > 100:
            print('\n'.join(lines[-100:]))
        else:
            print(result.stdout)

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode == 0:
        print(f"\n[OK] Training complete!")
        print(f"[*] Model saved to: data/models/xgboost_*_{symbol}_{timeframe}_*.json")
    else:
        print(f"\n[FAIL] Training failed with code {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr[:500]}")

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
