#!/usr/bin/env python3
"""
LSTM Model Training Script

Usage:
    python -m backend.training.train_lstm --symbol BTCUSDT --timeframe 1h --epochs 100

Features:
    - Loads historical data from Parquet
    - Calculates technical indicators
    - Trains bidirectional LSTM
    - Saves trained model
    - Generates training report
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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.ml.lstm import LSTMTrendPredictor


class TimeSeriesDataset(Dataset):
    """Time series dataset for LSTM"""

    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def calculate_indicators(df):
    """Calculate technical indicators for features"""

    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))

    # Moving averages
    for period in [7, 14, 21, 50, 100, 200]:
        df[f'sma_{period}'] = df['close'].rolling(period).mean()
        df[f'ema_{period}'] = df['close'].ewm(span=period).mean()

    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['close'].ewm(span=12).mean()
    exp2 = df['close'].ewm(span=26).mean()
    df['macd'] = exp1 - exp2
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']

    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
    df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']

    # ATR (Average True Range)
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    df['atr'] = true_range.rolling(14).mean()

    # Volume indicators
    df['volume_ma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_ma']

    # Momentum
    df['momentum'] = df['close'] - df['close'].shift(10)
    df['roc'] = ((df['close'] - df['close'].shift(12)) / df['close'].shift(12)) * 100

    # Price position
    df['price_position'] = (df['close'] - df['low'].rolling(14).min()) / (
        df['high'].rolling(14).max() - df['low'].rolling(14).min()
    )

    # Drop NaN rows
    df.dropna(inplace=True)

    return df


def create_sequences(data, target, seq_length=60):
    """
    Create sequences for LSTM

    Args:
        data: Feature array (n_samples, n_features)
        target: Target array (n_samples,)
        seq_length: Sequence length (lookback window)

    Returns:
        X: (n_sequences, seq_length, n_features)
        y: (n_sequences,)
    """
    X, y = [], []

    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(target[i+seq_length])

    return np.array(X), np.array(y)


def load_data(symbol, timeframe, data_dir='data/historical'):
    """Load historical data from Parquet"""

    filename = f"{symbol}_{timeframe}_futures.parquet"
    filepath = Path(data_dir) / filename

    if not filepath.exists():
        raise FileNotFoundError(f"Data file not found: {filepath}")

    print(f"📂 Loading data from {filepath}")
    df = pd.read_parquet(filepath)

    # Ensure required columns exist
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Data must have columns: {required_cols}")

    print(f"✅ Loaded {len(df)} candles")
    return df


def prepare_features(df, seq_length=60):
    """Prepare features and target for training"""

    print("🔧 Calculating technical indicators...")
    df = calculate_indicators(df)

    # Feature columns (exclude raw OHLCV, keep only indicators)
    feature_cols = [col for col in df.columns if col not in [
        'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'timestamp'
    ]]

    print(f"📊 Using {len(feature_cols)} features: {feature_cols[:5]}... (showing first 5)")

    # Create target: 1 if price goes up, 0 if down
    # Using future return (next candle)
    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
    df.dropna(inplace=True)

    # Extract features and target
    X = df[feature_cols].values
    y = df['target'].values

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    print(f"🔄 Creating sequences (lookback={seq_length})...")
    X_seq, y_seq = create_sequences(X_scaled, y, seq_length)

    print(f"✅ Created {len(X_seq)} sequences")
    print(f"   Shape: X={X_seq.shape}, y={y_seq.shape}")

    return X_seq, y_seq, scaler, feature_cols


def train_model(
    model,
    train_loader,
    val_loader,
    epochs,
    learning_rate=0.001,
    device='cpu'
):
    """Train LSTM model"""

    criterion = nn.BCEWithLogitsLoss()  # Binary classification
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )

    model.to(device)

    best_val_loss = float('inf')
    train_losses = []
    val_losses = []

    print(f"\n🚀 Starting training for {epochs} epochs...")
    print(f"   Device: {device}")
    print(f"   Learning rate: {learning_rate}")
    print(f"   Train batches: {len(train_loader)}")
    print(f"   Val batches: {len(val_loader)}")
    print("-" * 60)

    for epoch in range(epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0

        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            # Forward pass
            optimizer.zero_grad()
            outputs = model(X_batch)
            loss = criterion(outputs.squeeze(), y_batch)

            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            # Metrics
            train_loss += loss.item()
            predicted = (torch.sigmoid(outputs.squeeze()) > 0.5).float()
            correct += (predicted == y_batch).sum().item()
            total += y_batch.size(0)

        train_loss /= len(train_loader)
        train_acc = correct / total
        train_losses.append(train_loss)

        # Validation phase
        model.eval()
        val_loss = 0.0
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
        val_losses.append(val_loss)

        # Learning rate scheduling
        scheduler.step(val_loss)

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'train_loss': train_loss,
                'val_loss': val_loss,
            }, 'best_model_checkpoint.pt')

        # Print progress
        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{epochs} | "
                  f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | "
                  f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} | "
                  f"LR: {optimizer.param_groups[0]['lr']:.6f}")

    print("-" * 60)
    print(f"✅ Training complete! Best val loss: {best_val_loss:.4f}")

    return {
        'train_losses': train_losses,
        'val_losses': val_losses,
        'best_val_loss': best_val_loss
    }


def main():
    parser = argparse.ArgumentParser(description='Train LSTM model')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe (e.g., 1h, 4h)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--seq-length', type=int, default=60, help='Sequence length (lookback)')
    parser.add_argument('--hidden-size', type=int, default=128, help='LSTM hidden size')
    parser.add_argument('--num-layers', type=int, default=2, help='Number of LSTM layers')
    parser.add_argument('--lr', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--data-dir', type=str, default='data/historical', help='Data directory')
    parser.add_argument('--output-dir', type=str, default='models/trained', help='Output directory')

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("🤖 LSTM TREND PREDICTOR - TRAINING SCRIPT")
    print("="*60)
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Epochs: {args.epochs}")
    print(f"Batch size: {args.batch_size}")
    print(f"Sequence length: {args.seq_length}")
    print(f"Hidden size: {args.hidden_size}")
    print(f"Num layers: {args.num_layers}")
    print(f"Learning rate: {args.lr}")
    print("="*60)
    print()

    # 1. Load data
    df = load_data(args.symbol, args.timeframe, args.data_dir)

    # 2. Prepare features
    X, y, scaler, feature_cols = prepare_features(df, args.seq_length)

    # 3. Train/val split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, shuffle=False  # Don't shuffle time series!
    )

    print(f"\n📊 Data split:")
    print(f"   Train: {len(X_train)} sequences")
    print(f"   Val: {len(X_val)} sequences")

    # 4. Create data loaders
    train_dataset = TimeSeriesDataset(X_train, y_train)
    val_dataset = TimeSeriesDataset(X_val, y_val)

    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)

    # 5. Create model
    input_size = X.shape[2]  # Number of features
    model = LSTMTrendPredictor(
        input_size=input_size,
        hidden_size=args.hidden_size,
        num_layers=args.num_layers,
        dropout=0.2,
        bidirectional=True,
        output_size=1  # Binary classification
    )

    print(f"\n🏗️  Model architecture:")
    print(f"   Input size: {input_size}")
    print(f"   Hidden size: {args.hidden_size}")
    print(f"   Num layers: {args.num_layers}")
    print(f"   Bidirectional: True")
    print(f"   Total parameters: {sum(p.numel() for p in model.parameters()):,}")

    # 6. Train model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    history = train_model(
        model,
        train_loader,
        val_loader,
        args.epochs,
        args.lr,
        device
    )

    # 7. Save model and metadata
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_name = f"lstm_{args.symbol}_{args.timeframe}_{timestamp}"

    model_path = output_dir / f"{model_name}.pt"
    metadata_path = output_dir / f"{model_name}_metadata.json"

    # Save model
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_config': {
            'input_size': input_size,
            'hidden_size': args.hidden_size,
            'num_layers': args.num_layers,
            'dropout': 0.2,
            'bidirectional': True,
            'output_size': 1
        },
        'scaler': scaler,
        'feature_cols': feature_cols,
        'training_args': vars(args),
        'history': history
    }, model_path)

    # Save metadata
    metadata = {
        'model_name': model_name,
        'symbol': args.symbol,
        'timeframe': args.timeframe,
        'trained_at': timestamp,
        'epochs': args.epochs,
        'best_val_loss': history['best_val_loss'],
        'num_parameters': sum(p.numel() for p in model.parameters()),
        'feature_count': input_size,
        'sequence_length': args.seq_length
    }

    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\n💾 Model saved:")
    print(f"   Model: {model_path}")
    print(f"   Metadata: {metadata_path}")
    print()
    print("="*60)
    print("✅ TRAINING COMPLETE!")
    print("="*60)
    print()
    print("🎯 Next steps:")
    print("   1. Test the model: python -m backend.inference.predict_lstm --model", model_path)
    print("   2. Run backtest: python -m backend.backtest.run_backtest --model", model_path)
    print("   3. Deploy to production: Copy model to production server")
    print()


if __name__ == '__main__':
    main()
