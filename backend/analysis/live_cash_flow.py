"""
Live Market Cash Flow Analyzer - Binance'den Anlık Veri Çeker

API Key gerektirmez, public endpoint kullanır.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LiveMarketCashFlowAnalyzer:
    """
    Binance'den anlık veri çekerek market cash flow analizi yapar

    Avantajlar:
    - API key gerektirmez
    - Her seferinde güncel veri
    - Parquet dosyası gerekmez
    - Telegram/Discord botları için ideal
    """

    def __init__(self, base_url: str = "https://api.binance.com"):
        """
        Initialize live analyzer

        Args:
            base_url: Binance Spot API base URL (default: Spot API - more reliable)
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def analyze_market(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = '15m',
        limit: int = 500,
        top_n: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze market cash flow with live data from Binance

        Args:
            symbols: List of symbols (None = get top coins by volume)
            timeframe: Candle timeframe ('15m', '1h', '4h', '12h', '1d')
            limit: Number of recent candles to fetch
            top_n: Number of top coins to analyze if symbols=None

        Returns:
            Complete market cash flow report
        """
        logger.info(f"🔍 Starting LIVE market analysis (timeframe={timeframe})")

        # Get symbols to analyze
        if symbols is None:
            symbols = self._get_top_symbols(limit=top_n)
            logger.info(f"📊 Auto-selected top {len(symbols)} symbols by volume")
        else:
            logger.info(f"📊 Analyzing {len(symbols)} specified symbols")

        # Fetch live data for all symbols
        market_data = self._fetch_market_data(symbols, timeframe, limit)

        if not market_data:
            logger.warning("⚠️ No market data fetched")
            return {
                'status': 'error',
                'message': 'No market data available from Binance',
                'timestamp': datetime.now().isoformat()
            }

        logger.info(f"✅ Fetched data for {len(market_data)} symbols")

        # Calculate metrics (reuse existing logic)
        market_metrics = self._calculate_market_metrics(market_data)
        coin_flows = self._calculate_coin_flows(market_data)

        # Generate report
        report = self._generate_report(market_metrics, coin_flows)

        logger.info("✅ Live market analysis complete")
        return report

    def _get_top_symbols(self, limit: int = 30) -> List[str]:
        """
        Get top symbols by 24h volume from Binance

        Returns:
            List of symbol names (e.g., ['BTCUSDT', 'ETHUSDT', ...])
        """
        try:
            # Use Spot API (more reliable than Futures)
            url = f"{self.base_url}/api/v3/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            tickers = response.json()

            # Filter USDT pairs and sort by volume
            usdt_pairs = [
                t for t in tickers
                if t['symbol'].endswith('USDT')
                and float(t['quoteVolume']) > 0
            ]

            # Sort by quote volume (USD volume)
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)

            # Get top symbols
            symbols = [t['symbol'] for t in usdt_pairs[:limit]]

            logger.info(f"🔍 Top symbols by volume: {symbols[:5]}...")
            return symbols

        except Exception as e:
            logger.error(f"❌ Failed to get top symbols: {e}")
            # Fallback to default top coins
            return [
                'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
                'DOGEUSDT', 'ADAUSDT', 'TRXUSDT', 'AVAXUSDT', 'LINKUSDT'
            ]

    def _fetch_market_data(
        self,
        symbols: List[str],
        timeframe: str,
        limit: int
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch live OHLCV data from Binance for all symbols

        Returns:
            Dict mapping symbol -> DataFrame
        """
        market_data = {}

        for symbol in symbols:
            try:
                df = self._fetch_klines(symbol, timeframe, limit)

                if df is not None and len(df) > 0:
                    market_data[symbol] = df
                    logger.debug(f"✓ Fetched {symbol}: {len(df)} candles")

            except Exception as e:
                logger.warning(f"⚠️ Failed to fetch {symbol}: {e}")
                continue

        return market_data

    def _fetch_klines(
        self,
        symbol: str,
        timeframe: str,
        limit: int
    ) -> Optional[pd.DataFrame]:
        """
        Fetch klines (OHLCV) data from Binance Spot API

        Args:
            symbol: Symbol name (e.g., 'BTCUSDT')
            timeframe: Candle interval ('15m', '1h', '4h', '1d')
            limit: Number of candles (max 1000 for Spot)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume, taker_buy_base
        """
        try:
            # Use Spot API
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': timeframe,
                'limit': min(limit, 1000)  # Spot API max limit
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            klines = response.json()

            if not klines:
                return None

            # Parse klines into DataFrame
            # Binance klines format:
            # [
            #   [open_time, open, high, low, close, volume, close_time,
            #    quote_asset_volume, trades, taker_buy_base, taker_buy_quote, ignore]
            # ]

            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')

            # Convert to numeric
            numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'taker_buy_base']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # Select required columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'taker_buy_base']]

            return df

        except Exception as e:
            logger.warning(f"⚠️ Error fetching {symbol} klines: {e}")
            return None

    def _calculate_market_metrics(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """Calculate market-wide buyer percentages for different timeframes"""

        # Timeframes in minutes
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

        # Calculate short-term buying power
        buyer_15m = market_metrics['timeframes'].get('15m', {}).get('buyer_percentage', 0)
        buyer_1d = market_metrics['timeframes'].get('1d', {}).get('buyer_percentage', 1)

        if buyer_1d > 0:
            market_metrics['short_term_power'] = buyer_15m / buyer_1d
        else:
            market_metrics['short_term_power'] = 1.0

        return market_metrics

    def _calculate_coin_flows(
        self,
        market_data: Dict[str, pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Calculate cash flow for each coin"""

        coin_flows = []
        total_market_volume = 0

        # Calculate total market volume (approx 24h)
        for symbol, df in market_data.items():
            recent_24h = df.tail(96)  # Approx 24h for 15min candles
            total_market_volume += recent_24h['volume'].sum()

        # Calculate each coin's metrics
        for symbol, df in market_data.items():
            try:
                # Recent 24h data
                recent_24h = df.tail(96)

                coin_volume = recent_24h['volume'].sum()
                coin_buy_volume = recent_24h['taker_buy_base'].sum()

                if coin_volume == 0:
                    continue

                # Cash share
                cash_share = (coin_volume / total_market_volume * 100) if total_market_volume > 0 else 0

                # Buyer percentages for different timeframes
                timeframes = {
                    '15m': 1,
                    '1h': 4,
                    '4h': 16,
                    '12h': 48,
                    '1d': 96
                }

                buyer_percentages = {}
                for tf_name, candles in timeframes.items():
                    tf_df = df.tail(candles)
                    tf_buy = tf_df['taker_buy_base'].sum()
                    tf_vol = tf_df['volume'].sum()
                    buyer_percentages[tf_name] = (tf_buy / tf_vol * 100) if tf_vol > 0 else 0

                # Momentum score
                avg_buyer = np.mean(list(buyer_percentages.values()))
                momentum = buyer_percentages['15m'] / avg_buyer if avg_buyer > 0 else 1.0

                # Trend indicators
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

        # Sort by cash share
        coin_flows.sort(key=lambda x: x['cash_share'], reverse=True)

        return coin_flows

    def _generate_report(
        self,
        market_metrics: Dict[str, Any],
        coin_flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate formatted report"""

        # Market volume share
        top_volume = sum(c['total_volume'] for c in coin_flows[:30])
        total_volume = market_metrics.get('total_volume', 1)
        market_share = (top_volume / total_volume * 100) if total_volume > 0 else 0

        # Risk assessment
        buyer_1d = market_metrics['timeframes'].get('1d', {}).get('buyer_percentage', 0)

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
                'short_term_power': round(market_metrics.get('short_term_power', 1.0), 1),
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
            'top_flows': coin_flows[:30],
            'total_coins': len(coin_flows),
            'text_report': text_report,
            'data_source': 'binance_live'
        }

    def _format_text_report(
        self,
        market_metrics: Dict[str, Any],
        coin_flows: List[Dict[str, Any]],
        market_share: float,
        risk_message: str
    ) -> str:
        """Format human-readable text report"""

        lines = []

        # Header
        lines.append("=" * 60)
        lines.append("📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu")
        lines.append("🔴 CANLI VERİ - Binance Futures")
        lines.append("=" * 60)
        lines.append("")

        # Market overview
        power = market_metrics.get('short_term_power', 1.0)
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

        # Top coins
        for coin in coin_flows[:30]:
            symbol = coin['symbol'].replace('USDT', '')
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

        buyer_1d = market_metrics.get('timeframes', {}).get('1d', {}).get('buyer_percentage', 0)
        if buyer_1d < 49:
            lines.append(f"Bu değer %{buyer_1d:.1f} ile %49 altında oldukça piyasaya bulaşma!")

        lines.append("")
        lines.append("📅 Rapor Zamanı: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        lines.append("=" * 60)

        return "\n".join(lines)
