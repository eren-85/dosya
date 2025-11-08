# 🪟 Windows'ta Market Cash Flow Nasıl Çalıştırılır?

## ✅ Haklıydınız!

**Sorunuz:** "bunun için anlık veri çekip bakması gerekmiyor mu neden mum indirmesi gerekiyor?"

**Cevabınız:** Kesinlikle doğru! Artık **Binance'den anlık canlı veri çekiyor!** 🎉

---

## 🚀 Windows'ta Test (5 Adım)

### 1. Repoyu Klonlayın veya İndirin

```powershell
# PowerShell'de
cd D:\
git clone https://github.com/eren-85/dosya.git cashflow
cd cashflow

# veya ZIP olarak indirip çıkartın
```

### 2. Gerekli Paketleri Yükleyin

```powershell
# Python 3.11+ olduğundan emin olun
python --version

# Gerekli paketler
pip install pandas numpy pyarrow requests
```

### 3. Canlı Testi Çalıştırın

```powershell
# Canlı veri ile test (Binance'den çeker)
python test_live.py
```

**BEKLENTİ:**
- 📡 Top 30 coin otomatik seçilir
- ⏳ 30-60 saniye sürer
- ✅ Canlı rapor gösterir

**ÇIKTI:**
```
🚀 CANLI Market Cash Flow Testi
============================================================
📡 Binance Spot API'den canlı veri çekiliyor...
⏳ Lütfen bekleyin (30-60 saniye sürebilir)...
============================================================

✅ Analiz tamamlandı!

============================================================
📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu
🔴 CANLI VERİ - Binance Spot
============================================================

Kısa Vadeli Market Alım Gücü: 1.2X
Marketteki Hacim Payı: %85.3

15m=> %52.3 🔼
1h=> %48.7 🔻
4h=> %51.2 🔼
12h=> %49.8 🔻
1d=> %50.5 🔼

------------------------------------------------------------
BTC Nakit: %35.2 15m:%54 Mts: 1.1 🔼🔻🔼🔻🔼
ETH Nakit: %19.1 15m:%48 Mts: 0.9 🔻🔻🔻🔻🔻
SOL Nakit: %5.3 15m:%61 Mts: 1.3 🔼🔼🔼🔻🔼
BNB Nakit: %3.1 15m:%45 Mts: 0.8 🔻🔻🔻🔻🔻
XRP Nakit: %2.8 15m:%58 Mts: 1.2 🔼🔼🔼🔼🔼
...
------------------------------------------------------------
Piyasa düşük risk seviyesinde. Alım yapılabilir.
📅 Rapor Zamanı: 2025-11-08 15:30:45
============================================================
```

### 4. Telegram Botunuza Entegre Edin

#### Seçenek A: API ile (Önerilir)

```powershell
# Terminal 1: API'yi başlat
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: Test et
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"text\"}"
```

#### Seçenek B: Python ile Direkt

```python
# bot.py
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Canlı market analizi"""
    await update.message.reply_text("📊 Canlı veri çekiliyor...")

    # Canlı analiz
    analyzer = LiveMarketCashFlowAnalyzer()
    report = analyzer.analyze_market(
        symbols=None,      # Top 30 otomatik
        timeframe='15m',
        top_n=30
    )

    if report['status'] == 'success':
        # Text raporu al
        text = report['text_report']

        # Telegram'a gönder
        await update.message.reply_text(
            f"<pre>{text}</pre>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(f"❌ Hata: {report['message']}")

# Bot setup
app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("cashflow", cashflow))

print("🤖 Bot başlatılıyor (canlı veri modu)...")
app.run_polling()
```

### 5. Botunuzdan Kullanın

```
Telegram'da:
/cashflow

Bot yanıt verir:
📊 Canlı veri çekiliyor...

(30 saniye sonra)
[Market nakit akış raporunu gösterir]
```

---

## 🎯 Hızlı Python Örneği

```python
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

# Analyzer oluştur
analyzer = LiveMarketCashFlowAnalyzer()

# Canlı analiz yap
report = analyzer.analyze_market()

# Raporu göster
print(report['text_report'])

# JSON veriye eriş
print(f"\nRisk Seviyesi: {report['risk_assessment']['level']}")
print(f"Alım Gücü: {report['market_metrics']['short_term_power']}X")
```

