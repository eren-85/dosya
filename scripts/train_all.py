#!/usr/bin/env python3
"""
Train All Models Script

Bu script tüm ML modellerini (XGBoost, LSTM, PPO) tek komutla eğitir.

Kullanım:
    # Tüm modelleri eğit
    python scripts/train_all.py --symbol BTCUSDT --timeframe 1d

    # Sadece belirli modelleri eğit
    python scripts/train_all.py --symbol BTCUSDT --timeframe 1d --models xgboost,lstm

    # Birden fazla sembol
    python scripts/train_all.py --symbols BTCUSDT,ETHUSDT --timeframe 1d

    # GPU kullan
    python scripts/train_all.py --symbol BTCUSDT --timeframe 1d --use-gpu

Özellikler:
    ✅ Hata yönetimi - Her model için ayrı try-catch
    ✅ Veri kontrolü - Dosya varlığı kontrol edilir
    ✅ İlerleme takibi - Her adım raporlanır
    ✅ Özet rapor - Başarılı/başarısız eğitimler
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import json

# Renkli terminal çıktısı için
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text):
    """Başlık yazdır"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text):
    """Başarı mesajı"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")


def print_error(text):
    """Hata mesajı"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_warning(text):
    """Uyarı mesajı"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_info(text):
    """Bilgi mesajı"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")


def check_data_exists(symbol, timeframe, data_dir='data/historical'):
    """
    Veri dosyasının varlığını kontrol et

    Returns:
        (exists: bool, filepath: Path)
    """
    data_dir = Path(data_dir)

    # Önce parquet'i dene
    parquet_file = data_dir / f"{symbol}_{timeframe}_futures.parquet"
    if parquet_file.exists():
        return True, parquet_file

    # Sonra CSV'yi dene
    csv_file = data_dir / f"{symbol}_{timeframe}_futures.csv"
    if csv_file.exists():
        return True, csv_file

    return False, None


