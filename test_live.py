#!/usr/bin/env python3
"""
Test Live Market Cash Flow Analyzer - Binance'den canlı veri çeker
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

def main():
    print("🚀 CANLI Market Cash Flow Testi")
    print("=" * 60)
    print("📡 Binance Futures API'den canlı veri çekiliyor...")
    print("⏳ Lütfen bekleyin (30-60 saniye sürebilir)...")
    print("=" * 60)
    print()

    # Initialize live analyzer
    analyzer = LiveMarketCashFlowAnalyzer()

    # Run analysis with live data
    report = analyzer.analyze_market(
        symbols=None,  # Auto-select top 30 coins
        timeframe='15m',
        limit=500,
        top_n=30
    )

    if report['status'] == 'error':
        print(f"❌ Hata: {report['message']}")
        return

    print("✅ Analiz tamamlandı!\n")
    print(report['text_report'])

    print("\n" + "=" * 60)
    print("📊 JSON Özeti:")
    print(f"  - Veri Kaynağı: {report.get('data_source', 'unknown')}")
    print(f"  - Risk Seviyesi: {report['risk_assessment']['level']}")
    print(f"  - Kısa Vadeli Güç: {report['market_metrics']['short_term_power']}X")
    print(f"  - Toplam Coin: {report['total_coins']}")
    print(f"  - Market Payı (Top 30): {report['market_metrics']['market_volume_share']}%")

    print("\n💰 İlk 5 Coin:")
    for i, coin in enumerate(report['top_flows'][:5], 1):
        print(f"  {i}. {coin['symbol']}: {coin['cash_share']:.1f}% "
              f"(15m: {coin['buyer_15m']:.1f}%, momentum: {coin['momentum']:.2f})")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ İşlem kullanıcı tarafından iptal edildi")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
