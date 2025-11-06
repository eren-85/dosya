"""
CLI entry point for backend operations
Supports: download, sync, train commands
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def download_command(args):
    """Download historical data from Binance"""
    from backend.data.downloader import download_historical_data

    symbols = args.s.split(',') if args.s else []
    market = args.m or 'spot'
    interval = args.i or '1d'

    print(f"📥 Downloading {market} data for {symbols} at {interval} interval")

    for symbol in symbols:
        symbol = symbol.strip().upper()
        try:
            download_historical_data(
                symbol=symbol,
                interval=interval,
                market_type=market,
                all_time=args.all_time,
                start_date=args.start_date,
                end_date=args.end_date,
                use_parquet=args.parquet
            )
            print(f"✅ {symbol} downloaded successfully")
        except Exception as e:
            print(f"❌ {symbol} failed: {e}")


def sync_command(args):
    """Sync existing data (update to latest)"""
    print("⚠️  Sync command not implemented yet")
    print("Use 'download' command instead")


def train_command(args):
    """Train ML models"""
    print("⚠️  Train command not implemented yet")
    print("Use training scripts directly: backend/training/")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Backend CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Download command
    download_parser = subparsers.add_parser('download', help='Download historical data')
    download_parser.add_argument('-s', type=str, required=True, help='Symbols (comma-separated)')
    download_parser.add_argument('-i', type=str, default='1d', help='Interval (1m, 5m, 1h, 1d, etc.)')
    download_parser.add_argument('-m', type=str, default='spot', help='Market type (spot/futures)')
    download_parser.add_argument('--all-time', action='store_true', help='Download all available data')
    download_parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    download_parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    download_parser.add_argument('--parquet', action='store_true', help='Save as parquet')
    download_parser.set_defaults(func=download_command)

    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync existing data')
    sync_parser.add_argument('-s', type=str, required=True, help='Symbols (comma-separated)')
    sync_parser.add_argument('-i', type=str, default='1d', help='Interval')
    sync_parser.add_argument('-m', type=str, default='spot', help='Market type')
    sync_parser.add_argument('--parquet', action='store_true', help='Use parquet')
    sync_parser.set_defaults(func=sync_command)

    # Train command
    train_parser = subparsers.add_parser('train', help='Train ML models')
    train_parser.add_argument('-s', type=str, required=True, help='Symbols (comma-separated)')
    train_parser.add_argument('-t', type=str, required=True, help='Timeframes (comma-separated)')
    train_parser.set_defaults(func=train_command)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Call the appropriate function
    args.func(args)


if __name__ == '__main__':
    main()
