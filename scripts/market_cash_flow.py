#!/usr/bin/env python3
"""
Market Cash Flow CLI Tool

Kullanım:
    python scripts/market_cash_flow.py
    python scripts/market_cash_flow.py --symbols BTCUSDT ETHUSDT
    python scripts/market_cash_flow.py --timeframe 1H --limit 200
    python scripts/market_cash_flow.py --json  # JSON çıktı
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.analysis.market_cash_flow import MarketCashFlowAnalyzer
except ImportError as e:
    print(f"❌ Import hatası: {e}")
    print("Gerekli paketleri yükleyin: pip install -r requirements.txt")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Market Cash Flow Analyzer - Nakit Akış Raporu",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--symbols',
        nargs='*',
        default=None,
        help='Analiz edilecek coinler (boş = tüm coinler)'
    )

    parser.add_argument(
        '--timeframe',
        default='15min',
        choices=['15min', '1H', '4H', '12H', '1D'],
        help='Zaman dilimi (default: 15min)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=500,
        help='Analiz edilecek candle sayısı (default: 500)'
    )

    parser.add_argument(
        '--data-dir',
        default='data',
        help='Veri klasörü (default: data)'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='JSON formatında çıktı ver'
    )

    args = parser.parse_args()

    print("🚀 Market Cash Flow Analyzer")
    print("=" * 60)
    print(f"📁 Veri klasörü: {args.data_dir}")
    print(f"⏱️  Zaman dilimi: {args.timeframe}")
    print(f"📊 Candle limiti: {args.limit}")
    if args.symbols:
        print(f"🎯 Coinler: {', '.join(args.symbols)}")
    else:
        print("🎯 Coinler: Tüm mevcut coinler")
    print("=" * 60)
    print()

    # Initialize analyzer
    analyzer = MarketCashFlowAnalyzer(data_dir=args.data_dir)

    # Run analysis
    print("🔍 Analiz başlatılıyor...")
    try:
        report = analyzer.analyze_market(
            symbols=args.symbols,
            base_timeframe=args.timeframe,
            limit=args.limit
        )
    except Exception as e:
        print(f"❌ Hata: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if report['status'] == 'error':
        print(f"❌ Hata: {report['message']}")
        sys.exit(1)

    print("✅ Analiz tamamlandı!\n")

    # Output
    if args.json:
        import json
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(report['text_report'])


if __name__ == '__main__':
    main()