---

## ⚙️ Parametreler

```python
report = analyzer.analyze_market(
    symbols=None,       # None = Top 30 otomatik seçilir
                        # veya ["BTCUSDT", "ETHUSDT", ...]

    timeframe='15m',    # Candle aralığı: 15m, 1h, 4h, 12h, 1d

    limit=500,          # Kaç candle analiz edilecek (max 1000)

    top_n=30            # Otomatik seçimde kaç coin (5-50 arası)
)
```

---

## 💡 Avantajlar

### ✅ Artık Gerekmiyor:
- ❌ Parquet dosyası indirmek
- ❌ Veri saklamak
- ❌ Veri güncellemek
- ❌ API Key almak

### ✅ Şimdi:
- ✅ Her seferinde güncel canlı veri
- ✅ Otomatik top coin seçimi
- ✅ Direkt Telegram/Discord entegrasyonu
- ✅ Sadece `pip install` yeterli

---

## 🔧 API ile Kullanım (Windows)

### API Başlat:
```powershell
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### Test Et:
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:8000/api/analysis/cash-flow" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"live": true, "format": "text", "top_n": 30}'

# veya curl varsa
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"text\"}"
```

### Swagger Docs:
Tarayıcıda açın: http://localhost:8000/docs

---

## 📊 Örnek Senaryolar

### Senaryo 1: Basit Test
```python
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market()
print(report['text_report'])
```

### Senaryo 2: Belirli Coinler
```python
analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market(
    symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
    timeframe='1h'
)
print(report['text_report'])
```

### Senaryo 3: 1 Saatlik Mumlarla Top 20
```python
analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market(
    timeframe='1h',
    top_n=20,
    limit=300
)
print(report['text_report'])
```

### Senaryo 4: JSON Veri ile Çalışma
```python
analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market()

# Risk kontrolü
if report['risk_assessment']['level'] == 'high':
    print("⚠️ Yüksek risk! Alım yapma!")
elif report['risk_assessment']['level'] == 'low':
    print("✅ Düşük risk. Alım yapılabilir.")

# Top 5 coin
for coin in report['top_flows'][:5]:
    print(f"{coin['symbol']}: {coin['cash_share']:.1f}% - {coin['indicators']}")
```

---

## ⚡ Performans

| Coin Sayısı | Süre |
|-------------|------|
| 10 coin | ~10-15 saniye |
| 20 coin | ~20-30 saniye |
| 30 coin | ~30-45 saniye |
| 50 coin | ~50-75 saniye |

**İpucu**: Hızlı yanıt için `top_n=20` kullanın.

---

## 🐛 Sorun Giderme

### Problem: ModuleNotFoundError
```powershell
pip install pandas numpy pyarrow requests
```

### Problem: "403 Forbidden"
**Sebep**: Bazı kurumsal networkler Binance'ı engelliyor olabilir.

**Çözüm**:
- Ev internetinizden deneyin
- VPN kullanın
- Mobil hotspot kullanın

### Problem: Yavaş Yanıt
```python
# top_n'i azaltın
report = analyzer.analyze_market(top_n=15)

# veya limit'i azaltın
report = analyzer.analyze_market(limit=300)
```

---

## 🎉 Özet

Artık **veri indirmeye gerek yok!**

### Eski Yöntem:
```
1. Veri indir ❌
2. Parquet kaydet ❌
3. Dosyadan oku ❌
4. Eski veriyle analiz ❌
```

### Yeni Yöntem:
```python
analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market()
print(report['text_report'])
✅ CANLI VERİ!
```

**Telegram botunuz için mükemmel!** 🚀

---

## 📚 Daha Fazla Bilgi

- **Detaylı Kullanım**: `CANLI_KULLANIM.md`
- **API Dokümantasyonu**: `MARKET_CASH_FLOW_USAGE.md`
- **Hızlı Başlangıç**: `HIZLI_BASLANGIC.md`

---

## ✅ Hemen Test Edin!

```powershell
cd D:\cashflow
python test_live.py
```

**30 saniye içinde canlı market raporunu göreceksiniz!** 🎯