def train_xgboost(symbol, timeframe, data_dir, output_dir, task='trend_classification'):
    """XGBoost modelini eğit"""
    print_info(f"XGBoost eğitimi başlatılıyor... (Task: {task})")

    cmd = [
        sys.executable, '-m', 'backend.training.train_xgboost',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--task', task,
        '--n-estimators', '300',
        '--max-depth', '6',
        '--lr', '0.1',
        '--data-dir', data_dir,
        '--output-dir', output_dir
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success(f"XGBoost ({task}) eğitimi tamamlandı!")
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print_error(f"XGBoost ({task}) eğitimi başarısız!")
        print(f"   Hata: {error_msg[:200]}...")
        return False, error_msg
    except Exception as e:
        print_error(f"XGBoost ({task}) eğitimi başarısız!")
        print(f"   Beklenmeyen hata: {str(e)}")
        return False, str(e)


def train_lstm(symbol, timeframe, data_dir, output_dir, epochs=100, use_gpu=False):
    """LSTM modelini eğit"""
    print_info(f"LSTM eğitimi başlatılıyor... (Epochs: {epochs})")

    cmd = [
        sys.executable, '-m', 'backend.training.train_lstm',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--epochs', str(epochs),
        '--batch-size', '32',
        '--seq-length', '60',
        '--hidden-size', '128',
        '--num-layers', '2',
        '--lr', '0.001',
        '--data-dir', data_dir,
        '--output-dir', output_dir
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success(f"LSTM eğitimi tamamlandı!")
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print_error(f"LSTM eğitimi başarısız!")
        print(f"   Hata: {error_msg[:200]}...")
        return False, error_msg
    except Exception as e:
        print_error(f"LSTM eğitimi başarısız!")
        print(f"   Beklenmeyen hata: {str(e)}")
        return False, str(e)


def train_ppo(symbol, timeframe, data_dir, output_dir, episodes=1000, use_gpu=False):
    """PPO modelini eğit"""
    print_info(f"PPO eğitimi başlatılıyor... (Episodes: {episodes})")

    cmd = [
        sys.executable, '-m', 'backend.training.train_ppo',
        '--symbol', symbol,
        '--timeframe', timeframe,
        '--episodes', str(episodes),
        '--data-dir', data_dir,
        '--output-dir', output_dir
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print_success(f"PPO eğitimi tamamlandı!")
        return True, None
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print_error(f"PPO eğitimi başarısız!")
        print(f"   Hata: {error_msg[:200]}...")
        return False, error_msg
    except FileNotFoundError:
        print_warning("PPO eğitim scripti bulunamadı, atlanıyor...")
        return False, "Script not found"
    except Exception as e:
        print_error(f"PPO eğitimi başarısız!")
        print(f"   Beklenmeyen hata: {str(e)}")
        return False, str(e)


def generate_report(results, output_dir):
    """Eğitim sonuçlarını özetle"""
    print_header("EĞİTİM RAPORU")

    total_models = len(results)
    successful = sum(1 for r in results if r['success'])
    failed = total_models - successful

    print(f"📊 Toplam Model: {total_models}")
    print(f"{Colors.OKGREEN}✅ Başarılı: {successful}{Colors.ENDC}")
    print(f"{Colors.FAIL}❌ Başarısız: {failed}{Colors.ENDC}")
    print()

    # Detaylar
    print("Detaylar:")
    print("-" * 70)
    for r in results:
        status = f"{Colors.OKGREEN}✅{Colors.ENDC}" if r['success'] else f"{Colors.FAIL}❌{Colors.ENDC}"
        print(f"  {status} {r['model']:15s} | {r['symbol']:10s} | {r['timeframe']:5s}")
        if not r['success'] and r.get('error'):
            print(f"      {Colors.FAIL}└─ Hata: {r['error'][:60]}...{Colors.ENDC}")

    # JSON raporu kaydet
    report_file = Path(output_dir) / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"📄 Detaylı rapor: {report_file}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Tüm ML modellerini eğit',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # Tek sembol, tüm modeller
  python scripts/train_all.py --symbol BTCUSDT --timeframe 1d

  # Birden fazla sembol
  python scripts/train_all.py --symbols BTCUSDT,ETHUSDT --timeframe 1d

  # Sadece XGBoost ve LSTM
  python scripts/train_all.py --symbol BTCUSDT --timeframe 1d --models xgboost,lstm

  # GPU kullan
  python scripts/train_all.py --symbol BTCUSDT --timeframe 1d --use-gpu
        """
    )

    # Ana parametreler
    parser.add_argument('--symbol', type=str, help='Tek sembol (örn: BTCUSDT)')
    parser.add_argument('--symbols', type=str, help='Birden fazla sembol, virgülle ayrılmış (örn: BTCUSDT,ETHUSDT)')
    parser.add_argument('--timeframe', type=str, default='1d', help='Timeframe (örn: 1h, 4h, 1d)')

    # Model seçimi
    parser.add_argument('--models', type=str, default='xgboost,lstm',
                       help='Eğitilecek modeller, virgülle ayrılmış (xgboost,lstm,ppo)')

    # Model parametreleri
    parser.add_argument('--epochs', type=int, default=50, help='LSTM epoch sayısı')
    parser.add_argument('--episodes', type=int, default=1000, help='PPO episode sayısı')
    parser.add_argument('--use-gpu', action='store_true', help='GPU kullan')

    # Dizinler
    parser.add_argument('--data-dir', type=str, default='data/historical', help='Veri dizini')
    parser.add_argument('--output-dir', type=str, default='models/trained', help='Model çıktı dizini')

    args = parser.parse_args()

    # Sembolleri belirle
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(',')]
    elif args.symbol:
        symbols = [args.symbol]
    else:
        print_error("En az bir sembol belirtmelisiniz! (--symbol veya --symbols)")
        parser.print_help()
        sys.exit(1)

    # Modelleri belirle
    available_models = ['xgboost', 'lstm', 'ppo']
    selected_models = [m.strip().lower() for m in args.models.split(',')]

    # Geçersiz modelleri kontrol et
    invalid_models = [m for m in selected_models if m not in available_models]
    if invalid_models:
        print_error(f"Geçersiz model(ler): {invalid_models}")
        print_info(f"Geçerli modeller: {available_models}")
        sys.exit(1)

    # Başlık
    print_header("🤖 TÜM MODELLER İÇİN EĞİTİM BAŞLATILIYOR")

    print(f"📋 Ayarlar:")
    print(f"   Semboller: {', '.join(symbols)}")
    print(f"   Timeframe: {args.timeframe}")
    print(f"   Modeller: {', '.join(selected_models)}")
    print(f"   LSTM Epochs: {args.epochs}")
    print(f"   PPO Episodes: {args.episodes}")
    print(f"   GPU: {'Evet' if args.use_gpu else 'Hayır'}")
    print(f"   Veri Dizini: {args.data_dir}")
    print(f"   Çıktı Dizini: {args.output_dir}")
    print()

    # Çıktı dizinini oluştur
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    # Eğitim sonuçları
    results = []

    # Her sembol için
    for symbol in symbols:
        print_header(f"📊 {symbol} - {args.timeframe}")

        # Veri dosyasını kontrol et
        data_exists, data_file = check_data_exists(symbol, args.timeframe, args.data_dir)

        if not data_exists:
            print_error(f"Veri dosyası bulunamadı: {symbol}_{args.timeframe}_futures.parquet/csv")
            print_warning("Bu sembolu atlıyorum...")

            # Tüm modeller için başarısız kaydet
            for model in selected_models:
                results.append({
                    'symbol': symbol,
                    'timeframe': args.timeframe,
                    'model': model,
                    'success': False,
                    'error': 'Data file not found'
                })
            continue

        print_success(f"Veri dosyası bulundu: {data_file}")
        print()

        # XGBoost
        if 'xgboost' in selected_models:
            print(f"\n{Colors.BOLD}[1/X] XGBoost Eğitimi{Colors.ENDC}")
            print("-" * 70)

            # Trend classification
            success, error = train_xgboost(
                symbol, args.timeframe,
                args.data_dir, args.output_dir,
                task='trend_classification'
            )
            results.append({
                'symbol': symbol,
                'timeframe': args.timeframe,
                'model': 'xgboost_trend',
                'success': success,
                'error': error
            })

            # Pattern classification (opsiyonel)
            # Uncomment if you want pattern classification too
            # success, error = train_xgboost(
            #     symbol, args.timeframe,
            #     args.data_dir, args.output_dir,
            #     task='pattern_classification'
            # )
            # results.append({
            #     'symbol': symbol,
            #     'timeframe': args.timeframe,
            #     'model': 'xgboost_pattern',
            #     'success': success,
            #     'error': error
            # })

        # LSTM
        if 'lstm' in selected_models:
            print(f"\n{Colors.BOLD}[2/X] LSTM Eğitimi{Colors.ENDC}")
            print("-" * 70)

            success, error = train_lstm(
                symbol, args.timeframe,
                args.data_dir, args.output_dir,
                epochs=args.epochs,
                use_gpu=args.use_gpu
            )
            results.append({
                'symbol': symbol,
                'timeframe': args.timeframe,
                'model': 'lstm',
                'success': success,
                'error': error
            })

        # PPO
        if 'ppo' in selected_models:
            print(f"\n{Colors.BOLD}[3/X] PPO Eğitimi{Colors.ENDC}")
            print("-" * 70)

            success, error = train_ppo(
                symbol, args.timeframe,
                args.data_dir, args.output_dir,
                episodes=args.episodes,
                use_gpu=args.use_gpu
            )
            results.append({
                'symbol': symbol,
                'timeframe': args.timeframe,
                'model': 'ppo',
                'success': success,
                'error': error
            })

    # Raporu göster
    generate_report(results, args.output_dir)

    # Başarı durumuna göre exit code
    if any(r['success'] for r in results):
        print_success("Eğitim süreci tamamlandı!")
        sys.exit(0)
    else:
        print_error("Tüm eğitimler başarısız oldu!")
        sys.exit(1)


if __name__ == '__main__':
    main()
