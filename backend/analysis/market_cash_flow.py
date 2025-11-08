"""
Market Cash Flow Analyzer

Marketteki tüm coinlere olan nakit girişini analiz eder.
Alım-satım dengesini hesaplar ve raporlar.

Features:
- Farklı zaman dilimlerinde (15m, 1h, 4h, 12h, 1d) alım oranları
- Market geneli alım gücü hesaplama
- Coin bazlı nakit akış raporu
- Momentum skorları
- Risk değerlendirmesi
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketCashFlowAnalyzer:
    """
    Market-wide cash flow analyzer

    Calculates:
    - Buyer percentage across different timeframes (15m, 1h, 4h, 12h, 1d)
    - Cash flow distribution by coin
    - Momentum scores
    - Risk assessment
    """

    def __init__(self, data_dir: str = "data"):
        """
        Initialize the analyzer

        Args:
            data_dir: Directory containing parquet files
        """
        self.data_dir = Path(data_dir)
        self.timeframes_map = {
            '15m': '15min',
            '1h': '1H',
            '4h': '4H',
            '12h': '12H',
            '1d': '1D'
        }

    def analyze_market(
        self,
        symbols: Optional[List[str]] = None,
        base_timeframe: str = '15min',
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Analyze market-wide cash flow

        Args:
            symbols: List of symbols to analyze (None = all available)
            base_timeframe: Base timeframe for data loading
            limit: Number of recent candles to load

        Returns:
            Complete market cash flow report
        """
        logger.info(f"🔍 Starting market cash flow analysis (timeframe={base_timeframe}, limit={limit})")

        # Load data for all symbols
        market_data = self._load_market_data(symbols, base_timeframe, limit)

        if not market_data:
            logger.warning("⚠️ No market data available")
            return {
                'status': 'error',
                'message': 'No market data available',
                'timestamp': datetime.now().isoformat()
            }

        logger.info(f"📊 Loaded data for {len(market_data)} symbols")

        # Calculate market-wide metrics
        market_metrics = self._calculate_market_metrics(market_data)

        # Calculate coin-specific cash flows
        coin_flows = self._calculate_coin_flows(market_data)

        # Generate report
        report = self._generate_report(market_metrics, coin_flows)

        logger.info("✅ Market cash flow analysis complete")
        return report

    def _load_market_data(
        self,
        symbols: Optional[List[str]],
        timeframe: str,
        limit: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Load market data for all symbols

        Returns:
            Dict mapping symbol -> DataFrame
        """
        market_data = {}

        if symbols is None:
            # Auto-discover symbols from parquet files
            pattern = f"*_{timeframe}_*.parquet"
            files = list(self.data_dir.glob(pattern))
            logger.info(f"🔍 Found {len(files)} parquet files matching {pattern}")
        else:
            files = [
                self.data_dir / f"{symbol}_{timeframe}_futures.parquet"
                for symbol in symbols
            ]

        for file_path in files:
            try:
                if not file_path.exists():
                    continue

                # Extract symbol from filename
                symbol = file_path.stem.split('_')[0]

                # Load parquet
                df = pd.read_parquet(file_path)

                # Normalize column names (handle different naming conventions)
                # Binance uses: open_time, taker_base, quote_asset_volume
                # We expect: timestamp, taker_buy_base (USD-based!)
                if 'open_time' in df.columns and 'timestamp' not in df.columns:
                    df['timestamp'] = df['open_time']

                # Use USD-based volumes for accurate comparison
                # If quote_asset_volume exists, use it instead of base volume
                if 'quote_asset_volume' in df.columns:
                    df['volume'] = df['quote_asset_volume']  # USD volume
                    if 'taker_quote' in df.columns:
                        df['taker_buy_base'] = df['taker_quote']  # USD buy volume
                    elif 'taker_base' in df.columns:
                        # Fallback: convert coin volume to USD
                        logger.warning(f"⚠️ {symbol}: Using coin volume (less accurate)")
                        df['taker_buy_base'] = df['taker_base']
                elif 'taker_base' in df.columns and 'taker_buy_base' not in df.columns:
                    # Old format: only coin volume available
                    logger.warning(f"⚠️ {symbol}: Using coin volume (less accurate)")
                    df['taker_buy_base'] = df['taker_base']

                # Filter recent data
                if len(df) > limit:
                    df = df.tail(limit)

                # Validate required columns
                required = ['timestamp', 'volume', 'close', 'taker_buy_base']
                if not all(col in df.columns for col in required):
                    missing = [c for c in required if c not in df.columns]
                    logger.warning(f"⚠️ {symbol}: Missing required columns: {missing}")
                    continue

                # Ensure timestamp is datetime
                if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
                    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

                # Ensure numeric columns are numeric
                numeric_cols = ['volume', 'close', 'taker_buy_base', 'open', 'high', 'low',
                              'quote_asset_volume', 'taker_quote']
                for col in numeric_cols:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                market_data[symbol] = df
                logger.debug(f"✓ Loaded {symbol}: {len(df)} candles")

            except Exception as e:
                logger.warning(f"⚠️ Failed to load {file_path.name}: {e}")
                continue

        return market_data

    def _calculate_market_metrics(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Calculate market-wide metrics

        Returns buyer percentages for different timeframes
        """
        # Timeframes to analyze (in minutes)
        timeframes = {
            '15m': 15,
            '1h': 60,
            '4h': 240,
            '12h': 720,
            '1d': 1440
        }

        market_metrics = {
            'timeframes': {},
            'total_volume': 0.0,
            'total_buy_volume': 0.0
        }

        for tf_name, minutes in timeframes.items():
            buy_volumes = []
            total_volumes = []

            for symbol, df in market_data.items():
                try:
                    # Get recent data for this timeframe
                    cutoff_time = df['timestamp'].max() - pd.Timedelta(minutes=minutes)
                    recent_df = df[df['timestamp'] > cutoff_time]

                    if len(recent_df) == 0:
                        continue

                    # Calculate buy/sell volumes
                    buy_vol = recent_df['taker_buy_base'].sum()
                    total_vol = recent_df['volume'].sum()

                    if total_vol > 0:
                        buy_volumes.append(buy_vol)
                        total_volumes.append(total_vol)

                except Exception as e:
                    logger.debug(f"⚠️ {symbol}/{tf_name}: {e}")
                    continue

            # Calculate weighted average buyer percentage
            if total_volumes:
                total_market_vol = sum(total_volumes)
                total_market_buy = sum(buy_volumes)
                buyer_pct = (total_market_buy / total_market_vol * 100) if total_market_vol > 0 else 0

                market_metrics['timeframes'][tf_name] = {
                    'buyer_percentage': buyer_pct,
                    'total_volume': total_market_vol,
                    'buy_volume': total_market_buy
                }
            else:
                market_metrics['timeframes'][tf_name] = {
                    'buyer_percentage': 0,
                    'total_volume': 0,
                    'buy_volume': 0
                }

        # Overall market stats (last 24h)
        if '1d' in market_metrics['timeframes']:
            market_metrics['total_volume'] = market_metrics['timeframes']['1d']['total_volume']
            market_metrics['total_buy_volume'] = market_metrics['timeframes']['1d']['buy_volume']

        # Calculate short-term buying power (momentum)
        # Compare 15m buyer% to 1d buyer%
        buyer_15m = market_metrics['timeframes']['15m']['buyer_percentage']
        buyer_1d = market_metrics['timeframes']['1d']['buyer_percentage']

        if buyer_1d > 0:
            market_metrics['short_term_power'] = buyer_15m / buyer_1d
        else:
            market_metrics['short_term_power'] = 1.0

        return market_metrics

    def _calculate_coin_flows(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """
        Calculate cash flow for each coin

        Returns list of coin flow data sorted by volume
        """
        coin_flows = []
        total_market_volume = 0

        # First pass: calculate total market volume
        for symbol, df in market_data.items():
            recent_24h = df.tail(96)  # Approx 24h for 15min candles
            total_market_volume += recent_24h['volume'].sum()

        # Second pass: calculate each coin's metrics
        for symbol, df in market_data.items():
            try:
                # Recent 24h data
                recent_24h = df.tail(96)

                # Total volume for this coin
                coin_volume = recent_24h['volume'].sum()
                coin_buy_volume = recent_24h['taker_buy_base'].sum()

                if coin_volume == 0:
                    continue

                # Cash share (volume percentage in market)
                cash_share = (coin_volume / total_market_volume * 100) if total_market_volume > 0 else 0

                # Buyer percentages for different timeframes
                timeframes = {
                    '15m': 1,   # last 1 candle (15min)
                    '1h': 4,    # last 4 candles
                    '4h': 16,   # last 16 candles
                    '12h': 48,  # last 48 candles
                    '1d': 96    # last 96 candles
                }

                buyer_percentages = {}
                for tf_name, candles in timeframes.items():
                    tf_df = df.tail(candles)
                    tf_buy = tf_df['taker_buy_base'].sum()
                    tf_vol = tf_df['volume'].sum()
                    buyer_percentages[tf_name] = (tf_buy / tf_vol * 100) if tf_vol > 0 else 0

                # Momentum score: 15m buyer% / average buyer%
                avg_buyer = np.mean(list(buyer_percentages.values()))
                momentum = buyer_percentages['15m'] / avg_buyer if avg_buyer > 0 else 1.0

                # Determine trend indicators (🔼🔻)
                # Check if buyer% > 50 for each timeframe
                indicators = []
                for tf in ['15m', '1h', '4h', '12h', '1d']:
                    if buyer_percentages[tf] >= 50:
                        indicators.append('🔼')
                    else:
                        indicators.append('🔻')

                coin_flows.append({
                    'symbol': symbol,
                    'cash_share': cash_share,
                    'buyer_15m': buyer_percentages['15m'],
                    'buyer_1h': buyer_percentages['1h'],
                    'buyer_4h': buyer_percentages['4h'],
                    'buyer_12h': buyer_percentages['12h'],
                    'buyer_1d': buyer_percentages['1d'],
                    'momentum': momentum,
                    'indicators': ''.join(indicators),
                    'total_volume': coin_volume
                })

            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate flow for {symbol}: {e}")
                continue

        # Sort by cash share (descending)
        coin_flows.sort(key=lambda x: x['cash_share'], reverse=True)

        return coin_flows

    def _generate_report(
        self,
        market_metrics: Dict[str, Any],
        coin_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate formatted report

        Returns complete report dict
        """
        # Market volume share (top 30 coins volume / total volume)
        top_volume = sum(c['total_volume'] for c in coin_flows[:30])
        total_volume = market_metrics['total_volume']
        market_share = (top_volume / total_volume * 100) if total_volume > 0 else 0

        # Risk assessment based on 1d buyer percentage
        buyer_1d = market_metrics['timeframes']['1d']['buyer_percentage']

        if buyer_1d >= 50:
            risk_level = 'low'
            risk_message = 'Piyasa düşük risk seviyesinde. Alım yapılabilir.'
        elif buyer_1d >= 45:
            risk_level = 'medium'
            risk_message = 'Piyasa orta risk seviyesinde. Dikkatli olun.'
        else:
            risk_level = 'high'
            risk_message = 'Piyasa ciddi anlamda risk barındırıyor. Alım Yapma!'

        # Generate text report
        text_report = self._format_text_report(market_metrics, coin_flows, market_share, risk_message)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'market_metrics': {
                'short_term_power': round(market_metrics['short_term_power'], 1),
                'market_volume_share': round(market_share, 1),
                'timeframes': {
                    tf: {
                        'buyer_percentage': round(data.get('buyer_percentage', 0), 1),
                        'indicator': '🔼' if data.get('buyer_percentage', 0) >= 50 else '🔻'
                    }
                    for tf, data in market_metrics.get('timeframes', {}).items()
                }
            },
            'risk_assessment': {
                'level': risk_level,
                'message': risk_message,
                'buyer_1d': round(buyer_1d, 1)
            },
            'top_flows': coin_flows[:30],  # Top 30 coins
            'total_coins': len(coin_flows),
            'text_report': text_report
        }

    def _format_text_report(
        self,
        market_metrics: Dict[str, Any],
        coin_flows: List[Dict[str, Any]],
        market_share: float,
        risk_message: str
    ) -> str:
        """
        Format human-readable text report
        """
        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu")
        lines.append("=" * 60)
        lines.append("")

        # Market overview
        power = market_metrics['short_term_power']
        lines.append(f"Kısa Vadeli Market Alım Gücü: {power:.1f}X")
        lines.append(f"Marketteki Hacim Payı: %{market_share:.1f}")
        lines.append("")

        # Timeframe buyer percentages
        for tf, data in market_metrics.get('timeframes', {}).items():
            pct = data.get('buyer_percentage', 0)
            indicator = '🔼' if pct >= 50 else '🔻'
            lines.append(f"{tf}=> %{pct:.1f} {indicator}")

        lines.append("")
        lines.append("-" * 60)
        lines.append("En çok nakit girişi olanlar.")
        lines.append("(Sonunda 🔼 olanlarda nakit girişi daha sağlıklıdır)")
        lines.append("Nakitin nereye aktığını gösterir. (Nakit Göçü Raporu)")
        lines.append("-" * 60)
        lines.append("")

        # Top coins by cash flow
        for coin in coin_flows[:30]:
            symbol = coin['symbol'].replace('USDT', '')  # Remove USDT suffix
            cash = coin['cash_share']
            buyer_15m = coin['buyer_15m']
            momentum = coin['momentum']
            indicators = coin['indicators']

            line = f"{symbol} Nakit: %{cash:.1f} 15m:%{buyer_15m:.0f} Mts: {momentum:.1f} {indicators}"
            lines.append(line)

        lines.append("")
        lines.append("-" * 60)
        lines.append(risk_message)
        lines.append(f"Günlük nakit giriş oranı (1d satırındaki değer) %50 üzerine çıkarsa risk azalacaktır.")
        buyer_1d = market_metrics['timeframes']['1d']['buyer_percentage']
        if buyer_1d < 49:
            lines.append(f"Bu değer %{buyer_1d:.1f} ile %49 altında oldukça piyasaya bulaşma!")

        lines.append("")
        lines.append("📅 Rapor Zamanı: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        lines.append("=" * 60)

        return "\n".join(lines)
