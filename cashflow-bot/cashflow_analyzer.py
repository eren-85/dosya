"""
Market Cash Flow Analyzer - Standalone Version

Binance'den canlı veri çekerek market nakit akışını analiz eder.
Telegram/Discord botları için optimize edilmiştir.

Özellikler:
- API Key gerektirmez
- Canlı Binance Spot verisi
- USD bazlı hesaplama
- Top N coin otomatik seçimi
- Risk değerlendirmesi
- Emoji göstergeleri
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CashFlowAnalyzer:
    """Binance'den canlı veri çekerek nakit akışı analizi"""

    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def analyze(
        self,
        symbols: Optional[List[str]] = None,
        timeframe: str = '15m',
        top_n: int = 30,
        limit: int = 500
    ) -> Dict[str, Any]:
        """
        Ana analiz fonksiyonu

        Args:
            symbols: Analiz edilecek coinler (None = otomatik top N)
            timeframe: Candle aralığı ('15m', '1h', '4h', '1d')
            top_n: Otomatik seçimde kaç coin (5-50)
            limit: Kaç candle analiz edilecek (100-1000)

        Returns:
            Analiz raporu (dict)
        """
        logger.info(f"🔍 Analiz başlatılıyor (timeframe={timeframe}, top_n={top_n})")

        # Coin seçimi
        if symbols is None:
            symbols = self._get_top_coins(top_n)
            logger.info(f"📊 Top {len(symbols)} coin seçildi")

        # Veri çekme
        market_data = self._fetch_data(symbols, timeframe, limit)
        if not market_data:
            return {'status': 'error', 'message': 'Veri çekilemedi'}

        logger.info(f"✅ {len(market_data)} coin için veri çekildi")

        # Analiz
        metrics = self._calculate_metrics(market_data)
        flows = self._calculate_flows(market_data)
        report = self._generate_report(metrics, flows)

        logger.info("✅ Analiz tamamlandı")
        return report

    def _get_top_coins(self, limit: int) -> List[str]:
        """24h USD hacmine göre top coinleri getir"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            tickers = response.json()
            usdt_pairs = [
                t for t in tickers
                if t['symbol'].endswith('USDT') and float(t['quoteVolume']) > 0
            ]
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)
            return [t['symbol'] for t in usdt_pairs[:limit]]

        except Exception as e:
            logger.warning(f"⚠️ Top coin seçimi başarısız: {e}")
            # Fallback
            return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']

    def _fetch_data(
        self,
        symbols: List[str],
        timeframe: str,
        limit: int
    ) -> Dict[str, pd.DataFrame]:
        """Her coin için kline verisi çek"""
        data = {}
        for symbol in symbols:
            try:
                url = f"{self.base_url}/api/v3/klines"
                params = {'symbol': symbol, 'interval': timeframe, 'limit': min(limit, 1000)}

                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                klines = response.json()

                if not klines:
                    continue

                df = pd.DataFrame(klines, columns=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_volume', 'trades',
                    'taker_buy_base', 'taker_buy_quote', 'ignore'
                ])

                df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
                for col in ['close', 'quote_volume', 'taker_buy_quote']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

                # USD volume kullan
                df['volume'] = df['quote_volume']
                df['taker_buy'] = df['taker_buy_quote']

                data[symbol] = df[['timestamp', 'close', 'volume', 'taker_buy']]

            except Exception as e:
                logger.debug(f"⚠️ {symbol} çekilemedi: {e}")
                continue

        return data

    def _calculate_metrics(self, data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Market geneli metrikler"""
        timeframes = {'15m': 15, '1h': 60, '4h': 240, '12h': 720, '1d': 1440}
        metrics = {'timeframes': {}}

        for tf_name, minutes in timeframes.items():
            buy_vols, total_vols = [], []

            for symbol, df in data.items():
                cutoff = df['timestamp'].max() - pd.Timedelta(minutes=minutes)
                recent = df[df['timestamp'] > cutoff]
                if len(recent) > 0:
                    buy_vols.append(recent['taker_buy'].sum())
                    total_vols.append(recent['volume'].sum())

            if total_vols:
                total = sum(total_vols)
                buy = sum(buy_vols)
                pct = (buy / total * 100) if total > 0 else 0
                metrics['timeframes'][tf_name] = {
                    'buyer_percentage': pct,
                    'total_volume': total,
                    'buy_volume': buy
                }

        # Short-term power
        buyer_15m = metrics['timeframes'].get('15m', {}).get('buyer_percentage', 0)
        buyer_1d = metrics['timeframes'].get('1d', {}).get('buyer_percentage', 1)
        metrics['short_term_power'] = buyer_15m / buyer_1d if buyer_1d > 0 else 1.0

        return metrics

    def _calculate_flows(self, data: Dict[str, pd.DataFrame]) -> List[Dict[str, Any]]:
        """Coin bazlı nakit akışları"""
        flows = []
        total_market_vol = sum(df.tail(96)['volume'].sum() for df in data.values())

        for symbol, df in data.items():
            recent = df.tail(96)
            coin_vol = recent['volume'].sum()
            coin_buy = recent['taker_buy'].sum()

            if coin_vol == 0:
                continue

            # Cash share
            cash_share = (coin_vol / total_market_vol * 100) if total_market_vol > 0 else 0

            # Timeframe percentages
            timeframes = {'15m': 1, '1h': 4, '4h': 16, '12h': 48, '1d': 96}
            buyer_pcts = {}
            for tf, candles in timeframes.items():
                tf_df = df.tail(candles)
                tf_buy = tf_df['taker_buy'].sum()
                tf_vol = tf_df['volume'].sum()
                buyer_pcts[tf] = (tf_buy / tf_vol * 100) if tf_vol > 0 else 0

            # Momentum
            avg_buyer = np.mean(list(buyer_pcts.values()))
            momentum = buyer_pcts['15m'] / avg_buyer if avg_buyer > 0 else 1.0

            # Indicators
            indicators = ''.join(['🔼' if buyer_pcts[tf] >= 50 else '🔻'
                                 for tf in ['15m', '1h', '4h', '12h', '1d']])

            flows.append({
                'symbol': symbol,
                'cash_share': cash_share,
                'buyer_15m': buyer_pcts['15m'],
                'momentum': momentum,
                'indicators': indicators,
                'total_volume': coin_vol
            })

        flows.sort(key=lambda x: x['cash_share'], reverse=True)
        return flows

    def _generate_report(
        self,
        metrics: Dict[str, Any],
        flows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Rapor oluştur"""
        buyer_1d = metrics['timeframes'].get('1d', {}).get('buyer_percentage', 0)

        # Risk
        if buyer_1d >= 50:
            risk_level = 'low'
            risk_msg = 'Piyasa düşük risk seviyesinde. Alım yapılabilir.'
        elif buyer_1d >= 45:
            risk_level = 'medium'
            risk_msg = 'Piyasa orta risk seviyesinde. Dikkatli olun.'
        else:
            risk_level = 'high'
            risk_msg = 'Piyasa ciddi anlamda risk barındırıyor. Alım Yapma!'

        # Text report
        text = self._format_text(metrics, flows, risk_msg)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'market_metrics': metrics,
            'risk_assessment': {
                'level': risk_level,
                'message': risk_msg,
                'buyer_1d': buyer_1d
            },
            'top_flows': flows[:30],
            'total_coins': len(flows),
            'text_report': text
        }

    def _format_text(
        self,
        metrics: Dict[str, Any],
        flows: List[Dict[str, Any]],
        risk_msg: str
    ) -> str:
        """Text formatında rapor"""
        lines = [
            "=" * 60,
            "📊 Market Nakit Akışı Raporu",
            "🔴 CANLI VERİ - Binance Spot",
            "=" * 60,
            "",
            f"Kısa Vadeli Alım Gücü: {metrics['short_term_power']:.1f}X",
            ""
        ]

        # Timeframes
        for tf, data in metrics['timeframes'].items():
            pct = data['buyer_percentage']
            ind = '🔼' if pct >= 50 else '🔻'
            lines.append(f"{tf}=> %{pct:.1f} {ind}")

        lines.extend([
            "",
            "-" * 60,
            "En Çok Nakit Girişi Olanlar",
            "-" * 60,
            ""
        ])

        # Top coins
        for coin in flows[:30]:
            sym = coin['symbol'].replace('USDT', '')
            lines.append(
                f"{sym} Nakit:%{coin['cash_share']:.1f} "
                f"15m:%{coin['buyer_15m']:.0f} "
                f"Mts:{coin['momentum']:.1f} {coin['indicators']}"
            )

        lines.extend([
            "",
            "-" * 60,
            risk_msg,
            f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60
        ])

        return "\n".join(lines)


# Standalone kullanım
if __name__ == '__main__':
    analyzer = CashFlowAnalyzer()
    report = analyzer.analyze(top_n=30)

    if report['status'] == 'success':
        print(report['text_report'])
    else:
        print(f"Hata: {report.get('message')}")
