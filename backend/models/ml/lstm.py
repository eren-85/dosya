"""
LSTM model for trend prediction
"""

import torch
import torch.nn as nn
from typing import Tuple, Optional
import numpy as np


class LSTMTrendPredictor(nn.Module):
    """
    LSTM model for time-series trend prediction
    Predicts future price direction and magnitude
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        bidirectional: bool = True,
        output_size: int = 1
    ):
        """
        Args:
            input_size: Number of input features
            hidden_size: LSTM hidden size
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            bidirectional: Use bidirectional LSTM
            output_size: Output dimension (1 for regression, 3 for up/down/flat)
        """
        super().__init__()

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.output_size = output_size

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
            batch_first=True
        )

        # Attention mechanism
        lstm_output_size = hidden_size * 2 if bidirectional else hidden_size
        self.attention = nn.Sequential(
            nn.Linear(lstm_output_size, lstm_output_size // 2),
            nn.Tanh(),
            nn.Linear(lstm_output_size // 2, 1)
        )

        # Output layers
        self.fc = nn.Sequential(
            nn.Linear(lstm_output_size, lstm_output_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(lstm_output_size // 2, output_size)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass

        Args:
            x: Input tensor (batch, seq_len, features)

        Returns:
            predictions: (batch, output_size)
            attention_weights: (batch, seq_len) - for interpretability
        """
        batch_size, seq_len, _ = x.shape

        # LSTM forward
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Attention mechanism
        attention_scores = self.attention(lstm_out)  # (batch, seq_len, 1)
        attention_weights = torch.softmax(attention_scores, dim=1)

        # Apply attention
        context = torch.sum(lstm_out * attention_weights, dim=1)  # (batch, hidden_size)

        # Final prediction
        predictions = self.fc(context)

        return predictions, attention_weights.squeeze(-1)

    def predict_trend(
        self,
        x: torch.Tensor,
        classification: bool = False
    ) -> dict:
        """
        Predict trend with confidence

        Args:
            x: Input tensor
            classification: If True, output class probabilities (up/down/flat)

        Returns:
            {
                'prediction': float or class_idx,
                'confidence': float,
                'attention_weights': tensor
            }
        """
        self.eval()
        with torch.no_grad():
            predictions, attention_weights = self.forward(x)

            if classification:
                probs = torch.softmax(predictions, dim=-1)
                class_idx = torch.argmax(probs, dim=-1)
                confidence = torch.max(probs, dim=-1).values

                return {
                    'prediction': class_idx.item(),
                    'probabilities': probs.cpu().numpy(),
                    'confidence': confidence.item(),
                    'attention_weights': attention_weights.cpu().numpy()
                }
            else:
                # Regression
                return {
                    'prediction': predictions.squeeze(-1).item(),
                    'confidence': 1.0,  # No confidence for regression
                    'attention_weights': attention_weights.cpu().numpy()
                }


class MultiHorizonLSTM(nn.Module):
    """
    LSTM that predicts multiple time horizons simultaneously
    E.g., 1h, 4h, 1d ahead predictions
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        horizons: list = [1, 4, 24]  # Hours ahead
    ):
        super().__init__()

        self.horizons = horizons

        # Shared LSTM encoder
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=True,
            batch_first=True
        )

        # Separate prediction heads for each horizon
        lstm_output_size = hidden_size * 2
        self.prediction_heads = nn.ModuleDict({
            f'horizon_{h}h': nn.Sequential(
                nn.Linear(lstm_output_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size, 1)
            )
            for h in horizons
        })

    def forward(self, x: torch.Tensor) -> dict:
        """
        Forward pass

        Args:
            x: Input (batch, seq_len, features)

        Returns:
            {
                'horizon_1h': (batch, 1),
                'horizon_4h': (batch, 1),
                'horizon_24h': (batch, 1)
            }
        """
        # Shared LSTM encoding
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Use last hidden state
        last_hidden = lstm_out[:, -1, :]

        # Predict for each horizon
        predictions = {}
        for h in self.horizons:
            head = self.prediction_heads[f'horizon_{h}h']
            pred = head(last_hidden)
            predictions[f'horizon_{h}h'] = pred

        return predictions


class LSTMTrainer:
    """Trainer for LSTM models"""

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 1e-3,
        device: str = 'cpu'
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()

        self.train_losses = []
        self.val_losses = []

    def train_epoch(
        self,
        train_loader,
        clip_grad: float = 1.0
    ) -> float:
        """Train one epoch"""
        self.model.train()
        total_loss = 0

        for batch_x, batch_y in train_loader:
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)

            # Forward
            if isinstance(self.model, LSTMTrendPredictor):
                predictions, _ = self.model(batch_x)
            else:  # MultiHorizonLSTM
                predictions_dict = self.model(batch_x)
                predictions = predictions_dict[list(predictions_dict.keys())[0]]

            loss = self.criterion(predictions.squeeze(), batch_y)

            # Backward
            self.optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), clip_grad)

            self.optimizer.step()

            total_loss += loss.item()

        avg_loss = total_loss / len(train_loader)
        self.train_losses.append(avg_loss)
        return avg_loss

    def validate(self, val_loader) -> float:
        """Validate model"""
        self.model.eval()
        total_loss = 0

        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x = batch_x.to(self.device)
                batch_y = batch_y.to(self.device)

                if isinstance(self.model, LSTMTrendPredictor):
                    predictions, _ = self.model(batch_x)
                else:
                    predictions_dict = self.model(batch_x)
                    predictions = predictions_dict[list(predictions_dict.keys())[0]]

                loss = self.criterion(predictions.squeeze(), batch_y)
                total_loss += loss.item()

        avg_loss = total_loss / len(val_loader)
        self.val_losses.append(avg_loss)
        return avg_loss

    def fit(
        self,
        train_loader,
        val_loader,
        epochs: int = 100,
        early_stopping_patience: int = 10
    ):
        """Full training loop with early stopping"""
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(epochs):
            train_loss = self.train_epoch(train_loader)
            val_loss = self.validate(val_loader)

            print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'best_lstm_model.pt')
            else:
                patience_counter += 1

            if patience_counter >= early_stopping_patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

        # Load best model
        self.model.load_state_dict(torch.load('best_lstm_model.pt'))
