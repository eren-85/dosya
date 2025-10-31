#!/usr/bin/env python3
"""
LSTM Model Inference Script

Usage:
    python -m backend.inference.predict_lstm --model models/trained/lstm_BTCUSDT_1h.pt --symbol BTCUSDT

Features:
    - Loads trained LSTM model
    - Makes real-time predictions
    - Returns trading signals with confidence
"""

import argparse
import sys
from pathlib import Path
import torch
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.ml.lstm import LSTMTrendPredictor


def load_model(model_path):
    """Load trained model and metadata"""

    checkpoint = torch.load(model_path, map_location='cpu')

    # Create model
    config = checkpoint['model_config']
    model = LSTMTrendPredictor(**config)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    scaler = checkpoint['scaler']
    feature_cols = checkpoint['feature_cols']

    return model, scaler, feature_cols


def predict(model, data, scaler, device='cpu'):
    """
    Make prediction

    Args:
        model: Trained LSTM model
        data: Input sequence (seq_length, n_features)
        scaler: Fitted StandardScaler
        device: 'cpu' or 'cuda'

    Returns:
        probability: Float between 0-1 (probability of price going up)
        signal: 'LONG', 'SHORT', or 'WAIT'
        confidence: Float between 0-1
    """

    # Scale data
    data_scaled = scaler.transform(data)

    # Convert to tensor and add batch dimension
    X = torch.FloatTensor(data_scaled).unsqueeze(0).to(device)

    # Predict
    with torch.no_grad():
        output = model(X)
        probability = torch.sigmoid(output).item()

    # Generate signal
    if probability > 0.65:
        signal = 'LONG'
        confidence = probability
    elif probability < 0.35:
        signal = 'SHORT'
        confidence = 1 - probability
    else:
        signal = 'WAIT'
        confidence = 0.5

    return probability, signal, confidence


def main():
    parser = argparse.ArgumentParser(description='LSTM Inference')
    parser.add_argument('--model', type=str, required=True, help='Path to trained model')
    parser.add_argument('--symbol', type=str, default='BTCUSDT', help='Trading symbol')
    parser.add_argument('--timeframe', type=str, default='1h', help='Timeframe')

    args = parser.parse_args()

    print("="*60)
    print("🔮 LSTM PREDICTION")
    print("="*60)
    print(f"Model: {args.model}")
    print(f"Symbol: {args.symbol}")
    print(f"Timeframe: {args.timeframe}")
    print()

    # Load model
    print("📂 Loading model...")
    model, scaler, feature_cols = load_model(args.model)
    print(f"✅ Model loaded (features: {len(feature_cols)})")

    # TODO: Load latest data
    # For now, just show how to use it
    print()
    print("📊 To use this model in production:")
    print("   1. Fetch latest OHLCV data (60 candles for seq_length=60)")
    print("   2. Calculate indicators")
    print("   3. Call predict()")
    print()
    print("Example code:")
    print("""
    # Fetch data
    df = get_ohlcv('BTCUSDT', '1h', limit=100)
    df = calculate_indicators(df)

    # Prepare input (last 60 candles)
    X = df[feature_cols].tail(60).values

    # Predict
    prob, signal, conf = predict(model, X, scaler)
    print(f"Signal: {signal} (confidence: {conf:.2%})")
    """)


if __name__ == '__main__':
    main()
