"""
Advanced Technical Analysis Module - Professional ICT/Smart Money Concepts
Converted from Pine Script indicators

Features:
- Multi-indicator Divergences (MACD, RSI, Stochastic, CCI, Momentum, OBV, etc.)
- Order Blocks (Institutional footprints)
- Fair Value Gaps (FVG/Imbalance)
- Change of Character (ChoCh) patterns
- Harmonic Patterns with ZigZag (Gartley, Bat, Butterfly, Crab, Shark, Cypher, etc.)
- Kill Zones for Crypto (Asia, London, New York sessions)
- Enhanced Fibonacci (Golden Zones, OTE levels)
- Swing High/Low Detection
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, time
from scipy import stats


@dataclass
class SwingPoint:
    """Swing high or low point"""
    index: int
    timestamp: datetime
    price: float
    type: str  # 'high' or 'low'
    strength: int  # How many bars on each side


@dataclass
class Divergence:
    """Price-indicator divergence (Pine Script algorithm)"""
    type: str  # 'bullish_regular', 'bearish_regular', 'bullish_hidden', 'bearish_hidden'
    indicators: List[str]  # Which indicators show divergence
    start_index: int
    end_index: int
    start_price: float
    end_price: float
    start_indicator: float
    end_indicator: float
    strength: int  # Number of indicators confirming
    confidence: float


@dataclass
class OrderBlock:
    """Order Block (Institutional footprint)"""
    type: str  # 'bullish' or 'bearish'
    index: int
    timestamp: datetime
    high: float
    low: float
    open: float
    close: float
    zone_top: float  # Top of order block zone
    zone_bottom: float  # Bottom of order block zone
    mitigated: bool = False
    mitigation_index: Optional[int] = None


@dataclass
class FairValueGap:
    """Fair Value Gap (Imbalance/FVG)"""
    type: str  # 'bullish' or 'bearish'
    start_index: int
    end_index: int  # Always start_index + 2 (3 candles)
    gap_high: float
    gap_low: float
    gap_size: float
    adr_percentage: float  # Size as % of ADR
    mitigated: bool = False
    mitigation_index: Optional[int] = None


@dataclass
class ChoCh:
    """Change of Character pattern"""
    type: str  # 'bullish' or 'bearish'
    break_index: int
    break_price: float
    pivot_index: int
    pivot_price: float
    structure_break_index: int
    delta_volume: float  # Cumulative delta during formation


@dataclass
class HarmonicPattern:
    """Harmonic pattern with ZigZag detection"""
    name: str  # 'Gartley', 'Bat', 'Butterfly', 'Crab', 'Shark', 'Cypher', etc.
    type: str  # 'bullish' or 'bearish'
    points: Dict[str, float]  # X, A, B, C, D
    indices: Dict[str, int]
    ratios: Dict[str, float]  # XAB, ABC, BCD, XAD ratios
    confidence: float
    target_levels: List[float]
    stop_loss: float
    prz_high: float  # Potential Reversal Zone
    prz_low: float


@dataclass
class KillZone:
    """ICT Kill Zone definition"""
    name: str  # 'Asia', 'London Open', 'New York AM', etc.
    start_time: time  # UTC time
    end_time: time
    priority: int  # 1-5, higher = more important


@dataclass
class SupportResistance:
    """Support or resistance level"""
    level: float
    type: str  # 'support' or 'resistance'
    strength: int  # Number of touches
    first_touch: int
    last_touch: int
    zone_range: Tuple[float, float]


@dataclass
class TrendLine:
    """Trend line"""
    type: str  # 'uptrend' or 'downtrend'
    points: List[Tuple[int, float]]
    slope: float
    intercept: float
    r_squared: float
    breaks: int = 0


@dataclass
class FibonacciLevels:
    """Enhanced Fibonacci retracement levels"""
    swing_high: float
    swing_low: float
    swing_high_idx: int
    swing_low_idx: int
    direction: str  # 'retracement' or 'extension'

    # Standard levels
    level_0: float
    level_236: float
    level_382: float
    level_500: float
    level_618: float
    level_786: float
    level_1000: float

    # Enhanced levels (Golden Zones & OTE)
    golden_zone_618_low: float  # 0.618
    golden_zone_618_high: float  # 0.66
    golden_zone_382_low: float  # 0.34
    golden_zone_382_high: float  # 0.382
    ote_high: float  # 0.705
    ote_low: float  # 0.295


class AdvancedTechnicalAnalysis:
    """
    Advanced technical analysis with ICT/Smart Money concepts
    Converted from professional Pine Script indicators
    """

    # Kill Zones for Crypto (UTC times)
    KILL_ZONES = [
        KillZone("Asia Range", time(20, 0), time(0, 0), priority=2),
        KillZone("Midnight Open", time(0, 0), time(5, 0), priority=3),
        KillZone("London Open", time(3, 0), time(5, 0), priority=5),
        KillZone("New York AM", time(8, 30), time(11, 0), priority=5),
        KillZone("New York Lunch", time(12, 0), time(13, 0), priority=2),
        KillZone("Power Hour", time(15, 0), time(16, 0), priority=4),
    ]

    @staticmethod
    def get_current_kill_zone(timestamp: datetime) -> Optional[KillZone]:
        """Get active kill zone for given timestamp (UTC)"""
        current_time = timestamp.time()

        for kz in AdvancedTechnicalAnalysis.KILL_ZONES:
            if kz.start_time <= kz.end_time:
                if kz.start_time <= current_time < kz.end_time:
                    return kz
            else:  # Crosses midnight
                if current_time >= kz.start_time or current_time < kz.end_time:
                    return kz
        return None

    @staticmethod
    def detect_swing_points(
        df: pd.DataFrame,
        left_bars: int = 5,
        right_bars: int = 5
    ) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Detect swing highs and lows (pivothigh/pivotlow from Pine Script)

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
            # Pivot high
            is_pivot_high = True
            for j in range(1, left_bars + 1):
                if highs[i] < highs[i - j]:
                    is_pivot_high = False
                    break
            if is_pivot_high:
                for j in range(1, right_bars + 1):
                    if highs[i] < highs[i + j]:
                        is_pivot_high = False
                        break

            if is_pivot_high:
                swing_highs.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[i].get('timestamp'),
                    price=highs[i],
                    type='high',
                    strength=min(left_bars, right_bars)
                ))

            # Pivot low
            is_pivot_low = True
            for j in range(1, left_bars + 1):
                if lows[i] > lows[i - j]:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                for j in range(1, right_bars + 1):
                    if lows[i] > lows[i + j]:
                        is_pivot_low = False
                        break

            if is_pivot_low:
                swing_lows.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i] if isinstance(df.index, pd.DatetimeIndex) else df.iloc[i].get('timestamp'),
                    price=lows[i],
                    type='low',
                    strength=min(left_bars, right_bars)
                ))

        return swing_highs, swing_lows

    @staticmethod
    def detect_divergences(
        df: pd.DataFrame,
        prd: int = 5,
        source: str = 'Close',
        indicators: Dict[str, bool] = None,
        max_bars: int = 100,
        max_pivot_points: int = 10,
        error_percent: float = 0.0
    ) -> List[Divergence]:
        """
        Multi-indicator divergence detection (from Pine Script)

        Checks: MACD, MACD Histogram, RSI, Stochastic, CCI, Momentum, OBV

        Args:
            df: DataFrame with price and indicators
            prd: Pivot period
            source: 'Close' or 'High/Low' for pivot detection
            indicators: Dict of which indicators to check
            max_bars: Maximum bars to look back
            max_pivot_points: Max pivot points to check

        Returns:
            List of divergences
        """
        if indicators is None:
            indicators = {
                'macd': True,
                'macd_hist': True,
                'rsi': True,
                'stochastic': True,
                'cci': True,
                'momentum': True,
                'obv': True
            }

        divergences = []

        # Calculate indicators if not present
        if 'rsi_14' not in df.columns and indicators.get('rsi'):
            df['rsi_14'] = df['close'].rolling(14).apply(
                lambda x: 100 - (100 / (1 + (x[x > x.shift()].sum() / len(x)) /
                                        (x[x < x.shift()].sum() / len(x)))) if len(x) > 1 else 50
            )

        # Detect pivots
        pivot_source = df['close'] if source == 'Close' else None
        ph_indices = []
        pl_indices = []
        ph_vals = []
        pl_vals = []

        # Find pivot highs
        for i in range(prd, len(df) - prd):
            if source == 'Close':
                vals = df['close'].iloc[i-prd:i+prd+1].values
                if df['close'].iloc[i] == max(vals):
                    ph_indices.append(i)
                    ph_vals.append(df['close'].iloc[i])
            else:
                vals = df['high'].iloc[i-prd:i+prd+1].values
                if df['high'].iloc[i] == max(vals):
                    ph_indices.append(i)
                    ph_vals.append(df['high'].iloc[i])

        # Find pivot lows
        for i in range(prd, len(df) - prd):
            if source == 'Close':
                vals = df['close'].iloc[i-prd:i+prd+1].values
                if df['close'].iloc[i] == min(vals):
                    pl_indices.append(i)
                    pl_vals.append(df['close'].iloc[i])
            else:
                vals = df['low'].iloc[i-prd:i+prd+1].values
                if df['low'].iloc[i] == min(vals):
                    pl_indices.append(i)
                    pl_vals.append(df['low'].iloc[i])

        # Check each indicator for divergence
        indicator_map = {
            'rsi': 'rsi_14',
            'macd': 'macd',
            'macd_hist': 'macd_hist',
        }

        for ind_name, ind_col in indicator_map.items():
            if not indicators.get(ind_name, False) or ind_col not in df.columns:
                continue

            indicator_vals = df[ind_col].values

            # Bullish regular divergence (price lower low, indicator higher low)
            for i in range(len(pl_indices) - 1):
                for j in range(i + 1, min(i + max_pivot_points, len(pl_indices))):
                    idx1, idx2 = pl_indices[i], pl_indices[j]

                    if idx2 - idx1 > max_bars:
                        continue

                    price1, price2 = pl_vals[i], pl_vals[j]
                    ind1, ind2 = indicator_vals[idx1], indicator_vals[idx2]

                    # Check for bullish divergence
                    if price2 < price1 and ind2 > ind1:
                        divergences.append(Divergence(
                            type='bullish_regular',
                            indicators=[ind_name],
                            start_index=idx1,
                            end_index=idx2,
                            start_price=price1,
                            end_price=price2,
                            start_indicator=ind1,
                            end_indicator=ind2,
                            strength=1,
                            confidence=0.75
                        ))

            # Bearish regular divergence (price higher high, indicator lower high)
            for i in range(len(ph_indices) - 1):
                for j in range(i + 1, min(i + max_pivot_points, len(ph_indices))):
                    idx1, idx2 = ph_indices[i], ph_indices[j]

                    if idx2 - idx1 > max_bars:
                        continue

                    price1, price2 = ph_vals[i], ph_vals[j]
                    ind1, ind2 = indicator_vals[idx1], indicator_vals[idx2]

                    # Check for bearish divergence
                    if price2 > price1 and ind2 < ind1:
                        divergences.append(Divergence(
                            type='bearish_regular',
                            indicators=[ind_name],
                            start_index=idx1,
                            end_index=idx2,
                            start_price=price1,
                            end_price=price2,
                            start_indicator=ind1,
                            end_indicator=ind2,
                            strength=1,
                            confidence=0.75
                        ))

        return divergences

    @staticmethod
    def detect_order_blocks(
        df: pd.DataFrame,
        periods: int = 5,
        threshold: float = 0.0,
        use_wicks: bool = False
    ) -> List[OrderBlock]:
        """
        Order Block detection (from Pine Script)

        Bullish OB: Last down candle before sequence of up candles
        Bearish OB: Last up candle before sequence of down candles

        Args:
            df: DataFrame with OHLCV
            periods: Required number of sequential candles
            threshold: Min % move to identify OB
            use_wicks: Use High/Low range instead of Open/Close

        Returns:
            List of Order Blocks
        """
        order_blocks = []

        opens = df['open'].values
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values

        ob_period = periods + 1

        for i in range(ob_period, len(df)):
            # Check if we have enough candles
            if i < ob_period:
                continue

            # Calculate absolute % move
            absmove = abs(closes[i - ob_period] - closes[i - 1]) / closes[i - ob_period] * 100
            relmove = absmove >= threshold

            # Bullish Order Block
            bullish_ob = closes[i - ob_period] < opens[i - ob_period]  # Red candle

            if bullish_ob:
                # Check if all subsequent candles are green
                upcandles = sum(1 for j in range(1, periods + 1) if closes[i - j] > opens[i - j])

                if upcandles == periods and relmove:
                    ob_high = opens[i - ob_period] if not use_wicks else highs[i - ob_period]
                    ob_low = lows[i - ob_period]

                    order_blocks.append(OrderBlock(
                        type='bullish',
                        index=i - ob_period,
                        timestamp=df.index[i - ob_period] if isinstance(df.index, pd.DatetimeIndex) else None,
                        high=highs[i - ob_period],
                        low=lows[i - ob_period],
                        open=opens[i - ob_period],
                        close=closes[i - ob_period],
                        zone_top=ob_high,
                        zone_bottom=ob_low,
                        mitigated=False
                    ))

            # Bearish Order Block
            bearish_ob = closes[i - ob_period] > opens[i - ob_period]  # Green candle

            if bearish_ob:
                # Check if all subsequent candles are red
                downcandles = sum(1 for j in range(1, periods + 1) if closes[i - j] < opens[i - j])

                if downcandles == periods and relmove:
                    ob_high = highs[i - ob_period]
                    ob_low = opens[i - ob_period] if not use_wicks else lows[i - ob_period]

                    order_blocks.append(OrderBlock(
                        type='bearish',
                        index=i - ob_period,
                        timestamp=df.index[i - ob_period] if isinstance(df.index, pd.DatetimeIndex) else None,
                        high=highs[i - ob_period],
                        low=lows[i - ob_period],
                        open=opens[i - ob_period],
                        close=closes[i - ob_period],
                        zone_top=ob_high,
                        zone_bottom=ob_low,
                        mitigated=False
                    ))

        return order_blocks

    @staticmethod
    def detect_fair_value_gaps(
        df: pd.DataFrame,
        adr: float = None,
        min_adr_percent: float = 0.5
    ) -> List[FairValueGap]:
        """
        Fair Value Gap / Imbalance detection (from Pine Script)

        3-candle pattern where there's a gap between candle[2] and candle[0]

        Args:
            df: DataFrame with OHLC
            adr: Average Daily Range (for filtering)
            min_adr_percent: Minimum gap size as % of ADR

        Returns:
            List of FVGs
        """
        fvgs = []

        opens = df['open'].values
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values

        for i in range(2, len(df)):
            # Bullish FVG: low[0] > high[2] (gap up)
            # Sequence: down/doji, down/doji, up OR down/doji, up, up OR up, up, up
            up = [opens[i-j] < closes[i-j] for j in range(3)]
            down = [opens[i-j] > closes[i-j] for j in range(3)]
            doji = [opens[i-j] == closes[i-j] for j in range(3)]

            # Bullish imbalance patterns
            bullish_patterns = [
                (down[2] or doji[2]) and (down[1] or doji[1]) and up[0],
                (down[2] or doji[2]) and up[1] and up[0],
                up[2] and up[1] and up[0]
            ]

            if any(bullish_patterns):
                gap_bottom = lows[i]  # Low of current candle
                gap_top = highs[i - 2]  # High of 2 candles ago
                gap_size = gap_bottom - gap_top

                if gap_size > 0:
                    adr_pct = (gap_size / adr * 100) if adr else 0

                    if adr is None or adr_pct >= min_adr_percent:
                        fvgs.append(FairValueGap(
                            type='bullish',
                            start_index=i - 2,
                            end_index=i,
                            gap_high=gap_bottom,
                            gap_low=gap_top,
                            gap_size=gap_size,
                            adr_percentage=adr_pct,
                            mitigated=False
                        ))

            # Bearish FVG: high[0] < low[2] (gap down)
            bearish_patterns = [
                up[2] and up[1] and (down[0] or doji[0]),
                up[2] and down[1] and (down[0] or doji[0]),
                down[2] and down[1] and down[0]
            ]

            if any(bearish_patterns):
                gap_top = highs[i]  # High of current candle
                gap_bottom = lows[i - 2]  # Low of 2 candles ago
                gap_size = gap_bottom - gap_top

                if gap_size > 0:
                    adr_pct = (gap_size / adr * 100) if adr else 0

                    if adr is None or adr_pct >= min_adr_percent:
                        fvgs.append(FairValueGap(
                            type='bearish',
                            start_index=i - 2,
                            end_index=i,
                            gap_high=gap_bottom,
                            gap_low=gap_top,
                            gap_size=gap_size,
                            adr_percentage=adr_pct,
                            mitigated=False
                        ))

        return fvgs

    @staticmethod
    def detect_choch_patterns(
        df: pd.DataFrame,
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        volume_col: str = 'volume'
    ) -> List[ChoCh]:
        """
        Change of Character pattern detection (from Pine Script)

        Identifies market structure breaks with delta volume

        Args:
            df: DataFrame with OHLCV
            swing_highs: List of swing high points
            swing_lows: List of swing low points
            volume_col: Volume column name

        Returns:
            List of ChoCh patterns
        """
        choch_patterns = []

        closes = df['close'].values
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        volumes = df[volume_col].values if volume_col in df.columns else None

        # Combine swings into chronological order
        all_swings = []
        for sh in swing_highs:
            all_swings.append((sh.index, sh.price, 'high'))
        for sl in swing_lows:
            all_swings.append((sl.index, sl.price, 'low'))
        all_swings.sort()

        # Detect structure breaks
        for i in range(2, len(all_swings)):
            prev_swing = all_swings[i-1]
            curr_swing = all_swings[i]

            # Bullish ChoCh: Price breaks above previous high after downtrend
            if prev_swing[2] == 'high' and curr_swing[2] == 'high':
                if curr_swing[1] > prev_swing[1]:
                    # Calculate delta volume
                    delta = 0
                    if volumes is not None:
                        for j in range(prev_swing[0], curr_swing[0] + 1):
                            if j < len(closes):
                                delta += volumes[j] if closes[j] > opens[j] else -volumes[j]

                    choch_patterns.append(ChoCh(
                        type='bullish',
                        break_index=curr_swing[0],
                        break_price=curr_swing[1],
                        pivot_index=prev_swing[0],
                        pivot_price=prev_swing[1],
                        structure_break_index=curr_swing[0],
                        delta_volume=delta
                    ))

            # Bearish ChoCh: Price breaks below previous low after uptrend
            if prev_swing[2] == 'low' and curr_swing[2] == 'low':
                if curr_swing[1] < prev_swing[1]:
                    # Calculate delta volume
                    delta = 0
                    if volumes is not None:
                        for j in range(prev_swing[0], curr_swing[0] + 1):
                            if j < len(closes):
                                delta += volumes[j] if closes[j] > opens[j] else -volumes[j]

                    choch_patterns.append(ChoCh(
                        type='bearish',
                        break_index=curr_swing[0],
                        break_price=curr_swing[1],
                        pivot_index=prev_swing[0],
                        pivot_price=prev_swing[1],
                        structure_break_index=curr_swing[0],
                        delta_volume=delta
                    ))

        return choch_patterns

    @staticmethod
    def detect_harmonic_patterns(
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        error_percent: int = 10
    ) -> List[HarmonicPattern]:
        """
        Advanced Harmonic Pattern detection with proper ratios
        Based on comprehensive harmonic pattern ratios

        Patterns: Gartley, Bat, Butterfly, Crab, Deep Crab, Shark, Cypher,
                  NenStar, 5-0, Three Drives, AB=CD, etc.

        Args:
            swing_highs: List of swing highs
            swing_lows: List of swing lows
            error_percent: Error tolerance (10% default)

        Returns:
            List of harmonic patterns
        """
        patterns = []

        err_min = (100 - error_percent) / 100
        err_max = (100 + error_percent) / 100

        # Combine swings
        all_swings = []
        for sh in swing_highs:
            all_swings.append((sh.index, sh.price, 'high', sh.timestamp))
        for sl in swing_lows:
            all_swings.append((sl.index, sl.price, 'low', sl.timestamp))
        all_swings.sort()

        # Need at least 5 points (X, A, B, C, D)
        for i in range(len(all_swings) - 4):
            X = all_swings[i]
            A = all_swings[i + 1]
            B = all_swings[i + 2]
            C = all_swings[i + 3]
            D = all_swings[i + 4]

            # Must alternate
            types = [X[2], A[2], B[2], C[2], D[2]]
            if types not in [['high', 'low', 'high', 'low', 'high'],
                             ['low', 'high', 'low', 'high', 'low']]:
                continue

            # Calculate legs
            XA = abs(A[1] - X[1])
            AB = abs(B[1] - A[1])
            BC = abs(C[1] - B[1])
            CD = abs(D[1] - C[1])

            if XA == 0 or AB == 0 or BC == 0:
                continue

            # Calculate ratios
            AB_XA = AB / XA
            BC_AB = BC / AB
            CD_BC = CD / BC
            XAD = abs(D[1] - A[1]) / XA

            pattern_type = 'bullish' if types[0] == 'low' else 'bearish'

            # Gartley: XAB=0.618, ABC=0.382-0.886, XAD=0.786
            if (0.618 * err_min <= AB_XA <= 0.618 * err_max and
                0.382 <= BC_AB <= 0.886 and
                0.786 * err_min <= XAD <= 0.786 * err_max):

                patterns.append(HarmonicPattern(
                    name='Gartley',
                    type=pattern_type,
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    ratios={'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC, 'XAD': XAD},
                    confidence=0.85,
                    target_levels=[D[1] + (C[1] - D[1]) * 0.382,
                                   D[1] + (C[1] - D[1]) * 0.618],
                    stop_loss=X[1],
                    prz_high=max(D[1], X[1]),
                    prz_low=min(D[1], X[1])
                ))

            # Bat: XAB=0.382-0.5, ABC=0.382-0.886, XAD=0.886
            elif (0.382 <= AB_XA <= 0.5 and
                  0.382 <= BC_AB <= 0.886 and
                  0.886 * err_min <= XAD <= 0.886 * err_max):

                patterns.append(HarmonicPattern(
                    name='Bat',
                    type=pattern_type,
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    ratios={'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC, 'XAD': XAD},
                    confidence=0.8,
                    target_levels=[D[1] + (C[1] - D[1]) * 0.382,
                                   D[1] + (C[1] - D[1]) * 0.618],
                    stop_loss=X[1],
                    prz_high=max(D[1], X[1]),
                    prz_low=min(D[1], X[1])
                ))

            # Butterfly: XAB=0.786, ABC=0.382-0.886, XAD=1.27-1.618
            elif (0.786 * err_min <= AB_XA <= 0.786 * err_max and
                  0.382 <= BC_AB <= 0.886 and
                  1.27 <= XAD <= 1.618):

                patterns.append(HarmonicPattern(
                    name='Butterfly',
                    type=pattern_type,
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    ratios={'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC, 'XAD': XAD},
                    confidence=0.82,
                    target_levels=[D[1] + (A[1] - D[1]) * 0.382,
                                   D[1] + (A[1] - D[1]) * 0.618],
                    stop_loss=D[1] + (A[1] - D[1]) * 1.41,
                    prz_high=max(D[1], A[1]),
                    prz_low=min(D[1], A[1])
                ))

            # Crab: XAB=0.382-0.618, ABC=0.382-0.886, XAD=1.618
            elif (0.382 <= AB_XA <= 0.618 and
                  0.382 <= BC_AB <= 0.886 and
                  1.618 * err_min <= XAD <= 1.618 * err_max):

                patterns.append(HarmonicPattern(
                    name='Crab',
                    type=pattern_type,
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    ratios={'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC, 'XAD': XAD},
                    confidence=0.88,
                    target_levels=[D[1] + (A[1] - D[1]) * 0.382,
                                   D[1] + (A[1] - D[1]) * 0.618],
                    stop_loss=D[1] + (A[1] - D[1]) * 1.41,
                    prz_high=max(D[1], A[1]),
                    prz_low=min(D[1], A[1])
                ))

            # Shark: ABC=1.13-1.618, BCD=1.618-2.24, XAD=0.886-1.13
            elif (1.13 <= BC_AB <= 1.618 and
                  1.618 <= CD_BC <= 2.24 and
                  0.886 <= XAD <= 1.13):

                patterns.append(HarmonicPattern(
                    name='Shark',
                    type=pattern_type,
                    points={'X': X[1], 'A': A[1], 'B': B[1], 'C': C[1], 'D': D[1]},
                    indices={'X': X[0], 'A': A[0], 'B': B[0], 'C': C[0], 'D': D[0]},
                    ratios={'AB_XA': AB_XA, 'BC_AB': BC_AB, 'CD_BC': CD_BC, 'XAD': XAD},
                    confidence=0.78,
                    target_levels=[D[1] + (C[1] - D[1]) * 0.5,
                                   D[1] + (C[1] - D[1]) * 1.618],
                    stop_loss=D[1] + (C[1] - D[1]) * 2.0,
                    prz_high=max(D[1], C[1]),
                    prz_low=min(D[1], C[1])
                ))

        return patterns

    @staticmethod
    def calculate_enhanced_fibonacci(
        swing_high: float,
        swing_low: float,
        swing_high_idx: int,
        swing_low_idx: int,
        direction: str = 'retracement'
    ) -> FibonacciLevels:
        """
        Calculate enhanced Fibonacci with Golden Zones and OTE levels

        Golden Zone 618: 0.618 - 0.66
        Golden Zone 382: 0.34 - 0.382
        OTE High: 0.705
        OTE Low: 0.295
        """
        diff = swing_high - swing_low

        if direction == 'retracement':
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
                golden_zone_618_low=swing_low + diff * 0.618,
                golden_zone_618_high=swing_low + diff * 0.66,
                golden_zone_382_low=swing_low + diff * 0.34,
                golden_zone_382_high=swing_low + diff * 0.382,
                # OTE levels
                ote_high=swing_low + diff * 0.705,
                ote_low=swing_low + diff * 0.295
            )
        else:
            # Extension
            return FibonacciLevels(
                swing_high=swing_high,
                swing_low=swing_low,
                swing_high_idx=swing_high_idx,
                swing_low_idx=swing_low_idx,
                direction=direction,
                level_0=swing_high,
                level_236=swing_high + diff * 0.236,
                level_382=swing_high + diff * 0.382,
                level_500=swing_high + diff * 0.500,
                level_618=swing_high + diff * 0.618,
                level_786=swing_high + diff * 0.786,
                level_1000=swing_high + diff * 1.000,
                golden_zone_618_low=swing_high + diff * 0.618,
                golden_zone_618_high=swing_high + diff * 0.66,
                golden_zone_382_low=swing_high + diff * 0.34,
                golden_zone_382_high=swing_high + diff * 0.382,
                ote_high=swing_high + diff * 0.705,
                ote_low=swing_high + diff * 0.295
            )

    @staticmethod
    def detect_support_resistance(
        df: pd.DataFrame,
        window: int = 20,
        min_touches: int = 2,
        tolerance_pct: float = 0.005
    ) -> List[SupportResistance]:
        """Detect horizontal support and resistance levels"""
        levels = []

        highs = df['high'].values
        lows = df['low'].values

        # Find local extrema
        local_maxima = []
        local_minima = []

        for i in range(window, len(df) - window):
            if highs[i] == max(highs[i - window:i + window + 1]):
                local_maxima.append((i, highs[i]))
            if lows[i] == min(lows[i - window:i + window + 1]):
                local_minima.append((i, lows[i]))

        # Cluster resistance levels
        processed = set()
        for i, (idx, price) in enumerate(local_maxima):
            if i in processed:
                continue

            cluster = [(idx, price)]
            processed.add(i)

            for j, (idx2, price2) in enumerate(local_maxima):
                if j != i and j not in processed:
                    if abs(price - price2) / price < tolerance_pct:
                        cluster.append((idx2, price2))
                        processed.add(j)

            if len(cluster) >= min_touches:
                avg_price = np.mean([p for _, p in cluster])
                levels.append(SupportResistance(
                    level=avg_price,
                    type='resistance',
                    strength=len(cluster),
                    first_touch=min(idx for idx, _ in cluster),
                    last_touch=max(idx for idx, _ in cluster),
                    zone_range=(min(p for _, p in cluster), max(p for _, p in cluster))
                ))

        # Cluster support levels
        processed = set()
        for i, (idx, price) in enumerate(local_minima):
            if i in processed:
                continue

            cluster = [(idx, price)]
            processed.add(i)

            for j, (idx2, price2) in enumerate(local_minima):
                if j != i and j not in processed:
                    if abs(price - price2) / price < tolerance_pct:
                        cluster.append((idx2, price2))
                        processed.add(j)

            if len(cluster) >= min_touches:
                avg_price = np.mean([p for _, p in cluster])
                levels.append(SupportResistance(
                    level=avg_price,
                    type='support',
                    strength=len(cluster),
                    first_touch=min(idx for idx, _ in cluster),
                    last_touch=max(idx for idx, _ in cluster),
                    zone_range=(min(p for _, p in cluster), max(p for _, p in cluster))
                ))

        return levels

    @staticmethod
    def detect_trend_lines(
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        min_points: int = 3
    ) -> List[TrendLine]:
        """Detect trend lines from swing points"""
        trend_lines = []

        # Uptrend lines (connect swing lows)
        if len(swing_lows) >= min_points:
            for i in range(len(swing_lows) - min_points + 1):
                points = swing_lows[i:i + min_points]
                x = np.array([p.index for p in points])
                y = np.array([p.price for p in points])

                slope, intercept, r_value, _, _ = stats.linregress(x, y)

                if r_value ** 2 > 0.9 and slope > 0:
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

                if r_value ** 2 > 0.9 and slope < 0:
                    trend_lines.append(TrendLine(
                        type='downtrend',
                        points=[(p.index, p.price) for p in points],
                        slope=slope,
                        intercept=intercept,
                        r_squared=r_value ** 2,
                        breaks=0
                    ))

        return trend_lines
