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
        limit: int = 500,
        format: str = 'text'
    ) -> Dict[str, Any]:
        """
        Ana analiz fonksiyonu

        Args:
            symbols: Analiz edilecek coinler (None = otomatik top N)
            timeframe: Candle aralığı ('15m', '1h', '4h', '1d')
            top_n: Otomatik seçimde kaç coin (5-50)
            limit: Kaç candle analiz edilecek (100-1000)
            format: Çıktı formatı ('text', 'table', 'html')

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
        report = self._generate_report(metrics, flows, format)

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
                'buyer_1h': buyer_pcts['1h'],
                'buyer_4h': buyer_pcts['4h'],
                'buyer_12h': buyer_pcts['12h'],
                'buyer_1d': buyer_pcts['1d'],
                'momentum': momentum,
                'indicators': indicators,
                'total_volume': coin_vol
            })

        flows.sort(key=lambda x: x['cash_share'], reverse=True)
        return flows

    def _generate_report(
        self,
        metrics: Dict[str, Any],
        flows: List[Dict[str, Any]],
        format: str = 'text'
    ) -> Dict[str, Any]:
        """Rapor oluştur"""
        buyer_1d = metrics['timeframes'].get('1d', {}).get('buyer_percentage', 0)
        total_volume = sum(metrics['timeframes'].get(tf, {}).get('total_volume', 0)
                          for tf in ['15m', '1h', '4h', '12h', '1d']) / 5  # Average

        # Calculate market share (top 30 coins' share in total market)
        top_30_volume = sum(f['total_volume'] for f in flows[:30])
        market_share = (top_30_volume / total_volume * 100) if total_volume > 0 else 0

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

        # Format output
        if format == 'table':
            formatted_output = self._format_table(metrics, flows, risk_msg, market_share)
        elif format == 'html':
            formatted_output = self._format_html(metrics, flows, risk_msg, market_share)
        else:
            formatted_output = self._format_text(metrics, flows, risk_msg)

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'market_metrics': metrics,
            'market_share': market_share,
            'risk_assessment': {
                'level': risk_level,
                'message': risk_msg,
                'buyer_1d': buyer_1d
            },
            'top_flows': flows[:30],
            'total_coins': len(flows),
            'text_report': formatted_output,
            'format': format
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

    def _format_table(
        self,
        metrics: Dict[str, Any],
        flows: List[Dict[str, Any]],
        risk_msg: str,
        market_share: float
    ) -> str:
        """Tablo formatında rapor"""
        lines = [
            "=" * 95,
            "📊 Market Nakit Akışı Raporu - TABLO GÖRÜNÜMÜ",
            "🔴 CANLI VERİ - Binance Spot",
            "=" * 95,
            "",
            f"Kısa Vadeli Market Alım Gücü: {metrics['short_term_power']:.1f}X",
            f"Marketteki Hacim Payı: %{market_share:.1f}",
            ""
        ]

        # Market timeframes table
        lines.append("╔═══════════════════════════════════════════════════════════════════════════╗")
        lines.append("║                        MARKET GENELİ ALIM GÜC ÜÇ                         ║")
        lines.append("╠═════════╦══════════════╦══════════════╦══════════════╦══════════════════╣")
        lines.append("║   15m   ║      1h      ║      4h      ║     12h      ║        1d        ║")
        lines.append("╠═════════╬══════════════╬══════════════╬══════════════╬══════════════════╣")

        tf_data = metrics['timeframes']
        tf_line = "║"
        for tf in ['15m', '1h', '4h', '12h', '1d']:
            pct = tf_data.get(tf, {}).get('buyer_percentage', 0)
            ind = '🔼' if pct >= 50 else '🔻'
            if tf == '1d':
                tf_line += f" %{pct:5.1f} {ind} ║"
            else:
                tf_line += f" %{pct:5.1f} {ind} ║"
        lines.append(tf_line)
        lines.append("╚═════════╩══════════════╩══════════════╩══════════════╩══════════════════╝")
        lines.append("")

        # Top coins table header
        lines.append("╔══════════════════════════════════════════════════════════════════════════════════════════╗")
        lines.append("║                          EN ÇOK NAKİT GİRİŞİ OLAN COİNLER                                ║")
        lines.append("╠═══════╦═══════╦═══════╦══════╦═══════╦═══════╦═══════╦═══════╦═══════╦═══════════════╣")
        lines.append("║  Coin ║ Nakit ║  15m% ║  MTS ║  15m  ║  1h   ║  4h   ║  12h  ║  1d   ║  Trend        ║")
        lines.append("╠═══════╬═══════╬═══════╬══════╬═══════╬═══════╬═══════╬═══════╬═══════╬═══════════════╣")

        # Top 30 coins
        for coin in flows[:30]:
            sym = coin['symbol'].replace('USDT', '')[:6].ljust(6)
            cash = f"{coin['cash_share']:5.1f}"
            pct_15m = f"{coin['buyer_15m']:5.1f}"
            mts = f"{coin['momentum']:4.1f}"

            # Indicators for each timeframe
            ind_15m = '🔼' if coin['buyer_15m'] >= 50 else '🔻'
            ind_1h = '🔼' if coin['buyer_1h'] >= 50 else '🔻'
            ind_4h = '🔼' if coin['buyer_4h'] >= 50 else '🔻'
            ind_12h = '🔼' if coin['buyer_12h'] >= 50 else '🔻'
            ind_1d = '🔼' if coin['buyer_1d'] >= 50 else '🔻'

            lines.append(
                f"║ {sym} ║ %{cash} ║ %{pct_15m} ║ {mts}X ║ "
                f"{ind_15m:^4} ║ {ind_1h:^4} ║ {ind_4h:^4} ║ {ind_12h:^4} ║ {ind_1d:^4} ║ "
                f"{coin['indicators']} ║"
            )

        lines.append("╚═══════╩═══════╩═══════╩══════╩═══════╩═══════╩═══════╩═══════╩═══════╩═══════════════╝")
        lines.append("")
        lines.append("─" * 95)
        lines.append(f"⚠️  {risk_msg}")
        lines.append(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 95)

        return "\n".join(lines)

    def _format_html(
        self,
        metrics: Dict[str, Any],
        flows: List[Dict[str, Any]],
        risk_msg: str,
        market_share: float
    ) -> str:
        """HTML formatında interaktif rapor"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Risk color
        buyer_1d = metrics['timeframes'].get('1d', {}).get('buyer_percentage', 0)
        if buyer_1d >= 50:
            risk_color = '#10b981'  # green
        elif buyer_1d >= 45:
            risk_color = '#f59e0b'  # orange
        else:
            risk_color = '#ef4444'  # red

        html = f"""<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Nakit Akışı Raporu - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .header .subtitle {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8fafc;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}
        .metric-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }}
        .metric-label {{
            font-size: 12px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 28px;
            font-weight: bold;
            color: #1e293b;
        }}
        .table-container {{
            padding: 30px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        thead {{
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            color: white;
        }}
        th {{
            padding: 16px 12px;
            text-align: center;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
        }}
        td {{
            padding: 14px 12px;
            text-align: center;
            border-bottom: 1px solid #e2e8f0;
        }}
        tbody tr {{
            transition: background 0.2s;
        }}
        tbody tr:hover {{
            background: #f1f5f9;
        }}
        .coin-symbol {{
            font-weight: bold;
            color: #1e293b;
            font-size: 15px;
        }}
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 220px;
            background-color: #1e293b;
            color: #fff;
            text-align: center;
            border-radius: 8px;
            padding: 12px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -110px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 13px;
            line-height: 1.5;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        .positive {{ color: #10b981; }}
        .negative {{ color: #ef4444; }}
        .footer {{
            background: #f8fafc;
            padding: 20px 30px;
            border-top: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .risk-badge {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 20px;
            background: {risk_color};
            color: white;
            font-weight: 600;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Market Nakit Akışı Raporu</h1>
            <div class="subtitle">🔴 CANLI VERİ - Binance Spot | {timestamp}</div>
        </div>

        <div class="metrics">
            <div class="metric-card">
                <div class="metric-label">Kısa Vadeli Alım Gücü</div>
                <div class="metric-value">{metrics['short_term_power']:.2f}X</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Marketteki Hacim Payı</div>
                <div class="metric-value">{market_share:.1f}%</div>
            </div>"""

        # Add timeframe metrics
        for tf in ['15m', '1h', '4h', '12h', '1d']:
            pct = metrics['timeframes'].get(tf, {}).get('buyer_percentage', 0)
            ind = '🔼' if pct >= 50 else '🔻'
            color_class = 'positive' if pct >= 50 else 'negative'
            html += f"""
            <div class="metric-card">
                <div class="metric-label">{tf} Alım Gücü</div>
                <div class="metric-value {color_class}">{pct:.1f}% {ind}</div>
            </div>"""

        html += """
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Coin</th>
                        <th>Nakit Payı</th>
                        <th>15m %</th>
                        <th>MTS</th>
                        <th>15m</th>
                        <th>1h</th>
                        <th>4h</th>
                        <th>12h</th>
                        <th>1d</th>
                        <th>Trend</th>
                    </tr>
                </thead>
                <tbody>"""

        # Add coin rows
        for coin in flows[:30]:
            sym = coin['symbol'].replace('USDT', '')
            vol_usd = coin['total_volume']

            # Format volume for tooltip
            if vol_usd >= 1e9:
                vol_str = f"${vol_usd/1e9:.2f}B"
            elif vol_usd >= 1e6:
                vol_str = f"${vol_usd/1e6:.2f}M"
            else:
                vol_str = f"${vol_usd/1e3:.2f}K"

            ind_15m = '🔼' if coin['buyer_15m'] >= 50 else '🔻'
            ind_1h = '🔼' if coin['buyer_1h'] >= 50 else '🔻'
            ind_4h = '🔼' if coin['buyer_4h'] >= 50 else '🔻'
            ind_12h = '🔼' if coin['buyer_12h'] >= 50 else '🔻'
            ind_1d = '🔼' if coin['buyer_1d'] >= 50 else '🔻'

            html += f"""
                    <tr>
                        <td class="tooltip">
                            <span class="coin-symbol">{sym}</span>
                            <span class="tooltiptext">
                                <strong>{coin['symbol']}</strong><br>
                                24h Hacim: {vol_str}<br>
                                Nakit Payı: %{coin['cash_share']:.2f}<br>
                                Momentum: {coin['momentum']:.2f}X
                            </span>
                        </td>
                        <td><strong>{coin['cash_share']:.1f}%</strong></td>
                        <td class="{'positive' if coin['buyer_15m'] >= 50 else 'negative'}">
                            <strong>{coin['buyer_15m']:.1f}%</strong>
                        </td>
                        <td><strong>{coin['momentum']:.2f}X</strong></td>
                        <td>{ind_15m}</td>
                        <td>{ind_1h}</td>
                        <td>{ind_4h}</td>
                        <td>{ind_12h}</td>
                        <td>{ind_1d}</td>
                        <td>{coin['indicators']}</td>
                    </tr>"""

        html += f"""
                </tbody>
            </table>
        </div>

        <div class="footer">
            <div class="risk-badge">{risk_msg}</div>
            <div style="color: #64748b; font-size: 14px;">
                📅 {timestamp}
            </div>
        </div>
    </div>
</body>
</html>"""

        return html


# Standalone kullanım
if __name__ == '__main__':
    analyzer = CashFlowAnalyzer()
    report = analyzer.analyze(top_n=30)

    if report['status'] == 'success':
        print(report['text_report'])
    else:
        print(f"Hata: {report.get('message')}")
