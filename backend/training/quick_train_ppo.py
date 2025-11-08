#!/usr/bin/env python3
"""
Quick PPO Training Wrapper
Wraps train_ppo.py to support multi-file training for train_all.py

Usage:
    python backend/training/quick_train_ppo.py --data-files file1.parquet,file2.parquet --epochs 10 --device cuda
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json


def main():
    parser = argparse.ArgumentParser(description='Quick PPO Training Wrapper')
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet files')
    parser.add_argument('--epochs', type=int, default=10, help='Training epochs (maps to total_timesteps)')
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
        print("❌ No data files provided")
        return 1

    # For multi-file training, use the first file's symbol/timeframe/market
    first_file = Path(data_files[0])
    parts = first_file.stem.split('_')

    if len(parts) < 3:
        print(f"❌ Invalid filename format: {first_file.stem}")
        print("   Expected: SYMBOL_TF_MARKET_multi.parquet")
        return 1

    symbol = parts[0]
    timeframe = parts[1]
    market = parts[2]

    print(f"\n🎓 Training PPO on: {symbol} {timeframe} {market}")
    print(f"📊 Using {len(data_files)} data file(s)")
    print(f"📁 Output: {args.output_name}")

    # Build command for actual training script
    total_timesteps = hyperparams.get('total_timesteps', 100_000)
    learning_rate = hyperparams.get('learning_rate', 3e-4)
    batch_size = hyperparams.get('batch_size', 128)
    n_steps = hyperparams.get('n_steps', 2048)
    days = hyperparams.get('days', None)

    cmd = [
        sys.executable, '-m', 'backend.training.train_ppo',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--market', market,
        '--total-timesteps', str(total_timesteps),
        '--learning-rate', str(learning_rate),
        '--batch-size', str(batch_size),
        '--n-steps', str(n_steps),
        '--data-dir', 'data/advanced',
        '--output-dir', 'data/models',
    ]

    if days is not None:
        cmd.extend(['--days', str(days)])
        print(f"   ⚡ Using last {days} days of data for faster training")

    # Run training
    print(f"\n🚀 Starting training...")

    result = subprocess.run(
        cmd,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.stderr:
        print("\n⚠️  Stderr output:")
        print(result.stderr, file=sys.stderr)

    if result.returncode == 0:
        print(f"\n✅ Training complete!")
        print(f"📁 Model saved to: data/models/ppo_{symbol}_{timeframe}_*.zip")
    else:
        print(f"\n❌ Training failed with code {result.returncode}")
        if result.stderr:
            print(f"Error: {result.stderr[:500]}")

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
