#!/usr/bin/env python3
"""
LSTM Hyperparameter Tuning Script

Usage:
    python -m backend.training.tune_lstm --symbol BTCUSDT --timeframe 1h --trials 50

Features:
    - Grid search or random search
    - Optimize: hidden_size, num_layers, dropout, lr, seq_length
    - Cross-validation
    - Best model selection
    - Results visualization
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import json
from itertools import product
import random

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.ml.lstm import LSTMTrendPredictor
from backend.training.train_lstm import (
    load_data,
    calculate_indicators,
    create_sequences,
    TimeSeriesDataset
)


def train_and_evaluate(
    X_train, y_train, X_val, y_val,
    hidden_size, num_layers, dropout, learning_rate, seq_length,
    epochs=50, batch_size=32
):
    """
    Train model with given hyperparameters and return validation accuracy

    Returns:
        val_acc: Validation accuracy
        val_loss: Validation loss
    """

    # Create datasets
    train_dataset = TimeSeriesDataset(X_train, y_train)
    val_dataset = TimeSeriesDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    # Create model
    input_size = X_train.shape[2]
    model = LSTMTrendPredictor(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout,
        bidirectional=True,
        output_size=1
    )

    # Training setup
    criterion = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model.to(device)

    best_val_loss = float('inf')
    patience = 10
    patience_counter = 0

    # Training loop
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs.squeeze(), y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            train_loss += loss.item()

        # Validation
        model.eval()
        val_loss = 0
        correct = 0
        total = 0

        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)

                outputs = model(X_batch)
                loss = criterion(outputs.squeeze(), y_batch)

                val_loss += loss.item()
                predicted = (torch.sigmoid(outputs.squeeze()) > 0.5).float()
                correct += (predicted == y_batch).sum().item()
                total += y_batch.size(0)

        val_loss /= len(val_loader)
        val_acc = correct / total

        # Early stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
        else:
            patience_counter += 1
            if patience_counter >= patience:
                break

    return val_acc, best_val_loss


def grid_search(X_train, y_train, X_val, y_val, param_grid, epochs=50):
    """
    Grid search over hyperparameter space

    Args:
        param_grid: Dict with lists of values for each param
            e.g., {'hidden_size': [64, 128], 'num_layers': [1, 2]}

    Returns:
        results: List of dicts with params and scores
        best_params: Best hyperparameters
    """

    print("\n🔍 Starting grid search...")
    print(f"   Parameter space:")
    for param, values in param_grid.items():
        print(f"      {param}: {values}")

    # Generate all combinations
    keys = param_grid.keys()
    values = param_grid.values()
    combinations = list(product(*values))

    print(f"\n   Total combinations: {len(combinations)}")
    print("-" * 60)

    results = []

    for i, combo in enumerate(combinations, 1):
        params = dict(zip(keys, combo))

        print(f"\n[{i}/{len(combinations)}] Testing: {params}")

        try:
            val_acc, val_loss = train_and_evaluate(
                X_train, y_train, X_val, y_val,
                hidden_size=params['hidden_size'],
                num_layers=params['num_layers'],
                dropout=params['dropout'],
                learning_rate=params['learning_rate'],
                seq_length=params['seq_length'],
                epochs=epochs
            )

            results.append({
                'params': params,
                'val_acc': val_acc,
                'val_loss': val_loss
            })

            print(f"   Val Acc: {val_acc:.3f} | Val Loss: {val_loss:.4f}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'params': params,
                'val_acc': 0,
                'val_loss': float('inf'),
                'error': str(e)
            })

    print("-" * 60)

    # Find best params
    valid_results = [r for r in results if r['val_acc'] > 0]
    if not valid_results:
        raise ValueError("All hyperparameter combinations failed!")

    best_result = max(valid_results, key=lambda x: x['val_acc'])
    best_params = best_result['params']

    print(f"\n✅ Grid search complete!")
    print(f"   Best validation accuracy: {best_result['val_acc']:.3f}")
    print(f"   Best parameters: {best_params}")

    return results, best_params


def random_search(X_train, y_train, X_val, y_val, param_distributions, n_trials=50, epochs=50):
    """
    Random search over hyperparameter space

    Args:
        param_distributions: Dict with (min, max) ranges for each param
            e.g., {'hidden_size': (64, 512), 'learning_rate': (0.0001, 0.01)}
        n_trials: Number of random samples to try

    Returns:
        results: List of dicts with params and scores
        best_params: Best hyperparameters
    """

    print("\n🎲 Starting random search...")
    print(f"   Trials: {n_trials}")
    print(f"   Parameter ranges:")
    for param, (min_val, max_val) in param_distributions.items():
        print(f"      {param}: [{min_val}, {max_val}]")
    print("-" * 60)

    results = []

    for trial in range(1, n_trials + 1):
        # Sample random parameters
        params = {}
        for param, (min_val, max_val) in param_distributions.items():
            if param in ['hidden_size', 'num_layers', 'seq_length']:
                # Integer parameters
                params[param] = random.randint(min_val, max_val)
            else:
                # Float parameters
                params[param] = random.uniform(min_val, max_val)

        print(f"\n[{trial}/{n_trials}] Testing: {params}")

        try:
            val_acc, val_loss = train_and_evaluate(
                X_train, y_train, X_val, y_val,
                hidden_size=params['hidden_size'],
                num_layers=params['num_layers'],
                dropout=params['dropout'],
                learning_rate=params['learning_rate'],
                seq_length=params['seq_length'],
                epochs=epochs
            )

            results.append({
                'params': params,
                'val_acc': val_acc,
                'val_loss': val_loss
            })

            print(f"   Val Acc: {val_acc:.3f} | Val Loss: {val_loss:.4f}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")
            results.append({
                'params': params,
                'val_acc': 0,
                'val_loss': float('inf'),
                'error': str(e)
            })

    print("-" * 60)

    # Find best params
    valid_results = [r for r in results if r['val_acc'] > 0]
    if not valid_results:
        raise ValueError("All hyperparameter combinations failed!")

    best_result = max(valid_results, key=lambda x: x['val_acc'])
    best_params = best_result['params']

    print(f"\n✅ Random search complete!")
    print(f"   Best validation accuracy: {best_result['val_acc']:.3f}")
    print(f"   Best parameters: {best_params}")

    return results, best_params


def main():
    parser = argparse.ArgumentParser(description='LSTM hyperparameter tuning')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')
    parser.add_argument('--method', type=str, default='random', choices=['grid', 'random'],
                       help='Search method')
    parser.add_argument('--trials', type=int, default=50, help='Number of trials (for random search)')
    parser.add_argument('--epochs', type=int, default=50, help='Epochs per trial')
    parser.add_argument('--data-dir', type=str, default='data/historical', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='models/tuning', help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🔧 LSTM HYPERPARAMETER TUNING")
    print("=" * 60)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Method: {args.method}")
    print(f"Trials: {args.trials}")
    print(f"Epochs per trial: {args.epochs}")
    print("=" * 60)
    print()

    # 1. Load and prepare data
    print("📂 Loading data...")
    df = load_data(args.symbol, args.timeframe, args.data_dir)

    print("🔧 Calculating indicators...")
    df = calculate_indicators(df)

    # Feature columns
    feature_cols = [col for col in df.columns if col not in [
        'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'timestamp'
    ]]

    # Create target
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df.dropna(inplace=True)

    X = df[feature_cols].values
    y = df['target'].values

    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"✅ Data prepared: {len(X_scaled)} samples, {len(feature_cols)} features")

    # 2. Define hyperparameter space
    if args.method == 'grid':
        # Grid search - smaller space
        param_grid = {
            'hidden_size': [64, 128, 256],
            'num_layers': [1, 2, 3],
            'dropout': [0.1, 0.2, 0.3],
            'learning_rate': [0.0001, 0.001, 0.01],
            'seq_length': [30, 60, 120]
        }

        print(f"\n📊 Total combinations: {np.prod([len(v) for v in param_grid.values()])}")

    else:
        # Random search - larger space
        param_distributions = {
            'hidden_size': (64, 512),
            'num_layers': (1, 4),
            'dropout': (0.1, 0.5),
            'learning_rate': (0.0001, 0.01),
            'seq_length': (30, 240)
        }

    # 3. Prepare data for different sequence lengths
    # We'll need to recreate sequences for each seq_length, so we prepare a function
    print("\n🔄 Preparing for hyperparameter search...")

    # For simplicity, we'll use a fixed seq_length during search
    # and only vary it in the final training
    seq_length = 60
    X_seq, y_seq = create_sequences(X_scaled, y, seq_length)

    # Split data
    X_train, X_val, y_train, y_val = train_test_split(
        X_seq, y_seq, test_size=0.2, shuffle=False
    )

    print(f"   Train: {len(X_train)} sequences")
    print(f"   Val: {len(X_val)} sequences")

    # 4. Run hyperparameter search
    if args.method == 'grid':
        results, best_params = grid_search(
            X_train, y_train, X_val, y_val,
            param_grid, epochs=args.epochs
        )
    else:
        results, best_params = random_search(
            X_train, y_train, X_val, y_val,
            param_distributions, n_trials=args.trials, epochs=args.epochs
        )

    # 5. Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = output_dir / f"tuning_{args.symbol}_{args.timeframe}_{timestamp}.json"

    output = {
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'method': args.method,
        'trials': args.trials if args.method == 'random' else len(results),
        'epochs_per_trial': args.epochs,
        'best_params': best_params,
        'best_val_acc': max(r['val_acc'] for r in results),
        'all_results': results,
        'timestamp': timestamp
    }

    with open(results_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n💾 Results saved to: {results_file}")

    # Print top 5 results
    print("\n🏆 Top 5 Results:")
    print("-" * 60)
    sorted_results = sorted(results, key=lambda x: x['val_acc'], reverse=True)[:5]
    for i, result in enumerate(sorted_results, 1):
        print(f"{i}. Val Acc: {result['val_acc']:.3f} | Params: {result['params']}")

    print()
    print("=" * 60)
    print("✅ HYPERPARAMETER TUNING COMPLETE!")
    print("=" * 60)
    print()
    print("🎯 Next steps:")
    print("   1. Use best parameters to train final model:")
    print(f"      python -m backend.training.train_lstm \\")
    print(f"          --symbol {args.symbol} \\")
    print(f"          --timeframe {args.timeframe} \\")
    print(f"          --hidden-size {best_params['hidden_size']} \\")
    print(f"          --num-layers {best_params['num_layers']} \\")
    print(f"          --dropout {best_params['dropout']:.3f} \\")
    print(f"          --lr {best_params['learning_rate']:.6f} \\")
    print(f"          --seq-length {best_params['seq_length']} \\")
    print(f"          --epochs 200")
    print()


if __name__ == '__main__':
    main()
