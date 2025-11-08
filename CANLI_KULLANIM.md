# 🔴 CANLI Market Cash Flow - Kullanım Kılavuzu

## ✅ ARTIK DOSYA İNDİRMEYE GEREK YOK!

**Yeni Özellik**: Binance'den **anlık canlı veri** çekerek analiz yapar.
- ❌ Parquet dosyası indirmek yok
- ❌ Veri saklama yok
- ✅ Her seferinde güncel veri
- ✅ API Key gerektirmez
- ✅ Telegram/Discord botları için mükemmel!

---

## 🚀 Hızlı Başlangıç (Windows)

### 1. Gerekli Paketleri Yükle

```bash
pip install pandas numpy pyarrow requests
```

### 2. Test Et

```bash
# Canlı veri ile test
python test_live.py
```

**ÇIKTI:**
```
🚀 CANLI Market Cash Flow Testi
============================================================
📡 Binance Futures API'den canlı veri çekiliyor...
⏳ Lütfen bekleyin (30-60 saniye sürebilir)...
============================================================

✅ Analiz tamamlandı!

============================================================
📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu
🔴 CANLI VERİ - Binance Futures
============================================================

Kısa Vadeli Market Alım Gücü: 1.0X
Marketteki Hacim Payı: %83.9

15m=> %38.4 🔻
1h=> %49.0 🔻
4h=> %45.6 🔻
12h=> %46.0 🔻
1d=> %47.9 🔻

------------------------------------------------------------
BTC Nakit: %34.0 15m:%27 Mts: 0.9 🔻🔻🔻🔻🔻
ETH Nakit: %18.2 15m:%55 Mts: 1.0 🔼🔼🔻🔻🔻
SOL Nakit: %4.9 15m:%68 Mts: 0.8 🔼🔼🔼🔻🔻
...
```

---

## 📱 Kullanım Yöntemleri

### **Yöntem 1: Python Scripti (En Basit)**

```python
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

# Analyzer oluştur
analyzer = LiveMarketCashFlowAnalyzer()

# Canlı analiz yap
report = analyzer.analyze_market(
    symbols=None,      # None = Top 30 coin otomatik seçilir
    timeframe='15m',   # 15m, 1h, 4h, 12h, 1d
    limit=500,         # Kaç candle analiz edilecek
    top_n=30           # Kaç coin analiz edilecek
)

# Text raporu al
print(report['text_report'])

# JSON veriye eriş
print(f"Risk: {report['risk_assessment']['level']}")
print(f"Alım Gücü: {report['market_metrics']['short_term_power']}X")
```

### **Yöntem 2: API Servisi (Botlar için)**

#### API Başlat:
```bash
# Windows
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Linux/Mac
uvicorn backend.api.main:app --reload
```

#### Canlı Veri Çek:
```bash
# Text formatında (Telegram bot için)
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"text\", \"top_n\": 30}"

# JSON formatında (detaylı veri)
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"json\", \"top_n\": 30}"
```

### **Yöntem 3: Telegram Bot Entegrasyonu**

```python
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def cashflow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /cashflow - Canlı market analizi
    """
    await update.message.reply_text("📊 Canlı veri çekiliyor...")

    try:
        # API'den CANLI rapor al
        response = requests.post(
            "http://localhost:8000/api/analysis/cash-flow",
            json={
                "live": True,        # ✅ Canlı veri
                "format": "text",    # Text formatı
                "timeframe": "15m",
                "top_n": 30
            },
            timeout=60  # Canlı veri çekme biraz sürebilir
        )

        if response.status_code == 200:
            result = response.json()
            report = result['report']

            # Telegram'a gönder (max 4096 karakter)
            if len(report) > 4000:
                # Uzunsa parçalara böl
                chunks = [report[i:i+4000] for i in range(0, len(report), 4000)]
                for chunk in chunks:
                    await update.message.reply_text(
                        f"<pre>{chunk}</pre>",
                        parse_mode='HTML'
                    )
            else:
                await update.message.reply_text(
                    f"<pre>{report}</pre>",
                    parse_mode='HTML'
                )
        else:
            await update.message.reply_text(
                f"❌ Hata: {response.status_code}\n"
                f"API çalışıyor mu kontrol edin."
            )

    except requests.Timeout:
        await update.message.reply_text(
            "⏱️ Zaman aşımı. Binance API yanıt vermedi.\n"
            "Birkaç saniye sonra tekrar deneyin."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Hata: {str(e)}")

# Bot setup
app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("cashflow", cashflow))

print("🤖 Bot başlatılıyor (canlı veri modu)...")
app.run_polling()
```

---

## 🎯 Parametreler

### `live` (bool, default=True)
- `True`: Binance'den **canlı veri** çeker (önerilir!)
- `False`: Local parquet dosyalarını kullanır

### `symbols` (list, optional)
- `None`: Otomatik olarak en yüksek hacimli 30 coini seçer
- `["BTCUSDT", "ETHUSDT"]`: Belirli coinleri analiz eder

### `timeframe` (str)
- `"15m"`: 15 dakikalık mumlar (varsayılan)
- `"1h"`: 1 saatlik mumlar
- `"4h"`: 4 saatlik mumlar
- `"1d"`: Günlük mumlar

