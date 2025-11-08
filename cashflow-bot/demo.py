"""
Demo script - Tüm format tiplerini test et

Bu script 3 farklı format tipini gösterir:
1. text - Basit text format
2. table - Tablo formatında (düzenli)
3. html - Browser'da açılabilir HTML raporu

Kullanım:
    python demo.py
"""

from cashflow_analyzer import CashFlowAnalyzer
from datetime import datetime

def main():
    print("=" * 60)
    print("📊 Market Cash Flow Analyzer - Format Demo")
    print("=" * 60)
    print()

    analyzer = CashFlowAnalyzer()

    # 1. Text Format
    print("🔹 1. TEXT FORMAT (Basit metin)")
    print("-" * 60)
    print("Analiz yapılıyor (top 10 coin)...")
    report_text = analyzer.analyze(top_n=10, timeframe='15m', format='text')

    if report_text['status'] == 'success':
        print("\n" + report_text['text_report'])
        print(f"\n✅ Text format başarılı! Marketteki Hacim Payı: %{report_text['market_share']:.1f}")
    else:
        print(f"❌ Hata: {report_text.get('message')}")

    print("\n" + "=" * 60)
    input("Enter tuşuna basarak devam edin (TABLE format)...")

    # 2. Table Format
    print("\n🔹 2. TABLE FORMAT (Tablo)")
    print("-" * 60)
    print("Analiz yapılıyor (top 10 coin)...")
    report_table = analyzer.analyze(top_n=10, timeframe='15m', format='table')

    if report_table['status'] == 'success':
        print("\n" + report_table['text_report'])
        print(f"\n✅ Table format başarılı! Marketteki Hacim Payı: %{report_table['market_share']:.1f}")
    else:
        print(f"❌ Hata: {report_table.get('message')}")

    print("\n" + "=" * 60)
    input("Enter tuşuna basarak devam edin (HTML format)...")

    # 3. HTML Format
    print("\n🔹 3. HTML FORMAT (Browser'da açılabilir)")
    print("-" * 60)
    print("Analiz yapılıyor (top 10 coin)...")
    report_html = analyzer.analyze(top_n=10, timeframe='15m', format='html')

    if report_html['status'] == 'success':
        # HTML dosyasını kaydet
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"cashflow_report_{timestamp}.html"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_html['text_report'])

        print(f"✅ HTML raporu oluşturuldu: {filename}")
        print(f"   Marketteki Hacim Payı: %{report_html['market_share']:.1f}")
        print(f"\n💡 Browser'da açmak için:")
        print(f"   - Windows: start {filename}")
        print(f"   - Mac: open {filename}")
        print(f"   - Linux: xdg-open {filename}")
        print(f"\n🎯 HTML'de coin isimlerinin üzerine gelin - tooltip'te USD hacim göreceksiniz!")
    else:
        print(f"❌ Hata: {report_html.get('message')}")

    print("\n" + "=" * 60)
    print("✅ Demo tamamlandı!")
    print("=" * 60)


if __name__ == '__main__':
    main()
