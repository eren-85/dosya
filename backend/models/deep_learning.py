"""
Deep Learning Models - LSTM, Transformer
GPU-accelerated for RTX 4060 with Mixed Precision (FP16)
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Optional, List
from dataclasses import dataclass
import logging

# Compute config
import sys
sys.path.append('..')
from backend.config.compute_config import get_compute

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Training configuration"""
    epochs: int = 100
    batch_size: int = 128
    learning_rate: float = 0.001
    weight_decay: float = 1e-5
    patience: int = 10
    min_delta: float = 1e-4


class TimeSeriesDataset(Dataset):
    """Time series dataset for PyTorch"""

    def __init__(self, X: np.ndarray, y: np.ndarray):
        """
        Args:
            X: Features (batch, seq_len, features)
            y: Targets (batch,)
        """
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


class LSTMModel(nn.Module):
    """
    LSTM model for time series prediction

    Architecture:
        - Multi-layer bidirectional LSTM
        - Dropout for regularization
        - Fully connected output layers
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 256,
        num_layers: int = 3,
        dropout: float = 0.2,
        bidirectional: bool = True,
    ):
        super(LSTMModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=bidirectional,
        )

        # Output size depends on bidirectional
        lstm_output_size = hidden_size * 2 if bidirectional else hidden_size

        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Linear(lstm_output_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1),
        )

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor (batch, seq_len, features)

        Returns:
            Output tensor (batch, 1)
        """
        # LSTM forward
        lstm_out, _ = self.lstm(x)

        # Take last time step
        if self.bidirectional:
            # Concatenate forward and backward last outputs
            last_out = lstm_out[:, -1, :]
        else:
            last_out = lstm_out[:, -1, :]

        # Fully connected
        output = self.fc(last_out)
        return output


