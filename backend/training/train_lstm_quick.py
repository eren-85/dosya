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
    data_path: str = "/home/user/dosya/backend/data/prepared/BTCUSDT_1d_futures_prepared.parquet",
    seq_length: int = 60,
    epochs: int = 50,
    batch_size: int = 32,
    learning_rate: float = 0.001,
    save_path: str = "/home/user/dosya/backend/models/saved/lstm_btcusdt_1d.pth"
):
    """Train LSTM model"""

    logger.info("🧠 Starting LSTM Training")
    logger.info(f"   Data: {data_path}")
    logger.info(f"   Sequence length: {seq_length}")
    logger.info(f"   Epochs: {epochs}")

    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"   Device: {device}")

    # Load data
    df = pd.read_parquet(data_path)
    logger.info(f"   Loaded {len(df)} candles")

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
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
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
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--seq-length', type=int, default=60, help='Sequence length')
    args = parser.parse_args()

    model = train_lstm(
        epochs=args.epochs,
        batch_size=args.batch_size,
        seq_length=args.seq_length
    )
