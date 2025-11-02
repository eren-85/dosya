"""
Smart Money Concept Indicators
Converted from Pine Script to Python

Includes:
- Order Block Finder
- Fair Value Gaps
- Liquidity Sweeps
- Break of Structure
- Kill Zones
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import List, Dict, Tuple, Optional


class OrderBlockDetector:
    """
    Order Block Finder - Detects institutional buying/selling zones
    Converted from Pine Script indicator
    """

    def __init__(self, swing_length: int = 10):
        """
        Args:
            swing_length: Number of candles to look back for swing detection
        """
        self.swing_length = swing_length

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect order blocks in price data

        Args:
            df: DataFrame with columns ['open', 'high', 'low', 'close']

        Returns:
            DataFrame with additional columns:
            - 'bullish_ob': Boolean, True if bullish order block
            - 'bearish_ob': Boolean, True if bearish order block
            - 'ob_top': Float, top of order block zone
            - 'ob_bottom': Float, bottom of order block zone
        """
        df = df.copy()
        df['bullish_ob'] = False
        df['bearish_ob'] = False
        df['ob_top'] = np.nan
        df['ob_bottom'] = np.nan

        for i in range(self.swing_length, len(df) - self.swing_length):
            # Get current and surrounding candles
            current = df.iloc[i]
            prev_candles = df.iloc[i - self.swing_length:i]
            next_candles = df.iloc[i + 1:i + self.swing_length + 1]

            # Bullish Order Block:
            # Strong bearish candle followed by bullish reversal
            is_bearish = current['close'] < current['open']
            body_size = abs(current['close'] - current['open'])
            candle_range = current['high'] - current['low']

            # Check if strong bearish candle (body > 70% of range)
            if is_bearish and body_size > candle_range * 0.7:
                # Check if followed by bullish movement
                bullish_after = (next_candles['close'] > next_candles['open']).sum()
                if bullish_after >= self.swing_length * 0.6:  # 60% bullish candles after
                    df.at[df.index[i], 'bullish_ob'] = True
                    df.at[df.index[i], 'ob_bottom'] = current['low']
                    df.at[df.index[i], 'ob_top'] = current['open']  # Body top

            # Bearish Order Block:
            # Strong bullish candle followed by bearish reversal
            is_bullish = current['close'] > current['open']

            if is_bullish and body_size > candle_range * 0.7:
                # Check if followed by bearish movement
                bearish_after = (next_candles['close'] < next_candles['open']).sum()
                if bearish_after >= self.swing_length * 0.6:  # 60% bearish candles after
                    df.at[df.index[i], 'bearish_ob'] = True
                    df.at[df.index[i], 'ob_top'] = current['high']
                    df.at[df.index[i], 'ob_bottom'] = current['open']  # Body bottom

        return df


class FairValueGapDetector:
    """
    Fair Value Gap (FVG) Detector
    Identifies imbalance zones in price action
    """

    def __init__(self, min_gap_size: float = 0.001):
        """
        Args:
            min_gap_size: Minimum gap size as percentage of price (0.001 = 0.1%)
        """
        self.min_gap_size = min_gap_size

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect fair value gaps

        Returns:
            DataFrame with additional columns:
            - 'bullish_fvg': Boolean
            - 'bearish_fvg': Boolean
            - 'fvg_top': Float
            - 'fvg_bottom': Float
        """
        df = df.copy()
        df['bullish_fvg'] = False
        df['bearish_fvg'] = False
        df['fvg_top'] = np.nan
        df['fvg_bottom'] = np.nan

        for i in range(1, len(df) - 1):
            prev = df.iloc[i - 1]
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]

            # Bullish FVG: Gap between previous high and next low
            if prev['high'] < next_candle['low']:
                gap_size = (next_candle['low'] - prev['high']) / current['close']
                if gap_size >= self.min_gap_size:
                    df.at[df.index[i], 'bullish_fvg'] = True
                    df.at[df.index[i], 'fvg_bottom'] = prev['high']
                    df.at[df.index[i], 'fvg_top'] = next_candle['low']

            # Bearish FVG: Gap between previous low and next high
            if prev['low'] > next_candle['high']:
                gap_size = (prev['low'] - next_candle['high']) / current['close']
                if gap_size >= self.min_gap_size:
                    df.at[df.index[i], 'bearish_fvg'] = True
                    df.at[df.index[i], 'fvg_top'] = prev['low']
                    df.at[df.index[i], 'fvg_bottom'] = next_candle['high']

        return df


class LiquiditySweepDetector:
    """
    Liquidity Sweep Detector
    Identifies stop hunts and liquidity grabs
    """

    def __init__(self, lookback: int = 20):
        """
        Args:
            lookback: Number of candles to look back for swing highs/lows
        """
        self.lookback = lookback

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect liquidity sweeps

        Returns:
            DataFrame with additional columns:
            - 'high_sweep': Boolean, liquidity grab above
            - 'low_sweep': Boolean, liquidity grab below
        """
        df = df.copy()
        df['high_sweep'] = False
        df['low_sweep'] = False

        for i in range(self.lookback, len(df)):
            current = df.iloc[i]
            recent = df.iloc[i - self.lookback:i]

            recent_high = recent['high'].max()
            recent_low = recent['low'].min()

            # High sweep: Breaks above recent high then closes bearish
            if current['high'] > recent_high and current['close'] < current['open']:
                df.at[df.index[i], 'high_sweep'] = True

            # Low sweep: Breaks below recent low then closes bullish
            if current['low'] < recent_low and current['close'] > current['open']:
                df.at[df.index[i], 'low_sweep'] = True

        return df


