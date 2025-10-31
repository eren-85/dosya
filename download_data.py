#!/usr/bin/env python3
"""
Simple data downloader without Docker dependencies

Usage:
    python download_data.py BTCUSDT 1h futures
    python download_data.py ETHUSDT 4h spot
    python download_data.py BTCUSDT,ETHUSDT 1d futures  # Multiple symbols
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def main():
    if len(sys.argv) < 4:
        print("Usage: python download_data.py SYMBOL(S) INTERVAL MARKET")
        print("Examples:")
        print("  python download_data.py BTCUSDT 1h futures")
        print("  python download_data.py ETHUSDT 4h spot")
        print("  python download_data.py BTCUSDT,ETHUSDT,BNBUSDT 1d futures")
        sys.exit(1)

    symbols_str = sys.argv[1]
    interval = sys.argv[2]
    market = sys.argv[3]

    # Parse symbols
    symbols = [s.strip().upper() for s in symbols_str.split(',')]

    print(f"📥 Downloading data:")
    print(f"   Symbols: {', '.join(symbols)}")
    print(f"   Interval: {interval}")
    print(f"   Market: {market}")
    print()

    try:
        from historical_sync import sync_historical

        results = sync_historical(
            symbols=symbols,
            interval=interval,
            market=market,
            base_dir="data/historical",
            parquet=True,
            all_time=False  # Resume from last sync
        )

        print("\n" + "="*60)
        print("✅ Download completed!")
        print("="*60)

        for sym, first_ms, last_ms, added in results:
            if added > 0:
                print(f"✅ {sym}: Added {added} candles")
            else:
                print(f"✅ {sym}: Already up to date")

        print("\n💡 Now restart your Docker containers:")
        print("   docker-compose restart backend")

    except ImportError as e:
        print(f"❌ Error: {e}")
        print("Make sure you have required packages:")
        print("   pip install pandas pyarrow requests tqdm")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
