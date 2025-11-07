"""
Multi-Everything Data Downloader
Downloads data for multiple coins, timeframes, markets, and exchanges

Usage:
    python scripts/download_all.py

Configuration:
    Edit the CONFIGS section below to customize your downloads
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Fix Windows encoding issue (support emojis in print)
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import subprocess
import time
from datetime import datetime
from typing import List, Dict
import json

# ============================================
# CONFIGURATION
# ============================================

CONFIGS = {
    # Coins to download
    "symbols": [
        "BTCUSDT",
        "ETHUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "LINKUSDT",
        "LTCUSDT",
        "ARBUSDT",
        "DOTUSDT",
        "ATOMUSDT",
        "OPUSDT",
        "XLMUSDT",
        "SEIUSDT",
        "STRKUSDT",
        "ADAUSDT",
        "AVAXUSDT",
        "EIGENUSDT",
        "ETHFIUSDT",
        "DOGEUSDT",
        "TIAUSDT",
        "FETUSDT",
        "INJUSDT",
        "NEARUSDT",
    ],

    # Timeframes
    "timeframes": [
        "5m",
        "15m",
        "30m",
        "1h",
        "4h",
        "1d",
        "1w",
        "1M",
    ],

    # Market types
    "markets": [
        "spot",
        "futures",
    ],

    # Exchanges
    "exchanges": ["binance"],

    # Start date (auto = earliest available)
    "start_date": "auto",

    # Parallel workers (per download task)
    "max_workers": 3,

    # Output directory
    "output_dir": "data/advanced",
}

# ============================================
# DOWNLOAD LOGIC
# ============================================

def run_download(symbols: List[str], timeframe: str, market: str,
                exchanges: List[str], start_date: str, max_workers: int) -> Dict:
    """
    Run single download task

    Returns:
        dict with status, elapsed time, and details
    """
    start_time = time.time()

    # Build command with -u flag for unbuffered output (shows progress bars)
    cmd = [
        "python", "-u", "-m", "backend.data.advanced_collector",
        "--symbols", ",".join(symbols),
        "--timeframe", timeframe,
        "--market", market,
        "--exchanges", ",".join(exchanges),
        "--start-date", start_date,
        "--parallel",
        "--max-workers", str(max_workers),
    ]

    print(f"\n{'='*80}")
    print(f"📥 Downloading: {', '.join(symbols)} | {timeframe} | {market.upper()}")
    print(f"{'='*80}")

    try:
        # Use Popen for real-time output (shows progress bars)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',  # Decode subprocess output as UTF-8
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time with flush
        output_lines = []
        for line in process.stdout:
            print(line, end='', flush=True)  # Print immediately with flush
            output_lines.append(line)

        # Wait for completion
        return_code = process.wait(timeout=3600)

        elapsed = time.time() - start_time
        output = ''.join(output_lines)

        if return_code == 0:
            # Parse output for success count
            success_count = 0
            for line in output_lines:
                if 'Success:' in line:
                    # Extract "Success: X/Y"
                    parts = line.split('Success:')
                    if len(parts) > 1:
                        success_str = parts[1].strip().split('/')[0].strip()
                        try:
                            success_count = int(success_str)
                        except:
                            pass

            return {
                "status": "success",
                "elapsed": elapsed,
                "symbols": symbols,
                "timeframe": timeframe,
                "market": market,
                "success_count": success_count or len(symbols),
            }
        else:
            return {
                "status": "failed",
                "elapsed": elapsed,
                "symbols": symbols,
                "timeframe": timeframe,
                "market": market,
                "error": output[:200] if output else "Unknown error",
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "elapsed": time.time() - start_time,
            "symbols": symbols,
            "timeframe": timeframe,
            "market": market,
        }
    except Exception as e:
        return {
            "status": "error",
            "elapsed": time.time() - start_time,
            "symbols": symbols,
            "timeframe": timeframe,
            "market": market,
            "error": str(e),
        }


def main():
    """Main download orchestrator"""

    print("\n" + "="*80)
    print("🚀 MULTI-EVERYTHING DATA DOWNLOADER")
    print("="*80)
    print(f"📊 Symbols: {', '.join(CONFIGS['symbols'])}")
    print(f"⏰ Timeframes: {', '.join(CONFIGS['timeframes'])}")
    print(f"🏪 Markets: {', '.join(CONFIGS['markets'])}")
    print(f"🌐 Exchanges: {', '.join(CONFIGS['exchanges'])}")
    print(f"📅 Start date: {CONFIGS['start_date']}")
    print("="*80 + "\n")

    # Calculate total tasks
    total_tasks = len(CONFIGS['timeframes']) * len(CONFIGS['markets'])
    print(f"📋 Total tasks: {total_tasks}")
    print(f"📦 Total symbols: {len(CONFIGS['symbols'])}")
    print(f"🔄 Parallel workers per task: {CONFIGS['max_workers']}\n")

    input("Press ENTER to start downloads...")

    results = []
    start_time = time.time()

    task_num = 0
    for timeframe in CONFIGS['timeframes']:
        for market in CONFIGS['markets']:
            task_num += 1

            print(f"\n{'='*80}")
            print(f"📊 TASK {task_num}/{total_tasks}: {timeframe} | {market.upper()}")
            print(f"{'='*80}")

            result = run_download(
                symbols=CONFIGS['symbols'],
                timeframe=timeframe,
                market=market,
                exchanges=CONFIGS['exchanges'],
                start_date=CONFIGS['start_date'],
                max_workers=CONFIGS['max_workers'],
            )

            results.append(result)

            # Print result
            if result['status'] == 'success':
                print(f"✅ SUCCESS in {result['elapsed']:.1f}s - {result.get('success_count', 0)}/{len(CONFIGS['symbols'])} symbols")
            else:
                print(f"❌ FAILED: {result['status']} - {result.get('error', 'Unknown error')}")

    # Final summary
    total_elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("📊 DOWNLOAD SUMMARY")
    print("="*80)

    success_count = sum(1 for r in results if r['status'] == 'success')
    failed_count = len(results) - success_count

    print(f"✅ Success: {success_count}/{total_tasks}")
    print(f"❌ Failed: {failed_count}/{total_tasks}")
    print(f"⏱️  Total time: {total_elapsed/60:.1f} minutes")
    print(f"📁 Output directory: {CONFIGS['output_dir']}/")

    # Detailed results
    print(f"\n{'='*80}")
    print("DETAILED RESULTS:")
    print(f"{'='*80}")

    for i, result in enumerate(results, 1):
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} Task {i}: {result['timeframe']} | {result['market'].upper()} | "
              f"{result['elapsed']:.1f}s | {result['status']}")

    # Save results to JSON
    results_file = Path(CONFIGS['output_dir']) / f"download_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)

    with open(results_file, 'w') as f:
        json.dump({
            'config': CONFIGS,
            'total_elapsed': total_elapsed,
            'results': results,
        }, f, indent=2)

    print(f"\n💾 Results saved to: {results_file}")
    print(f"\n{'='*80}")
    print("🎉 DOWNLOAD COMPLETE!")
    print(f"{'='*80}\n")

    return success_count == total_tasks


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
