# 🚀 Market Cash Flow - Hızlı Başlangıç

## ✅ Sistem Hazır ve Test Edildi!

Market Cash Flow analiz sistemi başarıyla kuruldu ve çalışıyor.

---

## 📋 Gereksinimler

```bash
# Gerekli paketler (zaten yüklü)
pip install pandas numpy pyarrow
```

---

## 🎯 Kullanım Yöntemleri

### **1. Python CLI ile (En Hızlı)**

```bash
# Basit kullanım (tüm coinler)
python scripts/market_cash_flow.py

# Belirli coinler
python scripts/market_cash_flow.py --symbols BTCUSDT ETHUSDT SOLUSDT

# Farklı zaman dilimi
python scripts/market_cash_flow.py --timeframe 1H --limit 300

# JSON çıktı
python scripts/market_cash_flow.py --json
```

### **2. API Servisi ile (Botlar için)**

#### API'yi Başlat:
```bash
# Terminal 1: API'yi çalıştır
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Test et
curl http://localhost:8000/health
```

#### API'yi Çağır:
```bash
# Text formatında rapor al (Telegram bot için ideal)
curl -X POST "http://localhost:8000/api/analysis/cash-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": null,
    "timeframe": "15min",
    "limit": 500,
    "format": "text"
  }'

# JSON formatında detaylı veri
curl -X POST "http://localhost:8000/api/analysis/cash-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": null,
    "timeframe": "15min",
    "limit": 500,
    "format": "json"
  }'
```

### **3. Python Kodundan Doğrudan**

```python
from backend.analysis.market_cash_flow import MarketCashFlowAnalyzer

# Analyzer oluştur
analyzer = MarketCashFlowAnalyzer(data_dir="data")

# Analiz yap
report = analyzer.analyze_market(
    symbols=None,  # Tüm coinler
    base_timeframe='15min',
    limit=500
)

# Text raporu al
print(report['text_report'])

# JSON veriye eriş
print(f"Risk Level: {report['risk_assessment']['level']}")
print(f"Market Power: {report['market_metrics']['short_term_power']}X")
```

---

## 📊 Veri Gereksinimleri

### Mevcut Veri:
```
data/historical/BTCUSDT_1d_futures.parquet ✅
```

### Daha Fazla Coin Eklemek İçin:

Sistemin tam gücünü görmek için daha fazla coin verisi gerekiyor. Seçenekler:

#### **Seçenek 1: Mevcut Veri Toplama Scripti (Önerilir)**

```bash
# Eğer projenizde veri toplama scripti varsa
python backend/historical_sync.py --symbols BTCUSDT ETHUSDT SOLUSDT \
  --timeframes 15min 1H 4H --days 30
```

#### **Seçenek 2: Manuel Veri Toplama**

```python
# Binance'den veri topla
from backend.data.sources.binance import BinanceCollector
import pandas as pd

collector = BinanceCollector()

symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT']
timeframe = '15min'

for symbol in symbols:
    # Veri topla (son 7 gün)
    data = collector.fetch_klines(
        symbol=symbol,
        interval='15m',
        limit=672  # 7 gün x 96 candle
    )

    # Kaydet
    data.to_parquet(f'data/{symbol}_{timeframe}_futures.parquet')
    print(f"✓ {symbol} saved")
```

#### **Seçenek 3: Örnek Veri Seti (Test için)**

Eğer hızlıca test etmek istiyorsanız, mevcut BTC verisini kopyalayarak simüle edebilirsiniz:

```bash
# BTC verisini diğer coinler için kopyala (sadece test için!)
cp data/historical/BTCUSDT_1d_futures.parquet data/historical/ETHUSDT_1d_futures.parquet
cp data/historical/BTCUSDT_1d_futures.parquet data/historical/SOLUSDT_1d_futures.parquet
cp data/historical/BTCUSDT_1d_futures.parquet data/historical/BNBUSDT_1d_futures.parquet

# Test et
python scripts/market_cash_flow.py --timeframe 1d
```

---

## 🤖 Telegram Bot Entegrasyonu

### Basit Örnek:

