"""
Real-time Feature Calculator
Calculates same features as training data for live inference
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from collections import deque
import logging

logger = logging.getLogger(__name__)


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


class RealtimeFeatureCalculator:
    """
    Maintains a rolling window of OHLCV data and calculates features in real-time
    Matches the features from AdvancedDataCollector for consistency
    """

    def __init__(self, symbol: str, timeframe: str, window_size: int = 500):
        """
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '5m', '1h')
            window_size: Number of candles to keep in memory (for indicators like SMA_200)
        """
        self.symbol = symbol
        self.timeframe = timeframe
        self.window_size = window_size

        # Rolling OHLCV buffer
        self.ohlcv_buffer = deque(maxlen=window_size)

        # CVD tracking
        self.cvd = 0.0

    def add_candle(self, candle: Dict) -> None:
        """
        Add a new candle to the buffer

        Args:
            candle: Dict with keys: open_time, open, high, low, close, volume,
                    taker_buy_base (optional)
        """
        self.ohlcv_buffer.append(candle)

    def get_latest_features(self) -> Dict:
        """
        Calculate all features for the latest candle
        Returns a dict matching the training data columns
        """
        if len(self.ohlcv_buffer) < 200:
            logger.warning(f"Only {len(self.ohlcv_buffer)} candles in buffer, need 200+ for all features")
            return None

        # Convert buffer to DataFrame
        df = pd.DataFrame(list(self.ohlcv_buffer))

        # Calculate all features (same as training)
        df = self._calculate_technical_indicators(df)
        df = self._calculate_cvd(df)
        df = self._calculate_volatility(df)

        # Return only the latest row as dict
        latest = df.iloc[-1].to_dict()

        return latest

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators (matches AdvancedDataCollector)"""
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume']

        # RSI (14, 21)
        df['rsi_14'] = calculate_rsi(close, 14)
        df['rsi_21'] = calculate_rsi(close, 21)

        # MACD (12, 26, 9)
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']

        # Bollinger Bands (20, 2)
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (close - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])

        # SMAs
        df['sma_20'] = close.rolling(20).mean()
        df['sma_50'] = close.rolling(50).mean()
        df['sma_200'] = close.rolling(200).mean()

        # EMAs
        df['ema_9'] = close.ewm(span=9, adjust=False).mean()
        df['ema_21'] = close.ewm(span=21, adjust=False).mean()
        df['ema_50'] = close.ewm(span=50, adjust=False).mean()

        # Price distance from MAs
        df['dist_sma20'] = (close - df['sma_20']) / df['sma_20']
        df['dist_sma50'] = (close - df['sma_50']) / df['sma_50']
        df['dist_ema21'] = (close - df['ema_21']) / df['ema_21']

        # Volume features
        df['volume_sma_20'] = volume.rolling(20).mean()
        df['volume_ratio'] = volume / df['volume_sma_20']
        df['volume_momentum'] = volume.pct_change(5)

        # ATR (14)
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr_14'] = true_range.rolling(14).mean()
        df['atr_ratio'] = df['atr_14'] / close

        return df

    def _calculate_cvd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate CVD (matches AdvancedDataCollector)
        Uses OHLC proxy method by default
        """
        # OHLC proxy method (same as training data)
        eps = 1e-9
        range_hl = df['high'] - df['low'] + eps
        w = ((df['close'] - df['low']) / range_hl).clip(0, 1)
        buy_vol = df['volume'] * w
        sell_vol = df['volume'] * (1 - w)
        df['delta_vol'] = buy_vol - sell_vol
        df['cvd'] = df['delta_vol'].cumsum()

        # CVD derivatives
        df['cvd_change'] = df['cvd'].diff()
        df['cvd_momentum'] = df['cvd'].diff(5)

        return df

    def _calculate_volatility(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility metrics"""
        returns = df['close'].pct_change()

        df['volatility_5'] = returns.rolling(5).std()
        df['volatility_20'] = returns.rolling(20).std()
        df['volatility_ratio'] = df['volatility_5'] / df['volatility_20']

        return df

    def update_from_aggr_trade(self, trade: Dict) -> None:
        """
        Update real-time CVD from aggr.trade data

        Args:
            trade: {
                'price': float,
                'size': float,
                'side': 'buy' or 'sell',
                'timestamp': int
            }
        """
        # Update CVD
        if trade['side'] == 'buy':
            self.cvd += trade['size']
        else:
            self.cvd -= trade['size']

    def get_current_cvd(self) -> float:
        """Get current CVD value from aggr.trade"""
        return self.cvd

    def reset_cvd(self):
        """Reset CVD counter"""
        self.cvd = 0.0