class BreakOfStructureDetector:
    """
    Break of Structure (BOS) Detector
    Identifies trend changes based on market structure
    """

    def __init__(self, swing_length: int = 5):
        self.swing_length = swing_length

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect break of structure

        Returns:
            DataFrame with additional columns:
            - 'bullish_bos': Boolean
            - 'bearish_bos': Boolean
        """
        df = df.copy()
        df['bullish_bos'] = False
        df['bearish_bos'] = False

        # Find swing highs and lows
        df['swing_high'] = df['high'].rolling(window=self.swing_length * 2 + 1, center=True).max()
        df['swing_low'] = df['low'].rolling(window=self.swing_length * 2 + 1, center=True).min()

        df['is_swing_high'] = df['high'] == df['swing_high']
        df['is_swing_low'] = df['low'] == df['swing_low']

        for i in range(self.swing_length * 2, len(df)):
            # Bullish BOS: Price breaks above previous swing high
            recent_swing_highs = df.iloc[i - self.swing_length * 2:i][df['is_swing_high'] == True]
            if len(recent_swing_highs) > 0:
                last_swing_high = recent_swing_highs['high'].iloc[-1]
                if df.iloc[i]['close'] > last_swing_high:
                    df.at[df.index[i], 'bullish_bos'] = True

            # Bearish BOS: Price breaks below previous swing low
            recent_swing_lows = df.iloc[i - self.swing_length * 2:i][df['is_swing_low'] == True]
            if len(recent_swing_lows) > 0:
                last_swing_low = recent_swing_lows['low'].iloc[-1]
                if df.iloc[i]['close'] < last_swing_low:
                    df.at[df.index[i], 'bearish_bos'] = True

        return df


class KillZoneDetector:
    """
    Kill Zone Detector
    Identifies optimal trading sessions (Asian, London, New York)
    Based on UTC time
    """

    ASIAN_START = time(0, 0)  # 00:00 UTC
    ASIAN_END = time(9, 0)  # 09:00 UTC

    LONDON_START = time(7, 0)  # 07:00 UTC
    LONDON_END = time(16, 0)  # 16:00 UTC

    NY_START = time(13, 0)  # 13:00 UTC
    NY_END = time(22, 0)  # 22:00 UTC

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect kill zones based on timestamp

        Args:
            df: DataFrame with DatetimeIndex in UTC

        Returns:
            DataFrame with additional columns:
            - 'asian_killzone': Boolean
            - 'london_killzone': Boolean
            - 'ny_killzone': Boolean
        """
        df = df.copy()

        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame index must be DatetimeIndex")

        df['hour'] = df.index.hour
        df['minute'] = df.index.minute

        # Asian session (00:00 - 09:00 UTC)
        df['asian_killzone'] = (
            (df['hour'] >= self.ASIAN_START.hour) &
            (df['hour'] < self.ASIAN_END.hour)
        )

        # London session (07:00 - 16:00 UTC)
        df['london_killzone'] = (
            (df['hour'] >= self.LONDON_START.hour) &
            (df['hour'] < self.LONDON_END.hour)
        )

        # New York session (13:00 - 22:00 UTC)
        df['ny_killzone'] = (
            (df['hour'] >= self.NY_START.hour) &
            (df['hour'] < self.NY_END.hour)
        )

        df = df.drop(columns=['hour', 'minute'])

        return df


class SmartMoneyIndicators:
    """
    Combined Smart Money Concept Indicators
    """

    def __init__(self):
        self.order_blocks = OrderBlockDetector()
        self.fvg = FairValueGapDetector()
        self.liquidity_sweeps = LiquiditySweepDetector()
        self.bos = BreakOfStructureDetector()
        self.kill_zones = KillZoneDetector()

    def apply_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all indicators to DataFrame

        Args:
            df: OHLC DataFrame with DatetimeIndex

        Returns:
            DataFrame with all indicator columns added
        """
        df = self.order_blocks.detect(df)
        df = self.fvg.detect(df)
        df = self.liquidity_sweeps.detect(df)
        df = self.bos.detect(df)

        try:
            df = self.kill_zones.detect(df)
        except ValueError:
            # If index is not DatetimeIndex, skip kill zones
            pass

        return df
