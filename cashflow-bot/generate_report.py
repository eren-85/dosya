"""
HTML Rapor Olusturucu

cf.html dosyasina Market Cash Flow raporu olusturur ve browser'da acar.
Her calistirdiginda yeni veri ceker, ayni dosyaya kaydeder.

Kullanim:
    python generate_report.py

    veya

    python generate_report.py --coins 50 --format table
"""

import sys
import webbrowser
import os
from cashflow_analyzer import CashFlowAnalyzer
from datetime import datetime

def main():
    # Parametreler
    top_n = 30
    format_type = 'html'

    # Komut satiri argumanlari
    if '--coins' in sys.argv:
        try:
            idx = sys.argv.index('--coins')
            top_n = int(sys.argv[idx + 1])
        except:
            pass

    if '--format' in sys.argv:
        try:
            idx = sys.argv.index('--format')
            format_type = sys.argv[idx + 1]
        except:
            pass

    print("=" * 60)
    print("📊 Market Cash Flow - HTML Rapor Olusturucu")
    print("=" * 60)
    print()
    print(f"⚙️  Ayarlar:")
    print(f"   - Top N Coins: {top_n}")
    print(f"   - Format: {format_type}")
    print()
    print("🔄 Binance'den canli veri cekiliyor...")
    print("⏳ Bu 30-45 saniye surebilir...")
    print()

    # Analiz
    analyzer = CashFlowAnalyzer()
    report = analyzer.analyze(top_n=top_n, timeframe='15m', format=format_type)

    if report['status'] != 'success':
        print(f"❌ HATA: {report.get('message', 'Bilinmeyen hata')}")
        input("\nDevam etmek icin Enter'a basin...")
        return 1

    # Dosyaya kaydet
    if format_type == 'html':
        filename = 'cf.html'
        content = report['text_report']
    elif format_type == 'table':
        filename = 'cf_table.txt'
        content = report['text_report']
    else:
        filename = 'cf_report.txt'
        content = report['text_report']

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ Rapor olusturuldu!")
        print(f"   Dosya: {filename}")
        print(f"   Risk: {report['risk_assessment']['level'].upper()}")
        print(f"   Top 10 Dominance: %{report['top_10_dominance']:.1f}")
        print(f"   Toplam Coin: {report['total_coins']}")
        print(f"   Zaman: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Browser'da ac (sadece HTML icin)
        if format_type == 'html':
            print("🌐 Browser'da aciliyor...")
            abs_path = os.path.abspath(filename)
            webbrowser.open(f'file://{abs_path}')
            print(f"✅ Acildi: {abs_path}")
            print()
            print("💡 IPUCU:")
            print("   - Coin isimlerin uzerine gelin -> USD hacim gorursunuz")
            print("   - Sayfayi bookmark yapin!")
            print("   - Her calistirdiginda cf.html guncellenecek")
            print("   - Browser'da F5 ile yenileyebilirsiniz")
        else:
            print(f"📄 Rapor hazir: {os.path.abspath(filename)}")
            print(f"   Dosyayi text editor ile acabilirsiniz")

    except Exception as e:
        print(f"❌ DOSYA YAZMA HATASI: {e}")
        return 1

    print()
    print("=" * 60)
    input("Devam etmek icin Enter'a basin...")
    return 0


if __name__ == '__main__':
    sys.exit(main())
