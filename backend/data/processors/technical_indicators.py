"""
Technical indicators calculation
Supports 200+ indicators including:
- Trend (SMA, EMA, MACD, ADX)
- Momentum (RSI, Stochastic, CCI)
- Volatility (Bollinger Bands, ATR, Keltner)
- Volume (OBV, VWAP, MFI)
- Smart Money (Order Blocks, FVG, Liquidity)
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import pandas_ta as ta


class TechnicalIndicators:
    """
    Comprehensive technical indicators calculator
    """

    @staticmethod
    def add_all_indicators(df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
        """
        Add all technical indicators to DataFrame

        Args:
            df: DataFrame with columns [time, open, high, low, close, volume]
            config: Optional configuration for indicator parameters

        Returns:
            DataFrame with added indicator columns
        """
        df = df.copy()

        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must contain columns: {required_cols}")

        # === TREND INDICATORS ===
        df = TechnicalIndicators._add_trend_indicators(df)

        # === MOMENTUM INDICATORS ===
        df = TechnicalIndicators._add_momentum_indicators(df)

        # === VOLATILITY INDICATORS ===
        df = TechnicalIndicators._add_volatility_indicators(df)

        # === VOLUME INDICATORS ===
        df = TechnicalIndicators._add_volume_indicators(df)

        # === SMART MONEY / ICT ===
        df = TechnicalIndicators._add_smart_money_indicators(df)

        # === CUSTOM FEATURES ===
        df = TechnicalIndicators._add_custom_features(df)

        return df

    @staticmethod
    def _add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add trend-following indicators"""

        # Moving Averages
        for period in [9, 20, 50, 100, 200]:
            df[f'sma_{period}'] = ta.sma(df['close'], length=period)
            df[f'ema_{period}'] = ta.ema(df['close'], length=period)

        # MACD
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        if macd is not None:
            df = pd.concat([df, macd], axis=1)

        # ADX (Average Directional Index)
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None:
            df = pd.concat([df, adx], axis=1)

        # Supertrend
        supertrend = ta.supertrend(df['high'], df['low'], df['close'], length=10, multiplier=3)
        if supertrend is not None:
            df = pd.concat([df, supertrend], axis=1)

        # Parabolic SAR
        psar = ta.psar(df['high'], df['low'], df['close'])
        if psar is not None:
            df = pd.concat([df, psar], axis=1)

        # Ichimoku Cloud
        ichimoku = ta.ichimoku(df['high'], df['low'], df['close'])
        if ichimoku is not None and len(ichimoku) > 0:
            df = pd.concat([df, ichimoku[0]], axis=1)

        return df

    @staticmethod
    def _add_momentum_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add momentum oscillators"""

        # RSI (multiple periods)
        for period in [7, 14, 21]:
            df[f'rsi_{period}'] = ta.rsi(df['close'], length=period)

        # Stochastic
        stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3)
        if stoch is not None:
            df = pd.concat([df, stoch], axis=1)

        # CCI (Commodity Channel Index)
        df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)

        # Williams %R
        df['willr'] = ta.willr(df['high'], df['low'], df['close'], length=14)

        # ROC (Rate of Change)
        df['roc'] = ta.roc(df['close'], length=10)

        # CMO (Chande Momentum Oscillator)
        df['cmo'] = ta.cmo(df['close'], length=14)

        # Ultimate Oscillator
        df['uo'] = ta.uo(df['high'], df['low'], df['close'])

        # Awesome Oscillator
        df['ao'] = ta.ao(df['high'], df['low'])

        return df

    @staticmethod
    def _add_volatility_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volatility indicators"""

        # Bollinger Bands
        bbands = ta.bbands(df['close'], length=20, std=2)
        if bbands is not None:
            df = pd.concat([df, bbands], axis=1)

        # ATR (Average True Range)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # Keltner Channels
        kc = ta.kc(df['high'], df['low'], df['close'], length=20, scalar=2)
        if kc is not None:
            df = pd.concat([df, kc], axis=1)

        # Donchian Channels
        dc = ta.donchian(df['high'], df['low'], lower_length=20, upper_length=20)
        if dc is not None:
            df = pd.concat([df, dc], axis=1)

        # Historical Volatility
        df['hvol'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252) * 100

        # True Range
        df['true_range'] = ta.true_range(df['high'], df['low'], df['close'])

        return df

    @staticmethod
    def _add_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add volume-based indicators"""

        # OBV (On-Balance Volume)
        df['obv'] = ta.obv(df['close'], df['volume'])

        # VWAP (Volume Weighted Average Price)
        df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

        # MFI (Money Flow Index)
        df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)

        # CMF (Chaikin Money Flow)
        df['cmf'] = ta.cmf(df['high'], df['low'], df['close'], df['volume'], length=20)

        # AD (Accumulation/Distribution)
        df['ad'] = ta.ad(df['high'], df['low'], df['close'], df['volume'])

        # ADOSC (Chaikin Oscillator)
        df['adosc'] = ta.adosc(df['high'], df['low'], df['close'], df['volume'])

        # PVT (Price Volume Trend)
        df['pvt'] = ta.pvt(df['close'], df['volume'])

        # Volume SMA ratio
        df['volume_sma_20'] = ta.sma(df['volume'], length=20)
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']

        return df

    @staticmethod
    def _add_smart_money_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Add Smart Money / ICT concepts
        - Order Blocks
        - Fair Value Gaps (FVG)
        - Liquidity Voids
        - Market Structure
        """

        # Market Structure Break (MSB)
        df['higher_high'] = df['high'] > df['high'].shift(1)
        df['higher_low'] = df['low'] > df['low'].shift(1)
        df['lower_high'] = df['high'] < df['high'].shift(1)
        df['lower_low'] = df['low'] < df['low'].shift(1)

        # Swing highs and lows (for Order Blocks)
        df['swing_high'] = TechnicalIndicators._detect_swing_points(df['high'], order=5)
        df['swing_low'] = TechnicalIndicators._detect_swing_points(df['low'], order=5, mode='low')

        # Fair Value Gaps (FVG)
        df['fvg_bullish'] = TechnicalIndicators._detect_fvg(df, direction='bull')
        df['fvg_bearish'] = TechnicalIndicators._detect_fvg(df, direction='bear')

        # Liquidity levels (based on volume)
        df['high_volume'] = df['volume'] > df['volume'].rolling(50).quantile(0.95)
        df['low_volume'] = df['volume'] < df['volume'].rolling(50).quantile(0.05)

        # Imbalance (difference between wicks)
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['wick_ratio'] = df['upper_wick'] / (df['lower_wick'] + 1e-10)

        return df

    @staticmethod
    def _detect_swing_points(series: pd.Series, order: int = 5, mode: str = 'high') -> pd.Series:
        """
        Detect swing highs or lows

        Args:
            series: Price series (high or low)
            order: Number of periods to check on each side
            mode: 'high' or 'low'

        Returns:
            Boolean series indicating swing points
        """
        swings = pd.Series(False, index=series.index)

        for i in range(order, len(series) - order):
            if mode == 'high':
                # Swing high: current value is highest in window
                is_swing = all(series.iloc[i] >= series.iloc[i-j] for j in range(1, order+1)) and \
                           all(series.iloc[i] >= series.iloc[i+j] for j in range(1, order+1))
            else:
                # Swing low: current value is lowest in window
                is_swing = all(series.iloc[i] <= series.iloc[i-j] for j in range(1, order+1)) and \
                           all(series.iloc[i] <= series.iloc[i+j] for j in range(1, order+1))

            swings.iloc[i] = is_swing

        return swings

    @staticmethod
    def _detect_fvg(df: pd.DataFrame, direction: str = 'bull') -> pd.Series:
        """
        Detect Fair Value Gaps

        Bullish FVG: current low > previous high (gap up)
        Bearish FVG: current high < previous low (gap down)
        """
        fvg = pd.Series(False, index=df.index)

        if direction == 'bull':
            # Bullish FVG: gap between current low and 2-candle-back high
            fvg = (df['low'] > df['high'].shift(2)) & (df['close'] > df['open'])
        else:
            # Bearish FVG: gap between current high and 2-candle-back low
            fvg = (df['high'] < df['low'].shift(2)) & (df['close'] < df['open'])

        return fvg

    @staticmethod
    def _add_custom_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add custom engineered features"""

        # Price momentum (multiple periods)
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'].pct_change(period) * 100

        # Distance from MAs (%)
        for period in [20, 50, 200]:
            df[f'dist_from_sma_{period}'] = (df['close'] / df[f'sma_{period}'] - 1) * 100

        # Candle patterns
        df['body_size'] = abs(df['close'] - df['open'])
        df['body_pct'] = df['body_size'] / (df['high'] - df['low'] + 1e-10) * 100

        df['is_green'] = (df['close'] > df['open']).astype(int)
        df['is_doji'] = (df['body_pct'] < 5).astype(int)

        # Consecutive candles
        df['green_streak'] = (df['is_green'].groupby((df['is_green'] != df['is_green'].shift()).cumsum()).cumsum())

        # Range metrics
        df['range'] = df['high'] - df['low']
        df['range_pct'] = (df['range'] / df['close']) * 100

        # Volatility regime
        df['volatility_20'] = df['close'].pct_change().rolling(20).std()
        df['volatility_regime'] = pd.cut(
            df['volatility_20'],
            bins=3,
            labels=['low', 'medium', 'high']
        )

        return df

    @staticmethod
    def calculate_fibonacci_levels(
        swing_high: float,
        swing_low: float,
        direction: str = 'retracement'
    ) -> Dict[str, float]:
        """
        Calculate Fibonacci levels

        Args:
            swing_high: Recent swing high
            swing_low: Recent swing low
            direction: 'retracement' or 'extension'

        Returns:
            Dictionary of Fibonacci levels
        """
        diff = swing_high - swing_low

        if direction == 'retracement':
            # Fibonacci retracement (for pullbacks)
            return {
                '0.0': swing_low,
                '0.236': swing_low + diff * 0.236,
                '0.382': swing_low + diff * 0.382,
                '0.5': swing_low + diff * 0.5,
                '0.618': swing_low + diff * 0.618,  # Golden ratio
                '0.705': swing_low + diff * 0.705,  # OTE (Optimal Trade Entry)
                '0.786': swing_low + diff * 0.786,
                '1.0': swing_high
            }
        else:
            # Fibonacci extension (for targets)
            return {
                '1.0': swing_high,
                '1.272': swing_high + diff * 0.272,
                '1.414': swing_high + diff * 0.414,
                '1.618': swing_high + diff * 0.618,  # Golden extension
                '2.0': swing_high + diff * 1.0,
                '2.618': swing_high + diff * 1.618
            }

    @staticmethod
    def detect_order_blocks(df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
        """
        Detect Order Blocks (last candle before strong move)

        Order Block: The last opposing candle before a strong directional move
        """
        df = df.copy()

        df['bullish_ob'] = False
        df['bearish_ob'] = False
        df['ob_level'] = np.nan

        # Detect bullish order blocks
        for i in range(lookback, len(df)):
            # Look for bearish candle followed by strong bullish move
            if df['close'].iloc[i-1] < df['open'].iloc[i-1]:  # Bearish candle
                next_move = df['close'].iloc[i:i+5].max() - df['close'].iloc[i-1]
                if next_move > df['atr'].iloc[i-1] * 2:  # Strong move
                    df.loc[df.index[i-1], 'bullish_ob'] = True
                    df.loc[df.index[i-1], 'ob_level'] = df['low'].iloc[i-1]

        # Detect bearish order blocks
        for i in range(lookback, len(df)):
            # Look for bullish candle followed by strong bearish move
            if df['close'].iloc[i-1] > df['open'].iloc[i-1]:  # Bullish candle
                next_move = df['close'].iloc[i-1] - df['close'].iloc[i:i+5].min()
                if next_move > df['atr'].iloc[i-1] * 2:  # Strong move
                    df.loc[df.index[i-1], 'bearish_ob'] = True
                    df.loc[df.index[i-1], 'ob_level'] = df['high'].iloc[i-1]

        return df
