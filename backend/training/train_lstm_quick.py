"""
Quick LSTM Training for Trend Prediction
GPU-accelerated with Mixed Precision (FP16)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TimeSeriesDataset(Dataset):
    """Dataset for LSTM time series"""

    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMModel(nn.Module):
    """Bidirectional LSTM for price prediction"""

    def __init__(self, input_size, hidden_size=128, num_layers=2, dropout=0.2):
        super().__init__()

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=True
        )

        lstm_output_size = hidden_size * 2  # bidirectional

        self.fc = nn.Sequential(
            nn.Linear(lstm_output_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1)
        )

    def forward(self, x):
        # x shape: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)

        # Take last output
        last_out = lstm_out[:, -1, :]

        # Prediction
        out = self.fc(last_out)

        return out


def create_sequences(data, seq_length=60):
    """Create sequences for LSTM training"""
    X, y = [], []

    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length, :-1])  # All features except target
        y.append(data[i+seq_length, -1])  # Target (price change)

    return np.array(X), np.array(y)


def train_lstm(
    symbol: str = "BTCUSDT",
    timeframe: str = "1d",
    market_type: str = "futures",
    seq_length: int = 60,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    save_dir: str = "/home/user/dosya/backend/models/saved",
    use_advanced: bool = True
):
    """
    Train LSTM model for price prediction

    Args:
        symbol: Trading symbol
        timeframe: Candle timeframe
        market_type: 'spot' or 'futures'
        seq_length: Sequence length for LSTM
        epochs: Number of training epochs
        batch_size: Training batch size
        learning_rate: Learning rate
        save_dir: Directory to save model
        use_advanced: Use advanced multi-exchange features if available
    """

    logger.info("🧠 Starting LSTM Training")
    logger.info(f"   Symbol: {symbol} {timeframe} {market_type}")
    logger.info(f"   Sequence length: {seq_length}")
    logger.info(f"   Epochs: {epochs}")
    logger.info(f"   Advanced mode: {use_advanced}")

    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"   Device: {device}")

    # Load and prepare data (will auto-detect advanced data)
    from backend.training.prepare_rl_data import prepare_training_data

    df = prepare_training_data(
        symbol=symbol,
        timeframe=timeframe,
        market_type=market_type,
        use_advanced=use_advanced
    )
    logger.info(f"   Loaded {len(df)} candles with {len(df.columns)} features")

    # Features
    feature_cols = [col for col in df.columns if col not in [
        'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'quote_asset_volume',
        'trades', 'taker_base', 'taker_quote', 'ignore'
    ]]

    logger.info(f"   Features: {len(feature_cols)}")

    # Target: next candle price change
    df['target'] = df['close'].pct_change().shift(-1)
    df = df.dropna()

    # Prepare data
    data = df[feature_cols + ['target']].values

    # Normalize
    scaler = StandardScaler()
    data = scaler.fit_transform(data)

    # Create sequences
    logger.info("   Creating sequences...")
    X, y = create_sequences(data, seq_length)

    logger.info(f"   Sequences: {len(X)}")

    # Train/test split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"   Train: {len(X_train)} sequences")
    logger.info(f"   Test:  {len(X_test)} sequences")

    # Create datasets
    train_dataset = TimeSeriesDataset(X_train, y_train)
    test_dataset = TimeSeriesDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Model
    input_size = X.shape[2]
    model = LSTMModel(input_size=input_size, hidden_size=128, num_layers=2, dropout=0.2)
    model = model.to(device)

    logger.info(f"   Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Mixed precision training
    scaler_amp = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None

    # Training loop
    logger.info("\n🚀 Training started...")

    best_test_loss = float('inf')

    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0

        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()

            # Mixed precision
            if scaler_amp:
                with torch.cuda.amp.autocast():
                    outputs = model(X_batch).squeeze()
                    loss = criterion(outputs, y_batch)

                scaler_amp.scale(loss).backward()
                scaler_amp.step(optimizer)
                scaler_amp.update()
            else:
                outputs = model(X_batch).squeeze()
                loss = criterion(outputs, y_batch)
                loss.backward()
                optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Test
        model.eval()
        test_loss = 0

        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch).squeeze()
                loss = criterion(outputs, y_batch)
                test_loss += loss.item()

        test_loss /= len(test_loader)

        # Log
        if (epoch + 1) % 5 == 0:
            logger.info(f"   Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}")

        # Save best model
        if test_loss < best_test_loss:
            best_test_loss = test_loss
            save_path = Path(save_dir) / f"lstm_{symbol.lower()}_{timeframe}.pth"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'scaler': scaler,
                'input_size': input_size,
                'seq_length': seq_length,
                'feature_cols': feature_cols
            }, save_path)

    logger.info(f"\n✅ Training complete!")
    logger.info(f"   Best test loss: {best_test_loss:.6f}")
    logger.info(f"   Model saved: {save_path}")

    return model


if __name__ == "__main__":
    import json

    parser = argparse.ArgumentParser(description='Train LSTM Model (Batch Mode)')

    # Batch training parameters
    parser.add_argument('--data-files', type=str, required=True, help='Comma-separated parquet file paths')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--device', type=str, default='cpu', choices=['cpu', 'cuda'], help='Training device')
    parser.add_argument('--output-name', type=str, required=True, help='Output model name (e.g., spot_1h_lstm)')
    parser.add_argument('--hyperparams', type=str, required=True, help='Path to hyperparameters JSON file')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--eval-config', type=str, help='Path to evaluation config JSON file')

    # Legacy parameters (for backward compatibility)
    parser.add_argument('--symbol', type=str, help='Trading symbol (legacy mode)')
    parser.add_argument('--timeframe', type=str, help='Candle timeframe (legacy mode)')
    parser.add_argument('--market', type=str, help='spot or futures (legacy mode)')
    parser.add_argument('--batch-size', type=int, help='Batch size (legacy mode)')
    parser.add_argument('--seq-length', type=int, help='Sequence length (legacy mode)')
    parser.add_argument('--no-advanced', action='store_true', help='Disable advanced features (legacy mode)')

    args = parser.parse_args()

    # Set random seed
    np.random.seed(args.seed)
    import random
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)

    # Load hyperparameters
    with open(args.hyperparams, 'r') as f:
        hyperparams = json.load(f)

    logger.info(f"🧠 Starting LSTM Batch Training")
    logger.info(f"   Output: {args.output_name}")
    logger.info(f"   Device: {args.device}")
    logger.info(f"   Seed: {args.seed}")
    logger.info(f"   Epochs: {args.epochs}")
    logger.info(f"   Sequence length: {hyperparams.get('seq_len', 128)}")
    logger.info(f"   Hidden size: {hyperparams.get('hidden_size', 256)}")

    # Device
    device = torch.device(args.device)
    logger.info(f"   Using device: {device}")

    # Load data files
    data_file_paths = args.data_files.split(',')
    logger.info(f"   Loading {len(data_file_paths)} data files...")

    dfs = []
    for file_path in data_file_paths:
        df = pd.read_parquet(file_path.strip())
        logger.info(f"      - {Path(file_path).name}: {len(df)} rows")
        dfs.append(df)

    # Concatenate all data
    df_combined = pd.concat(dfs, ignore_index=True).sort_values('open_time').reset_index(drop=True)
    logger.info(f"   Combined data: {len(df_combined)} rows")

    # Features
    feature_cols = [col for col in df_combined.columns if col not in [
        'open', 'high', 'low', 'close', 'volume',
        'open_time', 'close_time', 'quote_asset_volume',
        'trades', 'taker_base', 'taker_quote', 'ignore'
    ]]

    logger.info(f"   Features: {len(feature_cols)}")

    # Target: next candle price change
    df_combined['target'] = df_combined['close'].pct_change().shift(-1)
    df_combined = df_combined.dropna()

    # Prepare data
    data = df_combined[feature_cols + ['target']].values

    # Normalize
    scaler = StandardScaler()
    data = scaler.fit_transform(data)

    # Create sequences
    seq_length = hyperparams.get('seq_len', 128)
    logger.info(f"   Creating sequences (length={seq_length})...")
    X, y = create_sequences(data, seq_length)

    logger.info(f"   Sequences: {len(X)}")

    # Train/test split
    split_idx = int(len(X) * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(f"   Train: {len(X_train)} sequences")
    logger.info(f"   Test:  {len(X_test)} sequences")

    # Create datasets
    batch_size = hyperparams.get('batch_size', 32)
    train_dataset = TimeSeriesDataset(X_train, y_train)
    test_dataset = TimeSeriesDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # Model
    input_size = X.shape[2]
    hidden_size = hyperparams.get('hidden_size', 256)
    num_layers = hyperparams.get('num_layers', 2)
    dropout = hyperparams.get('dropout', 0.2)

    model = LSTMModel(
        input_size=input_size,
        hidden_size=hidden_size,
        num_layers=num_layers,
        dropout=dropout
    )
    model = model.to(device)

    logger.info(f"   Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    # Loss and optimizer
    criterion = nn.MSELoss()
    learning_rate = hyperparams.get('learning_rate', 1e-3)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # Learning rate scheduler (ReduceLROnPlateau)
    reduce_lr_patience = hyperparams.get('reduce_lr_patience', 5)
    reduce_lr_factor = hyperparams.get('reduce_lr_factor', 0.5)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=reduce_lr_factor,
        patience=reduce_lr_patience,
        verbose=True
    )

    # Mixed precision training
    use_amp = hyperparams.get('use_amp', True) and device.type == 'cuda'
    scaler_amp = torch.cuda.amp.GradScaler() if use_amp else None

    # Gradient clipping
    grad_clip = hyperparams.get('grad_clip', 0.5)

    # Early stopping
    early_stopping = hyperparams.get('early_stopping', True)
    patience = hyperparams.get('patience', 10)
    patience_counter = 0

    # Training loop
    logger.info("\n🚀 Training started...")

    best_test_loss = float('inf')

    for epoch in range(args.epochs):
        # Train
        model.train()
        train_loss = 0

        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)

            optimizer.zero_grad()

            # Mixed precision
            if scaler_amp:
                with torch.cuda.amp.autocast():
                    outputs = model(X_batch).squeeze()
                    loss = criterion(outputs, y_batch)

                scaler_amp.scale(loss).backward()

                # Gradient clipping
                if grad_clip > 0:
                    scaler_amp.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

                scaler_amp.step(optimizer)
                scaler_amp.update()
            else:
                outputs = model(X_batch).squeeze()
                loss = criterion(outputs, y_batch)
                loss.backward()

                # Gradient clipping
                if grad_clip > 0:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)

                optimizer.step()

            train_loss += loss.item()

        train_loss /= len(train_loader)

        # Test
        model.eval()
        test_loss = 0

        with torch.no_grad():
            for X_batch, y_batch in test_loader:
                X_batch, y_batch = X_batch.to(device), y_batch.to(device)
                outputs = model(X_batch).squeeze()
                loss = criterion(outputs, y_batch)
                test_loss += loss.item()

        test_loss /= len(test_loader)

        # Update learning rate
        scheduler.step(test_loss)

        # Log
        if (epoch + 1) % 5 == 0:
            logger.info(f"   Epoch {epoch+1}/{args.epochs} - Train Loss: {train_loss:.6f}, Test Loss: {test_loss:.6f}")

        # Save best model
        if test_loss < best_test_loss:
            best_test_loss = test_loss
            patience_counter = 0

            save_path = Path("data/models") / f"{args.output_name}.pth"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save({
                'model_state_dict': model.state_dict(),
                'scaler': scaler,
                'input_size': input_size,
                'seq_length': seq_length,
                'feature_cols': feature_cols,
                'hyperparams': hyperparams
            }, save_path)
        else:
            patience_counter += 1

        # Early stopping
        if early_stopping and patience_counter >= patience:
            logger.info(f"\n⏸️  Early stopping triggered after {epoch+1} epochs")
            break

    logger.info(f"\n✅ Training complete!")
    logger.info(f"   Best test loss: {best_test_loss:.6f}")
    logger.info(f"   Model saved: {save_path}")
