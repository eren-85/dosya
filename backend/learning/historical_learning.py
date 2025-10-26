"""
Historical Data Learning System
Scans all-time historical data and learns from patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio


class HistoricalDataLearner:
    """
    Learn from historical data
    - Scan all-time candles
    - Detect patterns automatically
    - Build pattern library
    - Learn correlations
    """

    def __init__(
        self,
        data_aggregator,
        memory_manager,
        pattern_library_path: str = "./data/pattern_library.json"
    ):
        self.data_aggregator = data_aggregator
        self.memory_manager = memory_manager
        self.pattern_library_path = Path(pattern_library_path)

        self.pattern_library = {
            'harmonic_patterns': [],
            'candlestick_patterns': [],
            'swing_points': [],
            'support_resistance': [],
            'divergences': [],
            'statistics': {}
        }

    async def scan_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: Optional[str] = None,
        batch_size: int = 1000
    ):
        """
        Scan historical data and extract patterns

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (default: now)
            batch_size: Candles per batch
        """
        from ..data.processors.advanced_analysis import AdvancedTechnicalAnalysis
        from ..data.processors.technical_indicators import TechnicalIndicators

        print(f"🔍 Scanning historical data for {symbol} ({timeframe})")
        print(f"   Period: {start_date} to {end_date or 'now'}")

        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date) if end_date else datetime.now()

        total_patterns_found = 0
        current_date = start

        while current_date < end:
            batch_end = min(current_date + timedelta(days=batch_size), end)

            try:
                # Fetch data
                print(f"   Fetching {current_date.date()} to {batch_end.date()}...")

                df = await self.data_aggregator.fetch_ohlcv_aggregated(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=batch_size,
                    since=current_date
                )

                if df.empty:
                    print(f"   ⚠️  No data available for this period, skipping...")
                    current_date = batch_end
                    continue

                # Add indicators
                df = TechnicalIndicators.add_all_indicators(df)

                # Detect patterns
                swing_highs, swing_lows = AdvancedTechnicalAnalysis.detect_swing_points(df, left_bars=5, right_bars=5)
                harmonic_patterns = AdvancedTechnicalAnalysis.detect_harmonic_patterns(swing_highs, swing_lows)
                divergences = AdvancedTechnicalAnalysis.detect_divergences(df)
                sr_levels = AdvancedTechnicalAnalysis.detect_support_resistance(df)

                # Store patterns
                for pattern in harmonic_patterns:
                    self.pattern_library['harmonic_patterns'].append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'pattern': pattern.name,
                        'type': pattern.type,
                        'confidence': pattern.confidence,
                        'points': pattern.points,
                        'timestamp': df.index[pattern.indices['D']].isoformat() if hasattr(df.index, 'isoformat') else str(df.iloc[pattern.indices['D']]['time'])
                    })

                for div in divergences:
                    self.pattern_library['divergences'].append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'type': div.type,
                        'indicator': div.indicator,
                        'strength': div.strength,
                        'timestamp': df.index[div.end_index].isoformat() if hasattr(df.index, 'isoformat') else str(df.iloc[div.end_index]['time'])
                    })

                for sr in sr_levels:
                    self.pattern_library['support_resistance'].append({
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'type': sr.type,
                        'level': sr.level,
                        'strength': sr.strength,
                        'touches': sr.strength
                    })

                batch_patterns = len(harmonic_patterns) + len(divergences) + len(sr_levels)
                total_patterns_found += batch_patterns

                print(f"   ✅ Found {batch_patterns} patterns in this batch")

            except Exception as e:
                print(f"   ❌ Error processing batch: {e}")
                print(f"   ⏭️  Continuing to next batch...")

            current_date = batch_end

        # Save pattern library
        self._save_pattern_library()

        print(f"\n🎯 Historical scan complete!")
        print(f"   Total patterns found: {total_patterns_found}")
        print(f"   - Harmonic: {len(self.pattern_library['harmonic_patterns'])}")
        print(f"   - Divergences: {len(self.pattern_library['divergences'])}")
        print(f"   - S/R Levels: {len(self.pattern_library['support_resistance'])}")

    async def learn_from_onchain_correlation(
        self,
        symbol: str,
        timeframe: str,
        lookback_days: int = 365
    ):
        """
        Learn correlations between price action and on-chain metrics

        Args:
            symbol: Trading symbol
            timeframe: Timeframe
            lookback_days: Lookback period
        """
        print(f"🧠 Learning on-chain correlations for {symbol}")

        end = datetime.now()
        start = end - timedelta(days=lookback_days)

        try:
            # Fetch price data
            df_price = await self.data_aggregator.fetch_ohlcv_aggregated(
                symbol=symbol,
                timeframe=timeframe,
                limit=lookback_days * 24,  # Assuming hourly
                since=start
            )

            # Fetch on-chain data
            glassnode = self.data_aggregator.sources.get('glassnode')
            if not glassnode:
                print("   ⚠️  Glassnode source not available, skipping on-chain learning")
                return

            # Get multiple metrics
            metrics_to_fetch = [
                'exchange_netflow',
                'active_addresses',
                'mvrv_ratio',
                'nupl'
            ]

            onchain_data = await glassnode.fetch_multiple_metrics(
                metrics=metrics_to_fetch,
                symbol=symbol[:3],  # BTC from BTCUSDT
                resolution=timeframe,
                lookback_hours=lookback_days * 24
            )

            # Calculate correlations
            correlations = {}

            for metric_name, metric_data in onchain_data.items():
                if not metric_data:
                    print(f"   ⚠️  No data for {metric_name}, skipping...")
                    continue

                # Convert to DataFrame
                df_metric = pd.DataFrame([
                    {
                        'timestamp': m.timestamp,
                        'value': m.value
                    }
                    for m in metric_data
                ])

                if df_metric.empty:
                    continue

                # Align timestamps
                df_metric = df_metric.set_index('timestamp')
                df_price_indexed = df_price.set_index('time' if 'time' in df_price.columns else df_price.index)

                # Merge
                merged = pd.merge(
                    df_price_indexed[['close']],
                    df_metric,
                    left_index=True,
                    right_index=True,
                    how='inner'
                )

                if len(merged) < 10:
                    continue

                # Calculate correlation
                corr = merged['close'].corr(merged['value'])
                correlations[metric_name] = corr

                print(f"   📊 {metric_name}: correlation = {corr:.3f}")

            # Store correlations
            self.pattern_library['statistics']['onchain_correlations'] = correlations
            self._save_pattern_library()

            print(f"✅ On-chain correlation learning complete")

        except Exception as e:
            print(f"❌ Error learning on-chain correlations: {e}")
            print(f"⏭️  Continuing...")

    def get_pattern_statistics(self) -> Dict:
        """Get statistics from pattern library"""
        return {
            'total_harmonic_patterns': len(self.pattern_library['harmonic_patterns']),
            'total_divergences': len(self.pattern_library['divergences']),
            'total_sr_levels': len(self.pattern_library['support_resistance']),
            'pattern_success_rates': self._calculate_pattern_success_rates(),
            'onchain_correlations': self.pattern_library['statistics'].get('onchain_correlations', {})
        }

    def _calculate_pattern_success_rates(self) -> Dict:
        """Calculate success rates for different patterns"""
        # TODO: Implement success rate calculation
        # Requires forward-looking price data to check if pattern target was hit
        return {
            'gartley': 0.0,
            'bat': 0.0,
            'butterfly': 0.0,
            'crab': 0.0
        }

    def _save_pattern_library(self):
        """Save pattern library to disk"""
        import json

        with open(self.pattern_library_path, 'w') as f:
            json.dump(self.pattern_library, f, indent=2)

        print(f"💾 Pattern library saved to {self.pattern_library_path}")

    def _load_pattern_library(self):
        """Load pattern library from disk"""
        import json

        if self.pattern_library_path.exists():
            with open(self.pattern_library_path, 'r') as f:
                self.pattern_library = json.load(f)

            print(f"📂 Pattern library loaded")