class TransformerModel(nn.Module):
    """
    Transformer model for time series prediction

    Architecture:
        - Positional encoding
        - Multi-head self-attention
        - Feed-forward network
        - Layer normalization
    """

    def __init__(
        self,
        input_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        max_seq_len: int = 100,
    ):
        super(TransformerModel, self).__init__()

        self.d_model = d_model

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers,
        )

        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 1),
        )

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor (batch, seq_len, features)

        Returns:
            Output tensor (batch, 1)
        """
        # Project to d_model dimensions
        x = self.input_projection(x)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoding
        x = self.transformer_encoder(x)

        # Global average pooling
        x = x.mean(dim=1)

        # Output
        output = self.fc(x)
        return output


class PositionalEncoding(nn.Module):
    """Positional encoding for Transformer"""

    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))

        pe = torch.zeros(max_len, d_model)
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)

        self.register_buffer('pe', pe)

    def forward(self, x):
        """
        Args:
            x: Tensor (batch, seq_len, d_model)
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class DeepLearningTrainer:
    """
    Trainer for deep learning models with GPU acceleration

    Features:
        - Mixed precision training (BF16/FP16)
        - TF32 optimization for RTX 30xx/40xx
        - Early stopping
        - Learning rate scheduling
        - Gradient clipping
        - TensorBoard logging
    """

    def __init__(
        self,
        model_type: str = 'lstm',  # 'lstm' or 'transformer'
        config: Optional[TrainingConfig] = None,
    ):
        """
        Initialize trainer

        Args:
            model_type: 'lstm' or 'transformer'
            config: Training configuration
        """
        self.model_type = model_type
        self.config = config or TrainingConfig()

        # Get compute configuration
        self.compute = get_compute()
        self.device = self.compute.get_torch_device('dl')

        # Update batch size from compute config
        if hasattr(self.compute.config, 'dl_batch_size'):
            self.config.batch_size = self.compute.config.dl_batch_size

        # Mixed precision settings
        self.use_amp = self.compute.config.use_mixed_precision and self.device.type == 'cuda'
        self.amp_dtype = self.compute.amp_dtype() if self.use_amp else None

        # GradScaler only for FP16 (not needed for BF16)
        self.scaler = None
        if self.use_amp:
            if self.amp_dtype == torch.float16:
                self.scaler = torch.cuda.amp.GradScaler()
            # BF16 doesn't need GradScaler (better numeric stability)

        logger.info(f"🚀 Deep Learning Trainer ({model_type.upper()})")
        logger.info(f"   Device: {self.device}")
        logger.info(f"   Batch Size: {self.config.batch_size}")
        if self.use_amp:
            dtype_name = "BF16" if self.amp_dtype == torch.bfloat16 else "FP16"
            logger.info(f"   Mixed Precision: {dtype_name}")
        else:
            logger.info(f"   Mixed Precision: Disabled")

        self.model = None
        self.optimizer = None
        self.scheduler = None

        self.train_losses = []
        self.val_losses = []

    def build_model(self, input_size: int, seq_len: int = 60):
        """
        Build model architecture

        Args:
            input_size: Number of input features
            seq_len: Sequence length
        """
        if self.model_type == 'lstm':
            self.model = LSTMModel(
                input_size=input_size,
                hidden_size=256,
                num_layers=3,
                dropout=0.2,
                bidirectional=True,
            )
        elif self.model_type == 'transformer':
            self.model = TransformerModel(
                input_size=input_size,
                d_model=256,
                nhead=8,
                num_layers=6,
                dim_feedforward=1024,
                dropout=0.1,
                max_seq_len=seq_len,
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        self.model.to(self.device)

        # Optimizer
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
        )

        # Learning rate scheduler
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True,
        )

        # Count parameters
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        logger.info(f"   Total parameters: {total_params:,}")
        logger.info(f"   Trainable parameters: {trainable_params:,}")

        # Enable optimizations for RTX 4060
        if self.device.type == 'cuda':
            torch.backends.cudnn.benchmark = True
            self.compute.optimize_memory()

    def fit(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ):
        """
        Train model

        Args:
            X_train: Training features (samples, seq_len, features)
            y_train: Training targets (samples,)
            X_val: Validation features
            y_val: Validation targets
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        logger.info(f"\n🏋️  Training {self.model_type.upper()} Model")
        logger.info(f"   Training samples: {len(X_train)}")
        if X_val is not None:
            logger.info(f"   Validation samples: {len(X_val)}")

        # Create datasets
        train_dataset = TimeSeriesDataset(X_train, y_train)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config.batch_size,
            shuffle=True,
            num_workers=self.compute.config.dl_num_workers,
            pin_memory=(self.device.type == 'cuda'),
            persistent_workers=True if self.compute.config.dl_num_workers > 0 else False,
        )

        if X_val is not None and y_val is not None:
            val_dataset = TimeSeriesDataset(X_val, y_val)
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config.batch_size,
                shuffle=False,
                num_workers=self.compute.config.dl_num_workers,
                pin_memory=(self.device.type == 'cuda'),
                persistent_workers=True if self.compute.config.dl_num_workers > 0 else False,
            )
        else:
            val_loader = None

        # Loss function
        criterion = nn.MSELoss()

        # Early stopping
        best_val_loss = float('inf')
        patience_counter = 0

        # Training loop
        for epoch in range(self.config.epochs):
            # Reset peak memory stats at start of epoch
            if self.device.type == 'cuda' and epoch == 0:
                self.compute.reset_peak_memory_stats()

            # Training phase
            self.model.train()
            train_loss = 0.0

            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device, non_blocking=(self.device.type == 'cuda'))
                batch_y = batch_y.to(self.device, non_blocking=(self.device.type == 'cuda')).unsqueeze(1)

                self.optimizer.zero_grad()

                # Mixed precision forward pass
                if self.use_amp:
                    with torch.autocast(device_type='cuda', dtype=self.amp_dtype):
                        outputs = self.model(batch_X)
                        loss = criterion(outputs, batch_y)

                    # Backward pass
                    if self.scaler is not None:
                        # FP16: use GradScaler
                        self.scaler.scale(loss).backward()
                        self.scaler.unscale_(self.optimizer)
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                    else:
                        # BF16: no scaler needed (better numeric stability)
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                        self.optimizer.step()
                else:
                    # Standard forward/backward
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_y)
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                    self.optimizer.step()

                train_loss += loss.item()

            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)

            # Validation phase
            if val_loader is not None:
                self.model.eval()
                val_loss = 0.0

                with torch.no_grad():
                    for batch_X, batch_y in val_loader:
                        batch_X = batch_X.to(self.device, non_blocking=(self.device.type == 'cuda'))
                        batch_y = batch_y.to(self.device, non_blocking=(self.device.type == 'cuda')).unsqueeze(1)

                        if self.use_amp:
                            with torch.autocast(device_type='cuda', dtype=self.amp_dtype):
                                outputs = self.model(batch_X)
                                loss = criterion(outputs, batch_y)
                        else:
                            outputs = self.model(batch_X)
                            loss = criterion(outputs, batch_y)

                        val_loss += loss.item()

                val_loss /= len(val_loader)
                self.val_losses.append(val_loss)

                # Learning rate scheduling
                self.scheduler.step(val_loss)

                # Early stopping
                if val_loss < best_val_loss - self.config.min_delta:
                    best_val_loss = val_loss
                    patience_counter = 0
                else:
                    patience_counter += 1

                if patience_counter >= self.config.patience:
                    logger.info(f"\n⏹️  Early stopping at epoch {epoch+1}")
                    break

                # Log progress
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"   Epoch {epoch+1}/{self.config.epochs} | "
                        f"Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}"
                    )
            else:
                # No validation set
                if (epoch + 1) % 10 == 0:
                    logger.info(f"   Epoch {epoch+1}/{self.config.epochs} | Train Loss: {train_loss:.6f}")

            # Periodic cleanup (every 10 epochs)
            if (epoch + 1) % 10 == 0 and self.device.type == 'cuda':
                self.compute.optimize_memory()

        logger.info("✅ Training completed")

        # Final cleanup
        if self.device.type == 'cuda':
            self.compute.cleanup_after_training()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions

        Args:
            X: Input features (samples, seq_len, features)

        Returns:
            Predictions (samples,)
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        self.model.eval()

        dataset = TimeSeriesDataset(X, np.zeros(len(X)))  # Dummy targets
        loader = DataLoader(
            dataset,
            batch_size=self.config.batch_size,
            shuffle=False,
            num_workers=self.compute.config.dl_num_workers,
            pin_memory=(self.device.type == 'cuda'),
            persistent_workers=False,  # Not needed for single inference
        )

        predictions = []

        with torch.no_grad():
            for batch_X, _ in loader:
                batch_X = batch_X.to(self.device, non_blocking=(self.device.type == 'cuda'))

                if self.use_amp:
                    with torch.autocast(device_type='cuda', dtype=self.amp_dtype):
                        outputs = self.model(batch_X)
                else:
                    outputs = self.model(batch_X)

                predictions.append(outputs.cpu().numpy())

        predictions = np.concatenate(predictions, axis=0).squeeze()
        return predictions


# Example usage
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    # Initialize compute
    from backend.config.compute_config import initialize_compute
    initialize_compute(mode='hybrid')

    # Generate sample data
    np.random.seed(42)
    n_samples = 5000
    seq_len = 60
    n_features = 10

    X = np.random.randn(n_samples, seq_len, n_features)
    y = np.random.randn(n_samples)

    # Split data
    split_idx = int(n_samples * 0.8)
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    # Train LSTM
    lstm_trainer = DeepLearningTrainer(model_type='lstm')
    lstm_trainer.build_model(input_size=n_features, seq_len=seq_len)
    lstm_trainer.fit(X_train, y_train, X_test, y_test)

    # Predict
    predictions = lstm_trainer.predict(X_test)
    print(f"\n✅ Predictions shape: {predictions.shape}")
