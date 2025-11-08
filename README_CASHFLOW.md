# 💰 Market Cash Flow - Telegram Bot Özelliği

**Binance'den canlı veri çekerek marketteki nakit akışını analiz eder.**

## ✅ Sorunuza Cevap

> "bunun için anlık veri çekip bakması gerekmiyor mu neden mum indirmesi gerekiyor?"

**Haklıydınız!** Artık **Binance API'den anlık canlı veri** çekiyor! 🎉

- ❌ Veri indirmeye gerek yok
- ❌ Dosya saklamaya gerek yok
- ✅ Her seferinde güncel canlı veri
- ✅ API Key gerektirmez
- ✅ Telegram/Discord botları için hazır

---

## 🚀 Windows'ta Hızlı Test (3 Adım)

```powershell
# 1. Gerekli paketleri yükle
pip install pandas numpy pyarrow requests

# 2. Test scriptini çalıştır
python -c "
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer
analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market()
print(report['text_report'])
"

# 3. 30 saniye bekle, raporu gör! ✅
```

**Veya test dosyasıyla:**

```python
# test_cashflow.py
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market(
    symbols=None,      # Top 30 otomatik
    timeframe='15m',
    top_n=30
)

print(report['text_report'])
```

```powershell
python test_cashflow.py
```

---

## 📊 Örnek Çıktı

```
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
DOGE Nakit: %1.9 15m:%42 Mts: 0.7 🔻🔻🔻🔻🔻
ADA Nakit: %1.5 15m:%55 Mts: 1.1 🔼🔼🔼🔻🔻
...

------------------------------------------------------------
Piyasa düşük risk seviyesinde. Alım yapılabilir.
Günlük nakit giriş oranı %50 üzerine çıkarsa risk azalacaktır.

📅 Rapor Zamanı: 2025-11-08 15:30:45
============================================================
```

---

## 🤖 Telegram Bot Entegrasyonu

### Basit Örnek:

```python
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Canlı market analizi"""
    await update.message.reply_text("📊 Canlı veri çekiliyor (30 saniye)...")

    # Canlı analiz
    analyzer = LiveMarketCashFlowAnalyzer()
    report = analyzer.analyze_market()

    # Raporu gönder
    await update.message.reply_text(
        f"<pre>{report['text_report']}</pre>",
        parse_mode='HTML'
    )

# Bot
app = Application.builder().token("YOUR_TOKEN").build()
app.add_handler(CommandHandler("cashflow", cashflow))
app.run_polling()
```

**Kullanım:**
```
Telegram'da: /cashflow
Bot: [30 saniye içinde canlı rapor gösterir]
```

---

## ⚙️ API ile Kullanım

### 1. API'yi Başlat:
```powershell
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
```

### 2. Canlı Rapor İste:
```powershell
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"text\"}"
```

### 3. Swagger Docs:
http://localhost:8000/docs

---

## 🎯 Parametreler

```python
analyzer.analyze_market(
    symbols=None,       # None = Top 30 otomatik
                        # ["BTCUSDT", "ETHUSDT"] = Belirli coinler

    timeframe='15m',    # 15m, 1h, 4h, 12h, 1d

    top_n=30,           # Kaç coin analiz edilecek (5-50)

    limit=500           # Kaç candle analiz edilecek (100-1000)
)
```

---

## 📚 Dokümantasyon

| Dosya | Açıklama |
|-------|----------|
| **WINDOWS_TEST.md** | Windows için adım adım kılavuz |
| **CANLI_KULLANIM.md** | Detaylı kullanım ve örnekler |
| **MARKET_CASH_FLOW_USAGE.md** | API referansı |
| **HIZLI_BASLANGIC.md** | Genel başlangıç kılavuzu |

---

## 💡 Özellikler

### ✅ Canlı Veri Modu (`live=true`):
- Binance Spot API'den anlık veri
- Her seferinde güncel
- Veri indirmeye gerek yok
- API Key gerektirmez
- Top coins otomatik seçilir

### ⚡ Local Mod (`live=false`):
- Parquet dosyalarından okur
- Çok hızlı (1 saniye)
- Offline çalışır
- Ama veri indirmek gerekir

**Botlar için:** `live=true` kullanın! ✅

---

## 🔧 Teknik Detaylar

### Veri Kaynağı:
- **Binance Spot API** (public endpoints)
- `GET /api/v3/ticker/24hr` - Top coins
- `GET /api/v3/klines` - OHLCV data

### Hesaplamalar:
- Alım oranı: `(taker_buy_base / volume) * 100`
- Momentum: `15m alım oranı / ortalama alım oranı`
- Risk: 1d alım oranı < %50 → Yüksek risk

### Performans:
- 30 coin: ~30-45 saniye
- 20 coin: ~20-30 saniye
- Rate limit: ~1200 req/min (Binance)

---

## 🆚 Karşılaştırma

| Özellik | Eski Sistem | Yeni Sistem (Canlı) |
|---------|-------------|---------------------|
| Veri İndirme | ❌ Gerekli | ✅ Gereksiz |
| Güncel Veri | ❌ Manuel güncelleme | ✅ Her seferinde güncel |
| Kurulum | ❌ Karmaşık | ✅ Sadece pip install |
| Bot Entegrasyonu | ⚠️ Zor | ✅ Çok kolay |
| Hız | ⚡⚡⚡ 1 saniye | ⚡ 30 saniye |
| API Key | - | ✅ Gerektirmez |

---

## 🐛 Sorun Giderme

### "403 Forbidden"
- Ev internetinden deneyin (kurumsal ağ engelliyor olabilir)
- VPN kullanın

### "Timeout"
- `top_n=20` yapın (daha az coin)
- `limit=300` yapın (daha az candle)

### "No market data"
- İnternet bağlantınızı kontrol edin
- Binance API çalışıyor mu: https://api.binance.com/api/v3/ping

---

## ✨ Avantajlar

### ✅ Bot Sahipleri İçin:
- Gerçek zamanlı piyasa analizi
- Kullanıcılara güncel bilgi
- Kolay entegrasyon
- API Key yok

### ✅ Geliştiriciler İçin:
- Temiz API
- İyi dokümante
- Kolay özelleştirme
- Hem Python hem REST API

---

## 🎉 Başla!

```powershell
# Windows PowerShell
cd D:\cashflow
pip install pandas numpy pyarrow requests

python -c "
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer
analyzer = LiveMarketCashFlowAnalyzer()
print(analyzer.analyze_market()['text_report'])
"
```

**30 saniye içinde canlı market raporunu göreceksiniz!** 🚀

---

## 📞 Destek

- **Windows Kılavuzu**: `WINDOWS_TEST.md`
- **Detaylı Kullanım**: `CANLI_KULLANIM.md`
- **API Referansı**: `MARKET_CASH_FLOW_USAGE.md`

**Artık veri indirmeye gerek yok - sadece çalıştır!** ✅
