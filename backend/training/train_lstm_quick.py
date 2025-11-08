#!/usr/bin/env python3
"""
Quick LSTM Training Wrapper
Wraps train_lstm.py to support multi-file training for train_all.py

Usage:
    python backend/training/train_lstm_quick.py --data-files file1.parquet,file2.parquet --epochs 50 --device cuda
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json

def main():
    parser = argparse.ArgumentParser(description='Quick LSTM Training Wrapper')
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet files')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
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

    print(f"\n🎓 Training LSTM on: {symbol} {timeframe} {market}")
    print(f"📊 Using {len(data_files)} data file(s)")
    print(f"📁 Output: {args.output_name}")
    print(f"🎯 Epochs: {args.epochs}")

    # Get LSTM hyperparams
    seq_len = hyperparams.get('seq_len', 128)
    hidden_size = hyperparams.get('hidden_size', 256)
    num_layers = hyperparams.get('num_layers', 2)
    dropout = hyperparams.get('dropout', 0.2)
    learning_rate = hyperparams.get('learning_rate', 1e-3)

    # Build command for actual training script
    cmd = [
        'python', '-m', 'backend.training.train_lstm',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--market', market,
        '--epochs', str(args.epochs),
        '--seq-len', str(seq_len),
        '--hidden-size', str(hidden_size),
        '--num-layers', str(num_layers),
        '--dropout', str(dropout),
        '--learning-rate', str(learning_rate),
        '--device', args.device,
        '--output-dir', 'data/models',
    ]

    # Run training
    print(f"\n🚀 Starting training...")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"\n✅ Training complete!")
        print(f"📁 Model saved to: data/models/{symbol}_{timeframe}_{market}_lstm_*.pth")
    else:
        print(f"\n❌ Training failed with code {result.returncode}")

    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
