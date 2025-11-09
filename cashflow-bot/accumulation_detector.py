"""
Accumulation Detector - Gizli Toplanan Coinleri Tespit Et

Mantık:
- Hacim artıyor (whale'ler topluyor)
- Fiyat artmıyor/düşüyor (dikkat çekmemek için)
- Alım baskısı var ama aşırı değil (gizli akümülasyon)
- İşlem sayısı artıyor
- OBV (On-Balance Volume) artıyor

Sinyal:
✅ Hacim 7 gün ortalamasına göre %50+ artış
✅ Fiyat değişimi <%5 (yatay hareket)
✅ Alım baskısı %52-60 (gizli ama var)
✅ Trade count %30+ artış
✅ OBV trendi pozitif

Kullanım:
    python accumulation_detector.py

    veya

    from accumulation_detector import AccumulationDetector
    detector = AccumulationDetector()
    signals = detector.scan()
"""

import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AccumulationDetector:
    """Akümülasyon (gizli toplama) tespiti"""

    def __init__(self):
        self.base_url = "https://api.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def scan(
        self,
        min_volume_usd: float = 500000,
        max_coins: int = 200,
        volume_increase_threshold: float = 50.0,
        price_change_threshold: float = 5.0,
        buy_pressure_min: float = 52.0,
        buy_pressure_max: float = 60.0,
        trade_count_threshold: float = 30.0
    ) -> Dict[str, Any]:
        """
        Akümülasyon sinyalleri tara

        Args:
            min_volume_usd: Minimum 24h USD volume ($500K default)
            max_coins: Maksimum kaç coin taransın (200)
            volume_increase_threshold: Hacim artış eşiği (%50)
            price_change_threshold: Maksimum fiyat değişimi (%5)
            buy_pressure_min: Minimum alım baskısı (%52)
            buy_pressure_max: Maksimum alım baskısı (%60 - çok yüksek olmamalı)
            trade_count_threshold: Trade count artış eşiği (%30)

        Returns:
            Akümülasyon sinyalleri
        """
        logger.info(f"🔍 Akümülasyon taraması başlıyor...")
        logger.info(f"📊 Kriterler: Vol↑%{volume_increase_threshold}, Price<%{price_change_threshold}, Buy%{buy_pressure_min}-{buy_pressure_max}")

        # 1. Coinleri al (yüksek hacimli)
        symbols = self._get_active_coins(min_volume_usd, max_coins)
        logger.info(f"📈 {len(symbols)} coin taranacak (min volume: ${min_volume_usd:,.0f})")

        # 2. Her coin için akümülasyon analizi
        accumulation_signals = []

        for i, symbol in enumerate(symbols):
            try:
                if (i + 1) % 20 == 0:
                    logger.info(f"⏳ İlerleme: {i+1}/{len(symbols)} coin tarandı...")
                    time.sleep(1)  # Rate limit

                signal = self._analyze_accumulation(
                    symbol,
                    volume_increase_threshold,
                    price_change_threshold,
                    buy_pressure_min,
                    buy_pressure_max,
                    trade_count_threshold
                )

                if signal:
                    accumulation_signals.append(signal)
                    logger.info(f"✅ Sinyal: {symbol} - Skor: {signal['accumulation_score']:.1f}")

                time.sleep(0.2)  # Rate limit

            except Exception as e:
                logger.debug(f"⚠️ {symbol} analiz hatası: {e}")
                continue

        # 3. Skorla ve sırala
        accumulation_signals.sort(key=lambda x: x['accumulation_score'], reverse=True)

        logger.info(f"✅ Tarama tamamlandı! {len(accumulation_signals)} akümülasyon sinyali bulundu")

        return {
            'status': 'success',
            'timestamp': datetime.now().isoformat(),
            'total_scanned': len(symbols),
            'signals_found': len(accumulation_signals),
            'signals': accumulation_signals,
            'criteria': {
                'volume_increase': f'>{volume_increase_threshold}%',
                'price_change': f'<{price_change_threshold}%',
                'buy_pressure': f'{buy_pressure_min}-{buy_pressure_max}%',
                'trade_count_increase': f'>{trade_count_threshold}%'
            }
        }

    def _get_active_coins(self, min_volume_usd: float, max_coins: int) -> List[str]:
        """Aktif coinleri al (hacme göre)"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            tickers = response.json()

            # USDT çiftleri filtrele
            usdt_pairs = [
                t for t in tickers
                if t['symbol'].endswith('USDT') and float(t['quoteVolume']) >= min_volume_usd
            ]

            # Hacme göre sırala
            usdt_pairs.sort(key=lambda x: float(x['quoteVolume']), reverse=True)

            return [t['symbol'] for t in usdt_pairs[:max_coins]]

        except Exception as e:
            logger.error(f"⚠️ Coin listesi alınamadı: {e}")
            return []

    def _analyze_accumulation(
        self,
        symbol: str,
        vol_threshold: float,
        price_threshold: float,
        buy_min: float,
        buy_max: float,
        trade_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """
        Tek bir coin için akümülasyon analizi

        CRITICAL FIXES APPLIED:
        1. Buy pressure: Fixed index [10] for taker buy QUOTE volume (was [9] - wrong unit)
        2. Volume increase: Added $100K minimum avg volume filter to prevent million% anomalies
        3. Trade count: Filter out coins with decreasing activity (>-20%)
        4. OBV scoring: Penalize OBV DOWN with -10 points (was neutral)
        5. Data validation: Range checks for all metrics before signal generation
        """

        # 24h ticker data
        ticker = self._get_24h_ticker(symbol)
        if not ticker:
            return None

        # 30 günlük klines (FİYAT BAĞLAMI için - ÇOK ÖNEMLİ!)
        klines_30d = self._get_klines(symbol, '1d', 30)
        if not klines_30d or len(klines_30d) < 30:
            return None

        # 7 günlük klines (volume ortalaması için)
        klines_7d = self._get_klines(symbol, '1d', 7)
        if not klines_7d or len(klines_7d) < 7:
            return None

        # Son 24h klines (OBV hesabı için)
        klines_1d = self._get_klines(symbol, '1h', 24)
        if not klines_1d or len(klines_1d) < 24:
            return None

        # === METRİK HESAPLAMA ===

        # 0. FİYAT BAĞLAMI (30 günlük değişim) - DISTRIBUTION FİLTRESİ!
        price_30d_ago = float(klines_30d[0][4])  # 30 gün önce close
        current_price = float(klines_30d[-1][4])  # şu anki close
        price_change_30d = ((current_price / price_30d_ago) - 1) * 100

        # 30 gün içinde max/min fiyat
        prices_30d = [float(k[2]) for k in klines_30d]  # high prices
        max_price_30d = max(prices_30d)
        min_price_30d = min([float(k[3]) for k in klines_30d])  # low prices

        # Mevcut fiyatın 30 günlük range'deki pozisyonu (0-100%)
        price_position = ((current_price - min_price_30d) / (max_price_30d - min_price_30d) * 100) if (max_price_30d - min_price_30d) > 0 else 50

        # 1. Hacim artışı (son 24h vs 7 gün ortalaması)
        volume_24h = float(ticker['quoteVolume'])
        volumes_7d = [float(k[5]) for k in klines_7d]  # quote volume
        avg_volume_7d = np.mean(volumes_7d)

        # VALIDATION: Skip if 7-day average is too low (prevents million% anomalies)
        MIN_AVG_VOLUME = 100000  # $100K minimum
        if avg_volume_7d < MIN_AVG_VOLUME:
            logger.debug(f"⚠️ {symbol} - Volume too low: ${avg_volume_7d:,.0f}")
            return None

        volume_increase = ((volume_24h / avg_volume_7d) - 1) * 100

        # VALIDATION: Cap extreme volume increases (data quality check)
        if volume_increase > 10000:  # >10,000% is likely data error
            logger.warning(f"⚠️ {symbol} - Extreme volume increase: {volume_increase:.0f}%")
            return None

        # 2. Fiyat değişimi (24h)
        price_change = float(ticker['priceChangePercent'])

        # 3. Alım baskısı (taker buy / total volume)
        # FIX: Index [10] is taker buy QUOTE volume (USDT), not [9] (base asset)
        buy_volumes = [float(k[10]) for k in klines_1d]  # taker buy quote volume (FIXED!)
        total_volumes = [float(k[7]) for k in klines_1d]  # quote volume
        buy_pressure = (sum(buy_volumes) / sum(total_volumes) * 100) if sum(total_volumes) > 0 else 0

        # VALIDATION: Buy pressure must be 0-100%
        if buy_pressure < 0 or buy_pressure > 100:
            logger.warning(f"⚠️ {symbol} - Invalid buy pressure: {buy_pressure:.1f}%")
            return None

        # 4. Trade count artışı
        trade_count_24h = float(ticker['count'])
        avg_trade_count_7d = np.mean([float(k[8]) for k in klines_7d])  # number of trades
        trade_count_increase = ((trade_count_24h / avg_trade_count_7d) - 1) * 100 if avg_trade_count_7d > 0 else 0

        # VALIDATION: Skip if trade count is decreasing (not accumulation)
        # Negative trade count increase means less activity = distribution or dead coin
        if trade_count_increase < -20:  # More than 20% decrease
            logger.debug(f"⚠️ {symbol} - Trade count decreasing: {trade_count_increase:.1f}%")
            return None

        # 5. OBV (On-Balance Volume) trendi
        obv_trend = self._calculate_obv_trend(klines_1d)

        # === DATA QUALITY VALIDATION ===
        # Ensure all metrics are within reasonable ranges before proceeding

        # Volume increase should be reasonable (not millions of %)
        if volume_increase < -50 or volume_increase > 5000:
            logger.debug(f"⚠️ {symbol} - Suspicious volume increase: {volume_increase:.1f}%")
            return None

        # Buy pressure already validated (0-100%)

        # Price change should be reasonable for 24h period
        if abs(price_change) > 100:  # >100% in 24h is extremely rare
            logger.debug(f"⚠️ {symbol} - Extreme price change: {price_change:.1f}%")
            return None

        # === DISTRIBUTION FİLTRESİ (ÇOK ÖNEMLİ!) ===

        # Eğer coin son 30 günde %30+ artmışsa ve şimdi tepede ise (>70%)
        # Bu DISTRIBUTION (satış), ACCUMULATION değil!
        if price_change_30d > 30 and price_position > 70:
            # Bu whale satışı - SKIP!
            return None

        # Eğer coin son 30 günde %50+ artmışsa, kesinlikle distribution
        if price_change_30d > 50:
            return None

        # === AKÜMüLASYON KRİTERLERİ ===

        criteria_met = []
        score = 0

        # Kriter 0: Fiyat bağlamı (YENİ - EN ÖNEMLİ!)
        # İdeal akümülasyon: Fiyat dip/orta bölgede (%20-50 arası)
        if 20 <= price_position <= 50:
            criteria_met.append(f"DipPos{price_position:.0f}%")
            score += 30  # ÇOK ÖNEMLLİ!
        elif price_position < 30:
            criteria_met.append(f"Dip{price_position:.0f}%")
            score += 40  # DİPTE - SÜPER GÜÇLÜ!

        # Son 30 günde sideways veya düşüş (<%20 değişim) - iyi sinyal
        if abs(price_change_30d) < 20:
            criteria_met.append(f"30dSide{price_change_30d:+.0f}%")
            score += 15

        # Kriter 1: Hacim artışı
        if volume_increase >= vol_threshold:
            criteria_met.append(f"Vol↑{volume_increase:.1f}%")
            score += 20  # Azalttık çünkü tek başına yeterli değil

        # Kriter 2: Fiyat yatay/düşüyor (24h)
        if abs(price_change) <= price_threshold:
            criteria_met.append(f"Price{price_change:+.1f}%")
            score += 15
        elif price_change < 0:  # Düşüyorsa
            criteria_met.append(f"Price{price_change:+.1f}%↓")
            score += 20

        # Kriter 3: Gizli alım baskısı
        if buy_min <= buy_pressure <= buy_max:
            criteria_met.append(f"Buy{buy_pressure:.1f}%")
            score += 20

        # Kriter 4: Trade count artışı
        if trade_count_increase >= trade_threshold:
            criteria_met.append(f"Trades↑{trade_count_increase:.1f}%")
            score += 10

        # Kriter 5: OBV trendi
        if obv_trend > 0:
            criteria_met.append(f"OBV↑")
            score += 5
        else:
            # OBV DOWN is a NEGATIVE signal for accumulation
            criteria_met.append(f"OBV↓")
            score -= 10  # Penalize heavily - this contradicts accumulation

        # === SİNYAL DEĞERLENDİRME ===

        # MUTLAKA fiyat bağlamı kriteri olmalı + en az 3 kriter daha
        has_price_context = any('Dip' in c or '30dSide' in c for c in criteria_met)

        if has_price_context and len(criteria_met) >= 3 and score >= 60:
            return {
                'symbol': symbol.replace('USDT', ''),
                'accumulation_score': score,
                'volume_increase': volume_increase,
                'price_change': price_change,
                'price_change_30d': price_change_30d,  # YENİ
                'price_position': price_position,       # YENİ
                'buy_pressure': buy_pressure,
                'trade_count_increase': trade_count_increase,
                'obv_trend': 'UP' if obv_trend > 0 else 'DOWN',
                'volume_24h': volume_24h,
                'criteria_met': criteria_met,
                'criteria_count': len(criteria_met),
                'signal_type': 'ACCUMULATION'  # Artık emin olabiliriz!
            }

        return None

    def _get_24h_ticker(self, symbol: str) -> Optional[Dict]:
        """24h ticker data"""
        try:
            url = f"{self.base_url}/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            response = self.session.get(url, params=params, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _get_klines(self, symbol: str, interval: str, limit: int) -> Optional[List]:
        """Kline (candlestick) data"""
        try:
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except:
            return None

    def _calculate_obv_trend(self, klines: List) -> float:
        """
        OBV (On-Balance Volume) trendi hesapla

        Pozitif = Hacim alım yönünde
        Negatif = Hacim satış yönünde
        """
        if not klines or len(klines) < 2:
            return 0

        obv = 0
        obv_values = []

        for i, kline in enumerate(klines):
            close = float(kline[4])
            volume = float(kline[7])  # quote volume

            if i > 0:
                prev_close = float(klines[i-1][4])
                if close > prev_close:
                    obv += volume
                elif close < prev_close:
                    obv -= volume

            obv_values.append(obv)

        # Son OBV ile orta nokta OBV'yi karşılaştır (trend yönü)
        if len(obv_values) >= 2:
            mid_point = len(obv_values) // 2
            recent_obv = np.mean(obv_values[-5:])  # Son 5 değer
            mid_obv = np.mean(obv_values[mid_point-2:mid_point+3])  # Orta 5 değer

            return recent_obv - mid_obv

        return 0

    def generate_report(self, result: Dict[str, Any], format: str = 'text') -> str:
        """Rapor oluştur"""
        if format == 'text':
            return self._format_text_report(result)
        elif format == 'html':
            return self._format_html_report(result)
        else:
            return self._format_text_report(result)

    def _format_text_report(self, result: Dict[str, Any]) -> str:
        """Text formatında rapor"""
        lines = [
            "=" * 70,
            "🔍 AKÜMÜLASYON TESPİT RAPORU",
            "💰 Gizli Toplanan Coinler - Fiyat Patlamasına Hazır Sinyaller",
            "=" * 70,
            "",
            f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"📊 Taranan Coin: {result['total_scanned']}",
            f"✅ Sinyal Sayısı: {result['signals_found']}",
            "",
            "🎯 Kriterler:",
            f"   - Hacim Artışı: {result['criteria']['volume_increase']}",
            f"   - Fiyat Değişimi: {result['criteria']['price_change']}",
            f"   - Alım Baskısı: {result['criteria']['buy_pressure']}",
            f"   - Trade Count: {result['criteria']['trade_count_increase']}",
            "",
            "=" * 70,
        ]

        if not result['signals']:
            lines.append("")
            lines.append("❌ Akümülasyon sinyali bulunamadı.")
            lines.append("💡 Kriterleri gevşeterek tekrar deneyin.")
        else:
            lines.append("")
            lines.append("🚀 AKÜMÜLASYON SİNYALLERİ (Yüksek → Düşük Skor)")
            lines.append("-" * 70)

            for i, signal in enumerate(result['signals'], 1):
                coin = signal['symbol']
                score = signal['accumulation_score']
                vol_inc = signal['volume_increase']
                price_ch = signal['price_change']
                price_ch_30d = signal.get('price_change_30d', 0)  # YENİ
                price_pos = signal.get('price_position', 50)      # YENİ
                buy_p = signal['buy_pressure']
                trade_inc = signal['trade_count_increase']
                vol_24h = signal['volume_24h']
                criteria = ', '.join(signal['criteria_met'])

                lines.append(f"\n{i}. {coin}")
                lines.append(f"   Skor: {score:.1f}/100 ⭐")
                lines.append(f"   Hacim 24h: ${vol_24h:,.0f}")
                lines.append(f"   Fiyat 30d: {price_ch_30d:+.1f}% | Pozisyon: {price_pos:.0f}% {'🟢DİP' if price_pos < 30 else '🟡ORTA' if price_pos < 60 else '🔴TEPE'}")
                lines.append(f"   Hacim Artışı: {vol_inc:+.1f}% {'🔥' if vol_inc > 100 else '📈'}")
                lines.append(f"   Fiyat 24h: {price_ch:+.1f}% {'✅' if abs(price_ch) < 3 else '📊'}")
                lines.append(f"   Alım Baskısı: {buy_p:.1f}% {'🟢' if 52 <= buy_p <= 58 else '🟡'}")
                lines.append(f"   Trade Count: {trade_inc:+.1f}% {'🔥' if trade_inc > 50 else '📈'}")
                lines.append(f"   OBV Trend: {signal['obv_trend']}")
                lines.append(f"   Kriterler: {criteria}")

        lines.append("")
        lines.append("=" * 70)
        lines.append("")
        lines.append("💡 NASIL KULLANILIR?")
        lines.append("   1. Yüksek skorlu coinleri takip et")
        lines.append("   2. Grafik analizi yap (destek seviyeleri)")
        lines.append("   3. Hacim patlaması bekle (breakout)")
        lines.append("   4. Risk yönetimi ile gir (stop-loss)")
        lines.append("")
        lines.append("⚠️  DİKKAT: Bu sadece bir sinyal! Kendi analizinizi yapın.")
        lines.append("=" * 70)

        return '\n'.join(lines)

    def _format_html_report(self, result: Dict[str, Any]) -> str:
        """HTML formatında rapor"""
        # TODO: Gelişmiş HTML raporu
        return self._format_text_report(result)


def main():
    """CLI kullanımı"""
    print("=" * 70)
    print("🔍 Akümülasyon Detector - Gizli Toplanan Coinleri Bul")
    print("=" * 70)
    print()
    print("🔄 Tarama başlıyor...")
    print("⏳ Bu 2-5 dakika sürebilir (200 coin taranıyor)...")
    print()

    detector = AccumulationDetector()
    result = detector.scan(
        min_volume_usd=500000,  # Min $500K volume
        max_coins=200,          # Top 200 coin
        volume_increase_threshold=50.0,   # %50+ hacim artışı
        price_change_threshold=5.0,       # Max %5 fiyat değişimi
        buy_pressure_min=52.0,            # Min %52 alım
        buy_pressure_max=60.0,            # Max %60 alım (çok yüksek olmamalı)
        trade_count_threshold=30.0        # %30+ trade count artışı
    )

    report = detector.generate_report(result, format='text')
    print(report)

    # Dosyaya kaydet
    filename = f"accumulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print()
    print(f"📄 Rapor kaydedildi: {filename}")
    print()


if __name__ == '__main__':
    main()
