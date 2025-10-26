"""
Advanced Technical Analysis Module
- Harmonic Patterns (Gartley, Bat, Butterfly, Crab, Shark)
- Divergences (RSI, MACD, Volume)
- Support & Resistance (horizontal levels)
- Trend Lines & Channels
- Enhanced Fibonacci (Golden Zones, OTE levels)
- Swing High/Low Detection
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SwingPoint:
    """Swing high or low point"""
    index: int
    timestamp: datetime
    price: float
    type: str  # 'high' or 'low'
    strength: int  # How many bars on each side


@dataclass
class HarmonicPattern:
    """Detected harmonic pattern"""
    name: str  # 'Gartley', 'Bat', 'Butterfly', 'Crab', 'Shark'
    type: str  # 'bullish' or 'bearish'
    points: Dict[str, float]  # X, A, B, C, D
    indices: Dict[str, int]
    confidence: float
    target: float
    stop_loss: float


@dataclass
class Divergence:
    """Price-indicator divergence"""
    type: str  # 'bullish' or 'bearish'
    indicator: str  # 'RSI', 'MACD', 'Volume'
    strength: str  # 'regular', 'hidden'
    start_index: int
    end_index: int
    confidence: float


@dataclass
class SupportResistance:
    """Support or resistance level"""
    level: float
    type: str  # 'support' or 'resistance'
    strength: int  # Number of touches
    first_touch: int
    last_touch: int
    zone_range: Tuple[float, float]  # (low, high) for zone


@dataclass
class TrendLine:
    """Trend line"""
    type: str  # 'uptrend' or 'downtrend'
    points: List[Tuple[int, float]]  # [(index, price), ...]
    slope: float
    intercept: float
    r_squared: float  # Goodness of fit
    breaks: int  # Number of breaks


@dataclass
class FibonacciLevels:
    """Enhanced Fibonacci retracement levels"""
    swing_high: float
    swing_low: float
    swing_high_idx: int
    swing_low_idx: int
    direction: str  # 'retracement' or 'extension'

    # Standard levels
    level_0: float  # 0%
    level_236: float  # 23.6%
    level_382: float  # 38.2%
    level_500: float  # 50%
    level_618: float  # 61.8%
    level_786: float  # 78.6%
    level_1000: float  # 100%

    # Enhanced levels
    golden_zone_low: float  # 0.618-0.66
    golden_zone_high: float
    golden_zone_382_low: float  # 0.382-0.34
    golden_zone_382_high: float
    ote_high: float  # 0.705 (Optimal Trade Entry)
    ote_low: float  # 0.295


class AdvancedTechnicalAnalysis:
    """
    Advanced technical analysis tools
    """

    @staticmethod
    def detect_swing_points(
        df: pd.DataFrame,
        left_bars: int = 5,
        right_bars: int = 5
    ) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Detect swing highs and lows

        Args:
            df: DataFrame with OHLC data
            left_bars: Bars to left of pivot
            right_bars: Bars to right of pivot

        Returns:
            (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []

        highs = df['high'].values
        lows = df['low'].values

        for i in range(left_bars, len(df) - right_bars):
            # Check swing high
            is_swing_high = True
            for j in range(1, left_bars + 1):
                if highs[i] <= highs[i - j]:
                    is_swing_high = False
                    break
            for j in range(1, right_bars + 1):
                if highs[i] <= highs[i + j]:
                    is_swing_high = False
                    break

            if is_swing_high:
                swing_highs.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[i]['time'],
                    price=highs[i],
                    type='high',
                    strength=min(left_bars, right_bars)
                ))

            # Check swing low
            is_swing_low = True
            for j in range(1, left_bars + 1):
                if lows[i] >= lows[i - j]:
                    is_swing_low = False
                    break
            for j in range(1, right_bars + 1):
                if lows[i] >= lows[i + j]:
                    is_swing_low = False
                    break

            if is_swing_low:
                swing_lows.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[i]['time'],
                    price=lows[i],
                    type='low',
                    strength=min(left_bars, right_bars)
                ))

        return swing_highs, swing_lows

    @staticmethod
    def calculate_enhanced_fibonacci(
        swing_high: float,
        swing_low: float,
        swing_high_idx: int,
        swing_low_idx: int,
        direction: str = 'retracement'
    ) -> FibonacciLevels:
        """
        Calculate enhanced Fibonacci levels with Golden Zones and OTE

        Args:
            swing_high: Swing high price
            swing_low: Swing low price
            swing_high_idx: Index of swing high
            swing_low_idx: Index of swing low
            direction: 'retracement' or 'extension'

        Returns:
            FibonacciLevels object
        """
        diff = swing_high - swing_low

        if direction == 'retracement':
            # Retracement levels (from swing_low upward)
            return FibonacciLevels(
                swing_high=swing_high,
                swing_low=swing_low,
                swing_high_idx=swing_high_idx,
                swing_low_idx=swing_low_idx,
                direction=direction,
                # Standard levels
                level_0=swing_low,
                level_236=swing_low + diff * 0.236,
                level_382=swing_low + diff * 0.382,
                level_500=swing_low + diff * 0.500,
                level_618=swing_low + diff * 0.618,
                level_786=swing_low + diff * 0.786,
                level_1000=swing_high,
                # Golden Zones
                golden_zone_low=swing_low + diff * 0.618,
                golden_zone_high=swing_low + diff * 0.66,
                golden_zone_382_low=swing_low + diff * 0.34,
                golden_zone_382_high=swing_low + diff * 0.382,
                # OTE levels
                ote_high=swing_low + diff * 0.705,
                ote_low=swing_low + diff * 0.295
            )
        else:
            # Extension levels (beyond swing_high)
            return FibonacciLevels(
                swing_high=swing_high,
                swing_low=swing_low,
                swing_high_idx=swing_high_idx,
                swing_low_idx=swing_low_idx,
                direction=direction,
                # Standard extension levels
                level_0=swing_high,
                level_236=swing_high + diff * 0.236,
                level_382=swing_high + diff * 0.382,
                level_500=swing_high + diff * 0.500,
                level_618=swing_high + diff * 0.618,
                level_786=swing_high + diff * 0.786,
                level_1000=swing_high + diff * 1.000,
                # Extended zones
                golden_zone_low=swing_high + diff * 0.618,
                golden_zone_high=swing_high + diff * 0.66,
                golden_zone_382_low=swing_high + diff * 0.34,
                golden_zone_382_high=swing_high + diff * 0.382,
                ote_high=swing_high + diff * 0.705,
                ote_low=swing_high + diff * 0.295
            )

    @staticmethod
    def detect_harmonic_patterns(
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        tolerance: float = 0.05
    ) -> List[HarmonicPattern]:
        """
        Detect harmonic patterns (Gartley, Bat, Butterfly, Crab, Shark)

        Harmonic ratios:
        - Gartley: XA=0.618, AB=0.618, BC=0.382-0.886, CD=1.272-1.618
        - Bat: XA=0.382-0.500, AB=0.382-0.500, BC=0.382-0.886, CD=1.618-2.618
        - Butterfly: XA=0.786, AB=0.786, BC=0.382-0.886, CD=1.618-2.618
        - Crab: XA=0.382-0.618, AB=0.382-0.618, BC=0.382-0.886, CD=2.618-3.618
        - Shark: XA=0.886-1.13, AB=1.13-1.618, BC=1.618-2.24, CD=0.886-1.13
        """
        patterns = []

        # Combine and sort all swing points
        all_swings = []
        for sh in swing_highs:
            all_swings.append((sh.index, sh.price, 'high'))
        for sl in swing_lows:
            all_swings.append((sl.index, sl.price, 'low'))

        all_swings.sort(key=lambda x: x[0])

        # Look for 5-point patterns (X, A, B, C, D)
        for i in range(len(all_swings) - 4):
            X = all_swings[i]
            A = all_swings[i + 1]
            B = all_swings[i + 2]
            C = all_swings[i + 3]
            D = all_swings[i + 4]

            # Must alternate (high-low-high-low-high or low-high-low-high-low)
            types = [X[2], A[2], B[2], C[2], D[2]]
            if types != ['high', 'low', 'high', 'low', 'high'] and types != ['low', 'high', 'low', 'high', 'low']:
                continue

            # Calculate ratios
            XA = abs(A[1] - X[1])
            AB = abs(B[1] - A[1])
            BC = abs(C[1] - B[1])
            CD = abs(D[1] - C[1])

            if XA == 0:
                continue

            AB_XA = AB / XA
            BC_AB = BC / AB if AB != 0 else 0
            CD_BC = CD / BC if BC != 0 else 0
            CD_XA = CD / XA

            # Check for Gartley
            if (0.618 - tolerance < AB_XA < 0.618 + tolerance and
                    0.382 < BC_AB < 0.886 and
                    1.272 < CD_XA < 1.618):
                patterns.append(HarmonicPattern(
                    name='Gartley',
                    type='bullish' if types[0] == 'low' else 'bearish',
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    confidence=0.8,
                    target=D[1] + (D[1] - X[1]) * 0.618 if types[0] == 'low' else D[1] - (X[1] - D[1]) * 0.618,
                    stop_loss=X[1]
                ))

            # Check for Bat
            elif (0.382 < AB_XA < 0.500 and
                  0.382 < BC_AB < 0.886 and
                  1.618 < CD_XA < 2.618):
                patterns.append(HarmonicPattern(
                    name='Bat',
                    type='bullish' if types[0] == 'low' else 'bearish',
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    confidence=0.75,
                    target=D[1] + (D[1] - X[1]) * 0.886 if types[0] == 'low' else D[1] - (X[1] - D[1]) * 0.886,
                    stop_loss=X[1]
                ))

            # Check for Butterfly
            elif (0.786 - tolerance < AB_XA < 0.786 + tolerance and
                  0.382 < BC_AB < 0.886 and
                  1.618 < CD_XA < 2.618):
                patterns.append(HarmonicPattern(
                    name='Butterfly',
                    type='bullish' if types[0] == 'low' else 'bearish',
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    confidence=0.85,
                    target=D[1] + (D[1] - X[1]) * 1.618 if types[0] == 'low' else D[1] - (X[1] - D[1]) * 1.618,
                    stop_loss=X[1]
                ))

            # Check for Crab
            elif (0.382 < AB_XA < 0.618 and
                  0.382 < BC_AB < 0.886 and
                  2.618 < CD_XA < 3.618):
                patterns.append(HarmonicPattern(
                    name='Crab',
                    type='bullish' if types[0] == 'low' else 'bearish',
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    confidence=0.9,
                    target=D[1] + (D[1] - X[1]) * 1.618 if types[0] == 'low' else D[1] - (X[1] - D[1]) * 1.618,
                    stop_loss=X[1]
                ))

        return patterns

    @staticmethod
    def detect_divergences(
        df: pd.DataFrame,
        indicator_col: str = 'rsi_14',
        lookback: int = 14
    ) -> List[Divergence]:
        """
        Detect price-indicator divergences

        Args:
            df: DataFrame with price and indicator
            indicator_col: Indicator column name
            lookback: Lookback period for divergence detection

        Returns:
            List of divergences
        """
        divergences = []

        if indicator_col not in df.columns:
            return divergences

        prices = df['close'].values
        indicator = df[indicator_col].values

        # Find swing points in price
        price_highs = []
        price_lows = []

        for i in range(lookback, len(df) - lookback):
            # Swing high
            if all(prices[i] >= prices[i - j] for j in range(1, lookback + 1)) and \
                    all(prices[i] >= prices[i + j] for j in range(1, lookback + 1)):
                price_highs.append(i)

            # Swing low
            if all(prices[i] <= prices[i - j] for j in range(1, lookback + 1)) and \
                    all(prices[i] <= prices[i + j] for j in range(1, lookback + 1)):
                price_lows.append(i)

        # Check for divergences
        # Bullish divergence: price makes lower low, indicator makes higher low
        for i in range(len(price_lows) - 1):
            idx1, idx2 = price_lows[i], price_lows[i + 1]

            if prices[idx2] < prices[idx1] and indicator[idx2] > indicator[idx1]:
                divergences.append(Divergence(
                    type='bullish',
                    indicator=indicator_col,
                    strength='regular',
                    start_index=idx1,
                    end_index=idx2,
                    confidence=0.7
                ))

        # Bearish divergence: price makes higher high, indicator makes lower high
        for i in range(len(price_highs) - 1):
            idx1, idx2 = price_highs[i], price_highs[i + 1]

            if prices[idx2] > prices[idx1] and indicator[idx2] < indicator[idx1]:
                divergences.append(Divergence(
                    type='bearish',
                    indicator=indicator_col,
                    strength='regular',
                    start_index=idx1,
                    end_index=idx2,
                    confidence=0.7
                ))

        return divergences

    @staticmethod
    def detect_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
        min_touches: int = 2,
        tolerance_pct: float = 0.005
    ) -> List[SupportResistance]:
        """
        Detect horizontal support and resistance levels

        Args:
            df: DataFrame with OHLC
            window: Rolling window for local extrema
            min_touches: Minimum touches to confirm level
            tolerance_pct: Price tolerance (0.5% default)

        Returns:
            List of S/R levels
        """
        levels = []

        highs = df['high'].values
        lows = df['low'].values

        # Find local maxima and minima
        local_maxima = []
        local_minima = []

        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                local_maxima.append((i, highs[i]))

            if lows[i] == min(lows[i - window:i + window + 1]):
                local_minima.append((i, lows[i]))

        # Cluster levels (resistance from maxima)
        for i, (idx, price) in enumerate(local_maxima):
            # Find nearby levels
            cluster = [local_maxima[i]]

            for j, (idx2, price2) in enumerate(local_maxima):
                if i != j and abs(price - price2) / price < tolerance_pct:
                    cluster.append(local_maxima[j])

            if len(cluster) >= min_touches:
                avg_price = np.mean([p for _, p in cluster])
                price_range = (min([p for _, p in cluster]), max([p for _, p in cluster]))

                levels.append(SupportResistance(
                    level=avg_price,
                    type='resistance',
                    strength=len(cluster),
                    first_touch=min([idx for idx, _ in cluster]),
                    last_touch=max([idx for idx, _ in cluster]),
                    zone_range=price_range
                ))

        # Cluster levels (support from minima)
        for i, (idx, price) in enumerate(local_minima):
            cluster = [local_minima[i]]

            for j, (idx2, price2) in enumerate(local_minima):
                if i != j and abs(price - price2) / price < tolerance_pct:
                    cluster.append(local_minima[j])

            if len(cluster) >= min_touches:
                avg_price = np.mean([p for _, p in cluster])
                price_range = (min([p for _, p in cluster]), max([p for _, p in cluster]))

                levels.append(SupportResistance(
                    level=avg_price,
                    type='support',
                    strength=len(cluster),
                    first_touch=min([idx for idx, _ in cluster]),
                    last_touch=max([idx for idx, _ in cluster]),
                    zone_range=price_range
                ))

        # Remove duplicates
        unique_levels = []
        for level in levels:
            is_duplicate = False
            for ul in unique_levels:
                if abs(level.level - ul.level) / level.level < tolerance_pct:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_levels.append(level)

        return unique_levels

    @staticmethod
    def detect_trend_lines(
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        min_points: int = 3
    ) -> List[TrendLine]:
        """
        Detect trend lines from swing points

        Args:
            swing_highs: List of swing high points
            swing_lows: List of swing low points
            min_points: Minimum points for valid trend line

        Returns:
            List of trend lines
        """
        from scipy import stats

        trend_lines = []

        # Uptrend lines (connect swing lows)
        if len(swing_lows) >= min_points:
            for i in range(len(swing_lows) - min_points + 1):
                # Try different combinations
                points = swing_lows[i:i + min_points]
                x = np.array([p.index for p in points])
                y = np.array([p.price for p in points])

                # Linear regression
                slope, intercept, r_value, _, _ = stats.linregress(x, y)

                if r_value ** 2 > 0.9 and slope > 0:  # Good fit and upward
                    trend_lines.append(TrendLine(
                        type='uptrend',
                        points=[(p.index, p.price) for p in points],
                        slope=slope,
                        intercept=intercept,
                        r_squared=r_value ** 2,
                        breaks=0
                    ))

        # Downtrend lines (connect swing highs)
        if len(swing_highs) >= min_points:
            for i in range(len(swing_highs) - min_points + 1):
                points = swing_highs[i:i + min_points]
                x = np.array([p.index for p in points])
                y = np.array([p.price for p in points])

                slope, intercept, r_value, _, _ = stats.linregress(x, y)

                if r_value ** 2 > 0.9 and slope < 0:  # Good fit and downward
                    trend_lines.append(TrendLine(
                        type='downtrend',
                        points=[(p.index, p.price) for p in points],
                        slope=slope,
                        intercept=intercept,
                        r_squared=r_value ** 2,
                        breaks=0
                    ))

        return trend_lines