### `top_n` (int, 5-50)
- Otomatik seçimde kaç coin analiz edilecek (varsayılan: 30)

### `limit` (int, 100-1000)
- Kaç candle analiz edilecek (varsayılan: 500)

### `format` (str)
- `"text"`: Telegram/Discord için text rapor
- `"json"`: Detaylı JSON veri

---

## 🔧 API Örnekleri

### Örnek 1: Top 30 Coin (Varsayılan)
```bash
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true}"
```

### Örnek 2: Belirli Coinler
```bash
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"symbols\": [\"BTCUSDT\", \"ETHUSDT\", \"SOLUSDT\"]}"
```

### Örnek 3: 1 Saatlik Mumlarla
```bash
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"timeframe\": \"1h\", \"top_n\": 20}"
```

### Örnek 4: Text Format (Bot için)
```bash
curl -X POST "http://localhost:8000/api/analysis/cash-flow" ^
  -H "Content-Type: application/json" ^
  -d "{\"live\": true, \"format\": \"text\"}"
```

---

## ⚡ Performans

### Canlı Veri Çekme Süresi:
- 30 coin: ~30-45 saniye
- 20 coin: ~20-30 saniye
- 10 coin: ~10-15 saniye

**İpucu**: Daha hızlı yanıt için `top_n` parametresini azaltın.

### Rate Limiting:
- Binance public API limit: ~1200 requests/minute
- 30 coin için ~30 request gerekir
- Her 2 dakikada bir çalıştırabilirsiniz

---

## 🆚 Canlı vs Local Karşılaştırma

| Özellik | Canlı Veri (`live=true`) | Local Veri (`live=false`) |
|---------|--------------------------|---------------------------|
| Veri Güncelliği | ✅ Her seferinde güncel | ❌ Eski veriler |
| Kurulum | ✅ Sadece pip install | ❌ Veri indirmek gerekir |
| Hız | ⚡ 30-60 saniye | ⚡⚡⚡ Çok hızlı (1 saniye) |
| API Key | ✅ Gerektirmez | - |
| İnternet | ✅ Gerekli | ❌ Offline çalışır |
| Bot için | ✅✅✅ Mükemmel | ⚠️ Eski veri |

**Önerimiz**: Telegram/Discord botları için **`live=true`** kullanın!

---

## 🐛 Sorun Giderme

### Problem: "403 Forbidden" hatası
**Sebep**: Bazı sunucular Binance tarafından engellenmiş olabilir.

**Çözüm**:
1. **Kendi bilgisayarınızda** çalıştırın (Windows/Mac/Linux)
2. VPN kullanın
3. Proxy ayarlayın

### Problem: "Timeout" hatası
**Sebep**: Binance API yanıt vermedi.

**Çözüm**:
- `limit` parametresini azaltın (örn: 300)
- `top_n` parametresini azaltın (örn: 20)
- Birkaç saniye sonra tekrar deneyin

### Problem: "No market data available"
**Sebep**: Hiçbir coindens veri çekilemedi.

**Çözüm**:
- İnternet bağlantınızı kontrol edin
- Binance API'nin çalıştığından emin olun: https://api.binance.com/api/v3/ping
- `symbols` parametresini manuel belirleyin

---

## 📊 Örnek Çıktılar

### Text Formatı (format="text"):
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
...
------------------------------------------------------------
Piyasa düşük risk seviyesinde. Alım yapılabilir.
📅 Rapor Zamanı: 2025-11-08 15:30:45
============================================================
```

### JSON Formatı (format="json"):
```json
{
  "status": "success",
  "timestamp": "2025-11-08T15:30:45",
  "data_source": "binance_live",
  "market_metrics": {
    "short_term_power": 1.2,
    "market_volume_share": 85.3,
    "timeframes": {
      "15m": {"buyer_percentage": 52.3, "indicator": "🔼"},
      "1h": {"buyer_percentage": 48.7, "indicator": "🔻"},
      "4h": {"buyer_percentage": 51.2, "indicator": "🔼"},
      "12h": {"buyer_percentage": 49.8, "indicator": "🔻"},
      "1d": {"buyer_percentage": 50.5, "indicator": "🔼"}
    }
  },
  "risk_assessment": {
    "level": "low",
    "message": "Piyasa düşük risk seviyesinde. Alım yapılabilir.",
    "buyer_1d": 50.5
  },
  "top_flows": [
    {
      "symbol": "BTCUSDT",
      "cash_share": 35.2,
      "buyer_15m": 54,
      "momentum": 1.1,
      "indicators": "🔼🔻🔼🔻🔼"
    }
  ],
  "total_coins": 30
}
```

---

## 🎯 Özet

### ✅ Avantajlar:
- Her seferinde **güncel canlı veri**
- Veri indirmeye **gerek yok**
- API Key **gerektirmez**
- Telegram/Discord botları için **mükemmel**

### ⚠️ Dikkat:
- İnternet gerektirir
- Binance API limitlerini aşmayın
- 30-60 saniye sürebilir

### 🚀 Başla:
```python
from backend.analysis.live_cash_flow import LiveMarketCashFlowAnalyzer

analyzer = LiveMarketCashFlowAnalyzer()
report = analyzer.analyze_market()
print(report['text_report'])
```

**Artık dosya indirmeden direkt canlı veri ile analiz yapabilirsiniz!** 🎉