```python
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

async def cashflow_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /cashflow komutu - Market nakit akış raporu
    """
    await update.message.reply_text("📊 Market analizi yapılıyor...")

    # API'den rapor al
    response = requests.post(
        "http://localhost:8000/api/analysis/cash-flow",
        json={
            "symbols": None,
            "timeframe": "15min",
            "limit": 500,
            "format": "text"
        },
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()

        # Raporu parçalara böl (Telegram 4096 karakter limiti)
        report = result['report']

        # Telegram'a gönder
        await update.message.reply_text(
            f"<pre>{report}</pre>",
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Rapor alınamadı. API çalışıyor mu?")

# Bot setup
app = Application.builder().token("YOUR_BOT_TOKEN").build()
app.add_handler(CommandHandler("cashflow", cashflow_command))

print("🤖 Bot başlatılıyor...")
app.run_polling()
```

### Kullanım:
```
Kullanıcı: /cashflow
Bot: [Market nakit akış raporunu gösterir]
```

---

## 📈 Örnek Rapor Çıktısı

```
============================================================
📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu
============================================================

Kısa Vadeli Market Alım Gücü: 1.0X
Marketteki Hacim Payı: %83.9

15m=> %38.4 🔻
1h=> %49.0 🔻
4h=> %45.6 🔻
12h=> %46.0 🔻
1d=> %47.9 🔻

------------------------------------------------------------
En çok nakit girişi olanlar.
(Sonunda 🔼 olanlarda nakit girişi daha sağlıklıdır)
Nakitin nereye aktığını gösterir. (Nakit Göçü Raporu)
------------------------------------------------------------

BTC Nakit: %34.0 15m:%27 Mts: 0.9 🔻🔻🔻🔻🔻
ETH Nakit: %18.2 15m:%55 Mts: 1.0 🔼🔼🔻🔻🔻
SOL Nakit: %4.9 15m:%68 Mts: 0.8 🔼🔼🔼🔻🔻
...

------------------------------------------------------------
Piyasa ciddi anlamda risk barındırıyor. Alım Yapma!
Günlük nakit giriş oranı %50 üzerine çıkarsa risk azalacaktır.
============================================================
```

---

## 🔧 Troubleshooting

### Problem: "No module named 'pandas'"
```bash
pip install pandas numpy pyarrow
```

### Problem: "No market data available"
- `data/` klasöründe parquet dosyaları olduğundan emin olun
- Dosya isimleri: `{SYMBOL}_{TIMEFRAME}_futures.parquet` formatında olmalı

### Problem: "Missing required columns"
- Sistem otomatik olarak Binance kolonlarını (open_time, taker_base) normalize eder
- Eğer problem devam ederse parquet dosyasını kontrol edin:
```python
import pandas as pd
df = pd.read_parquet('data/BTCUSDT_15min_futures.parquet')
print(df.columns.tolist())
```

### Problem: API 503 hatası
- FastAPI başlatın: `uvicorn backend.api.main:app`
- Port çakışması varsa: `--port 8001` ekleyin

---

## 📚 Daha Fazla Bilgi

- **Detaylı API Dokümantasyonu**: `MARKET_CASH_FLOW_USAGE.md`
- **API Swagger Docs**: http://localhost:8000/docs (API başlatıldıktan sonra)
- **Kod Referansı**: `backend/analysis/market_cash_flow.py`

---

## 🎯 Hızlı Test

```bash
# 1. Sistemi test et
python test_quick.py

# 2. CLI ile çalıştır
python scripts/market_cash_flow.py

# 3. API'yi başlat (başka terminalde)
uvicorn backend.api.main:app --reload

# 4. API'yi test et
curl -X POST "http://localhost:8000/api/analysis/cash-flow" \
  -H "Content-Type: application/json" \
  -d '{"format": "text"}'
```

---

## ✅ Sistem Durumu

- ✅ Market Cash Flow Analyzer: Çalışıyor
- ✅ API Endpoint: Hazır
- ✅ CLI Tool: Hazır
- ✅ Kolonlar otomatik normalize ediliyor
- ✅ BTC verisi ile test edildi
- ⏳ Daha fazla coin verisi için veri toplama gerekiyor

**Sisteminiz hazır! Botunuza entegre edebilirsiniz.** 🚀
