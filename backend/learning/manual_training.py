"""
Manuel Training System
Allows users to manually annotate patterns, swing points, and train the system
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np


class ManualAnnotation:
    """
    Manual pattern and swing point annotation system
    """

    def __init__(self, annotations_dir: str = "./data/annotations"):
        self.annotations_dir = Path(annotations_dir)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)

        self.annotations = {
            'patterns': [],
            'swing_highs': [],
            'swing_lows': [],
            'support_resistance': [],
            'trend_lines': []
        }

        # Load existing annotations
        self._load_annotations()

    def annotate_pattern(
        self,
        symbol: str,
        timeframe: str,
        pattern_type: str,
        points: List[Dict],  # [{'index': int, 'price': float, 'timestamp': str}, ...]
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Annotate a chart pattern

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            pattern_type: Type of pattern (e.g., 'head_and_shoulders', 'double_top')
            points: List of points defining the pattern
            metadata: Additional metadata (volume, RSI, etc. at key points)

        Returns:
            Annotation ID
        """
        annotation_id = f"pattern_{datetime.now().timestamp()}"

        annotation = {
            'id': annotation_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'pattern_type': pattern_type,
            'points': points,
            'metadata': metadata or {},
            'annotated_at': datetime.now().isoformat(),
            'verified': False
        }

        self.annotations['patterns'].append(annotation)
        self._save_annotations()

        print(f"✅ Pattern annotated: {pattern_type} on {symbol} ({timeframe})")

        return annotation_id

    def annotate_swing_point(
        self,
        symbol: str,
        timeframe: str,
        swing_type: str,  # 'high' or 'low'
        index: int,
        price: float,
        timestamp: str,
        market_data: Optional[Dict] = None
    ) -> str:
        """
        Annotate a swing high or low point

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            swing_type: 'high' or 'low'
            index: Bar index
            price: Price at swing point
            timestamp: Timestamp
            market_data: Market data at this point (volume, RSI, OI, CVD, etc.)

        Returns:
            Annotation ID
        """
        annotation_id = f"swing_{swing_type}_{datetime.now().timestamp()}"

        annotation = {
            'id': annotation_id,
            'symbol': symbol,
            'timeframe': timeframe,
            'type': swing_type,
            'index': index,
            'price': price,
            'timestamp': timestamp,
            'market_data': market_data or {},
            'annotated_at': datetime.now().isoformat()
        }

        if swing_type == 'high':
            self.annotations['swing_highs'].append(annotation)
        else:
            self.annotations['swing_lows'].append(annotation)

        self._save_annotations()

        print(f"✅ Swing {swing_type} annotated at ${price:.2f}")

        return annotation_id

    def capture_market_context(
        self,
        df: pd.DataFrame,
        index: int,
        additional_data: Optional[Dict] = None
    ) -> Dict:
        """
        Capture full market context at a specific point

        Args:
            df: DataFrame with OHLCV and indicators
            index: Bar index
            additional_data: Additional data (OI, net longs/shorts, CVD, order book)

        Returns:
            Market context dictionary
        """
        if index >= len(df):
            return {}

        row = df.iloc[index]

        context = {
            'price': float(row.get('close', 0)),
            'volume': float(row.get('volume', 0)),
            'high': float(row.get('high', 0)),
            'low': float(row.get('low', 0)),

            # Technical indicators
            'rsi_14': float(row.get('rsi_14', 0)) if 'rsi_14' in df.columns else None,
            'macd': float(row.get('MACD_12_26_9', 0)) if 'MACD_12_26_9' in df.columns else None,
            'atr': float(row.get('atr', 0)) if 'atr' in df.columns else None,
            'bb_upper': float(row.get('BBU_20_2.0', 0)) if 'BBU_20_2.0' in df.columns else None,
            'bb_lower': float(row.get('BBL_20_2.0', 0)) if 'BBL_20_2.0' in df.columns else None,

            # Volume indicators
            'obv': float(row.get('obv', 0)) if 'obv' in df.columns else None,
            'vwap': float(row.get('vwap', 0)) if 'vwap' in df.columns else None,

            # Moving averages
            'sma_20': float(row.get('sma_20', 0)) if 'sma_20' in df.columns else None,
            'sma_50': float(row.get('sma_50', 0)) if 'sma_50' in df.columns else None,
            'ema_20': float(row.get('ema_20', 0)) if 'ema_20' in df.columns else None,

            # Time-based
            'hour': row.get('hour', 0) if 'hour' in df.columns else None,
            'day_of_week': row.get('day_of_week', 0) if 'day_of_week' in df.columns else None,
        }

        # Add additional on-chain/derivatives data
        if additional_data:
            context.update({
                'open_interest': additional_data.get('open_interest'),
                'funding_rate': additional_data.get('funding_rate'),
                'net_longs': additional_data.get('net_longs'),
                'net_shorts': additional_data.get('net_shorts'),
                'long_short_ratio': additional_data.get('long_short_ratio'),
                'cvd': additional_data.get('cvd'),
                'orderbook_imbalance': additional_data.get('orderbook_imbalance'),
                'liquidations_24h': additional_data.get('liquidations_24h'),
                'exchange_netflow': additional_data.get('exchange_netflow'),
                'whale_tx_count': additional_data.get('whale_tx_count'),
            })

        return context

    def get_annotations(
        self,
        annotation_type: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[Dict]:
        """
        Get annotations with optional filters

        Args:
            annotation_type: Type filter ('patterns', 'swing_highs', etc.)
            symbol: Symbol filter
            timeframe: Timeframe filter

        Returns:
            List of matching annotations
        """
        if annotation_type:
            results = self.annotations.get(annotation_type, [])
        else:
            # All annotations
            results = []
            for ann_list in self.annotations.values():
                results.extend(ann_list)

        # Apply filters
        if symbol:
            results = [a for a in results if a.get('symbol') == symbol]

        if timeframe:
            results = [a for a in results if a.get('timeframe') == timeframe]

        return results

    def export_training_dataset(self, output_path: str) -> int:
        """
        Export annotated data as training dataset

        Returns:
            Number of samples exported
        """
        dataset = {
            'patterns': self.annotations['patterns'],
            'swing_points': self.annotations['swing_highs'] + self.annotations['swing_lows'],
            'support_resistance': self.annotations['support_resistance'],
            'trend_lines': self.annotations['trend_lines'],
            'metadata': {
                'total_annotations': sum(len(v) for v in self.annotations.values()),
                'exported_at': datetime.now().isoformat()
            }
        }

        with open(output_path, 'w') as f:
            json.dump(dataset, f, indent=2)

        total = dataset['metadata']['total_annotations']
        print(f"✅ Exported {total} annotations to {output_path}")

        return total

    def _save_annotations(self):
        """Save annotations to disk"""
        filepath = self.annotations_dir / "annotations.json"

        with open(filepath, 'w') as f:
            json.dump(self.annotations, f, indent=2)

    def _load_annotations(self):
        """Load existing annotations"""
        filepath = self.annotations_dir / "annotations.json"

        if filepath.exists():
            with open(filepath, 'r') as f:
                self.annotations = json.load(f)

            total = sum(len(v) for v in self.annotations.values())
            print(f"✅ Loaded {total} existing annotations")


class ManualTrainingIntegration:
    """
    Integrate manual annotations with ML training
    """

    @staticmethod
    def prepare_pattern_training_data(
        annotations: List[Dict],
        feature_columns: List[str]
    ) -> tuple:
        """
        Prepare pattern annotations for supervised learning

        Args:
            annotations: List of pattern annotations
            feature_columns: Feature column names

        Returns:
            (X, y) training data
        """
        X = []
        y = []

        for annotation in annotations:
            # Extract features from metadata
            metadata = annotation.get('metadata', {})

            features = []
            for col in feature_columns:
                features.append(metadata.get(col, 0))

            # Label (pattern type)
            pattern_type = annotation.get('pattern_type', 'unknown')

            X.append(features)
            y.append(pattern_type)

        return np.array(X), np.array(y)

    @staticmethod
    def augment_swing_point_detection(
        annotations: List[Dict],
        auto_detected: List[Dict]
    ) -> List[Dict]:
        """
        Augment auto-detected swing points with manual annotations

        Args:
            annotations: Manual annotations
            auto_detected: Automatically detected swing points

        Returns:
            Combined and validated swing points
        """
        combined = auto_detected.copy()

        # Add manual annotations that are not already detected
        for manual in annotations:
            is_duplicate = False

            for auto in auto_detected:
                # Check if same point (within tolerance)
                if (abs(manual['index'] - auto['index']) <= 2 and
                        abs(manual['price'] - auto['price']) / manual['price'] < 0.001):
                    is_duplicate = True
                    break

            if not is_duplicate:
                combined.append(manual)

        print(f"✅ Combined {len(auto_detected)} auto + {len(annotations)} manual = {len(combined)} swing points")

        return combined
