"""
Transformer for pattern recognition in price action
"""

import torch
import torch.nn as nn
from typing import Optional, Tuple
import math


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""

    def __init__(self, d_model: int, max_len: int = 5000):
        super().__init__()

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)

        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.pe[:, :x.size(1)]


class TransformerPatternRecognizer(nn.Module):
    """
    Transformer model for recognizing candlestick patterns and market structures
    """

    PATTERN_CLASSES = [
        'bullish_engulfing', 'bearish_engulfing',
        'hammer', 'shooting_star',
        'doji', 'morning_star', 'evening_star',
        'three_white_soldiers', 'three_black_crows',
        'bull_flag', 'bear_flag',
        'head_and_shoulders', 'inverse_head_and_shoulders',
        'double_top', 'double_bottom',
        'ascending_triangle', 'descending_triangle',
        'no_pattern'
    ]

    def __init__(
        self,
        input_size: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 1024,
        dropout: float = 0.1,
        max_seq_len: int = 200
    ):
        super().__init__()

        self.input_size = input_size
        self.d_model = d_model
        self.num_classes = len(self.PATTERN_CLASSES)

        # Input projection
        self.input_projection = nn.Linear(input_size, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, self.num_classes)
        )

        # Pattern localization head (where in sequence pattern occurs)
        self.localizer = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Linear(d_model // 2, 1),
            nn.Sigmoid()
        )

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass

        Args:
            x: Input (batch, seq_len, input_size)
            mask: Attention mask (batch, seq_len)

        Returns:
            class_logits: (batch, num_classes)
            localization_scores: (batch, seq_len) - where pattern occurs
        """
        # Project input
        x = self.input_projection(x)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Transformer encoding
        if mask is not None:
            mask = mask.bool()

        encoded = self.transformer_encoder(x, src_key_padding_mask=mask)

        # Global average pooling for classification
        pooled = encoded.mean(dim=1)

        # Classification
        class_logits = self.classifier(pooled)

        # Localization (per-timestep)
        localization_scores = self.localizer(encoded).squeeze(-1)

        return class_logits, localization_scores

    def predict_pattern(self, x: torch.Tensor) -> dict:
        """
        Predict pattern with confidence

        Args:
            x: Input tensor

        Returns:
            {
                'pattern': str,
                'confidence': float,
                'location': int (index where pattern is strongest)
            }
        """
        self.eval()
        with torch.no_grad():
            class_logits, localization_scores = self.forward(x)

            # Get predicted class
            probs = torch.softmax(class_logits, dim=-1)
            predicted_class_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, predicted_class_idx].item()

            # Get pattern location
            location_idx = torch.argmax(localization_scores, dim=-1).item()

            return {
                'pattern': self.PATTERN_CLASSES[predicted_class_idx],
                'confidence': confidence,
                'location': location_idx,
                'all_probabilities': {
                    self.PATTERN_CLASSES[i]: probs[0, i].item()
                    for i in range(self.num_classes)
                }
            }


class Multi ScaleTransformer(nn.Module):
    """
    Multi-scale transformer that processes multiple timeframes simultaneously
    """

    def __init__(
        self,
        input_size: int,
        timeframes: list = ['1H', '4H', '1D'],
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 4
    ):
        super().__init__()

        self.timeframes = timeframes

        # Separate encoder for each timeframe
        self.timeframe_encoders = nn.ModuleDict({
            tf: nn.TransformerEncoder(
                nn.TransformerEncoderLayer(d_model, nhead, batch_first=True),
                num_layers=num_layers
            )
            for tf in timeframes
        })

        # Input projections
        self.input_projections = nn.ModuleDict({
            tf: nn.Linear(input_size, d_model)
            for tf in timeframes
        })

        # Cross-timeframe attention
        self.cross_attention = nn.MultiheadAttention(d_model, nhead, batch_first=True)

        # Final classifier
        self.classifier = nn.Sequential(
            nn.Linear(d_model * len(timeframes), d_model),
            nn.ReLU(),
            nn.Linear(d_model, len(TransformerPatternRecognizer.PATTERN_CLASSES))
        )

    def forward(self, inputs: dict) -> torch.Tensor:
        """
        Forward pass

        Args:
            inputs: Dict with keys '1H', '4H', '1D' -> (batch, seq_len, features)

        Returns:
            class_logits: (batch, num_classes)
        """
        timeframe_embeddings = []

        # Encode each timeframe
        for tf in self.timeframes:
            x = inputs[tf]
            x = self.input_projections[tf](x)
            encoded = self.timeframe_encoders[tf](x)
            # Global pool
            pooled = encoded.mean(dim=1)
            timeframe_embeddings.append(pooled)

        # Concatenate timeframe embeddings
        combined = torch.cat(timeframe_embeddings, dim=-1)

        # Classify
        logits = self.classifier(combined)

        return logits
