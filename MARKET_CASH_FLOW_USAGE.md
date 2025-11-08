# Market Cash Flow Raporu - Kullanım Kılavuzu

## Özellik Özeti

Market genelindeki nakit akışını analiz eder ve rapor verir:

- ✅ Farklı zaman dilimlerinde alım-satım dengeleri (15m, 1h, 4h, 12h, 1d)
- ✅ Market geneli alım gücü hesaplama
- ✅ Coin bazlı nakit akış raporu
- ✅ Momentum skorları
- ✅ Risk değerlendirmesi
- ✅ Emoji göstergeleri (🔼🔻)

## API Kullanımı

### Endpoint: `POST /api/analysis/cash-flow`

### Parametreler

```json
{
  "symbols": null,           // null = tüm coinler, ya da ["BTCUSDT", "ETHUSDT", ...]
  "timeframe": "15min",      // Veri kaynağı: "15min", "1H", "4H", "1D"
  "limit": 500,              // Analiz edilecek candle sayısı
  "format": "text"           // "text" = bot için, "json" = detaylı veri
}
```

### Örnek İstek (curl)

```bash
curl -X POST "http://localhost:8000/api/analysis/cash-flow" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": null,
    "timeframe": "15min",
    "limit": 500,
    "format": "text"
  }'
```

### Örnek İstek (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/api/analysis/cash-flow",
    json={
        "symbols": None,  # Tüm coinler
        "timeframe": "15min",
        "limit": 500,
        "format": "text"
    }
)

if response.status_code == 200:
    result = response.json()
    print(result['report'])  # Text formatında rapor
else:
    print(f"Error: {response.status_code}")
```

## Rapor Formatı

### Text Format (format="text")

```
============================================================
📊 Marketteki Tüm Coinlere Olan Nakit Girişi Raporu
============================================================

Kısa Vadeli Market Alım Gücü: 1,0X
Marketteki Hacim Payı: %83,9

15m=> %38,4 🔻
1h=> %49,0 🔻
4h=> %45,6 🔻
12h=> %46,0 🔻
1d=> %47,9 🔻

------------------------------------------------------------
En çok nakit girişi olanlar.
(Sonunda 🔼 olanlarda nakit girişi daha sağlıklıdır)
Nakitin nereye aktığını gösterir. (Nakit Göçü Raporu)
------------------------------------------------------------

BTC Nakit: %34,0 15m:%27 Mts: 0,9 🔻🔻🔻🔻🔻
ETH Nakit: %18,2 15m:%55 Mts: 1,0 🔼🔼🔻🔻🔻
SOL Nakit: %4,9 15m:%68 Mts: 0,8 🔼🔼🔼🔻🔻
...
```

### JSON Format (format="json")

```json
{
  "status": "success",
  "timestamp": "2025-11-08T12:00:00",
  "market_metrics": {
    "short_term_power": 1.0,
    "market_volume_share": 83.9,
    "timeframes": {
      "15m": {"buyer_percentage": 38.4, "indicator": "🔻"},
      "1h": {"buyer_percentage": 49.0, "indicator": "🔻"},
      "4h": {"buyer_percentage": 45.6, "indicator": "🔻"},
      "12h": {"buyer_percentage": 46.0, "indicator": "🔻"},
      "1d": {"buyer_percentage": 47.9, "indicator": "🔻"}
    }
  },
  "risk_assessment": {
    "level": "high",
    "message": "Piyasa ciddi anlamda risk barındırıyor. Alım Yapma!",
    "buyer_1d": 47.9
  },
  "top_flows": [
    {
      "symbol": "BTCUSDT",
      "cash_share": 34.0,
      "buyer_15m": 27,
      "buyer_1h": 30,
      "buyer_4h": 35,
      "buyer_12h": 40,
      "buyer_1d": 45,
      "momentum": 0.9,
      "indicators": "🔻🔻🔻🔻🔻",
      "total_volume": 1500000
    }
  ],
  "total_coins": 150
}
```

## Telegram/Discord Bot Entegrasyonu

### Telegram Bot Örneği

```python
import requests
from telegram import Update
from telegram.ext import CallbackContext, CommandHandler

async def market_cash_flow(update: Update, context: CallbackContext):
    """
    /cashflow komutu - Market nakit akış raporu
    """
    # API'den raporu al
    response = requests.post(
        "http://your-api-url:8000/api/analysis/cash-flow",
        json={"format": "text", "timeframe": "15min", "limit": 500}
    )

    if response.status_code == 200:
        result = response.json()
        await update.message.reply_text(
            result['report'],
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text("❌ Rapor alınamadı")

# Bot'a komut ekle
application.add_handler(CommandHandler("cashflow", market_cash_flow))
```

## Metriklerin Anlamı

### Market Metrikleri

1. **Kısa Vadeli Market Alım Gücü**:
   - 15 dakikalık alım oranı / 1 günlük alım oranı
   - > 1.0: Kısa vadede güçlü alım var
   - < 1.0: Kısa vadede alım zayıf

2. **Marketteki Hacim Payı**:
   - Top 30 coin'in toplam volume içindeki payı

3. **Zaman Dilimi Alım Oranları (15m, 1h, 4h, 12h, 1d)**:
   - Alıcıların toplam volume içindeki yüzdesi
   - > %50: Alıcılar baskın 🔼
   - < %50: Satıcılar baskın 🔻

### Coin Metrikleri

1. **Nakit Payı**: Toplam market volume içindeki payı

2. **15m Alım Oranı**: Son 15 dakikada alıcı yüzdesi

3. **Momentum (Mts)**:
   - Son alım oranı / ortalama alım oranı
   - > 1.0: Güçleniyor
   - < 1.0: Zayıflıyor

4. **Göstergeler (🔼🔻)**:
   - 5 zaman diliminde alım durumu
   - 🔼 = Alıcılar baskın (> %50)
   - 🔻 = Satıcılar baskın (< %50)

## Risk Değerlendirmesi

- **1d alım oranı ≥ %50**: Düşük risk ✅
- **1d alım oranı %45-50**: Orta risk ⚠️
- **1d alım oranı < %45**: Yüksek risk ❌ (Piyasaya bulaşma!)

## Veri Kaynağı

Sistem `data/` klasöründeki parquet dosyalarını kullanır:

```
data/
├── BTCUSDT_15min_futures.parquet
├── ETHUSDT_15min_futures.parquet
├── SOLUSDT_15min_futures.parquet
└── ...
```

Her dosya şu kolonları içermelidir:
- `timestamp`: Zaman damgası
- `volume`: Toplam hacim
- `close`: Kapanış fiyatı
- `taker_buy_base`: Alıcı tarafından başlatılan işlem hacmi

## API Başlatma

```bash
# API'yi başlat
cd /home/user/dosya
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Test et
curl http://localhost:8000/api/analysis/cash-flow \
  -H "Content-Type: application/json" \
  -d '{"format": "text"}'
```

## Notlar

- Market analizi için minimum 10 coin verisi önerilir
- 15min timeframe için en az 500 candle (yaklaşık 5 gün) veri kullanın
- API rate limiting eklenmesi önerilir (production için)
- Büyük market analizleri için caching kullanın

## Sorun Giderme

### "No market data available" hatası
- `data/` klasöründe parquet dosyaları var mı kontrol edin
- Dosya isimlendirmesi: `{SYMBOL}_{TIMEFRAME}_futures.parquet`

### Eksik kolonlar
- Parquet dosyalarında `taker_buy_base` kolonu olmalı
- Binance futures API'den veri çekerken bu alan otomatik gelir

### Yavaş yanıt
- `limit` parametresini azaltın (örn: 300)
- Daha az coin analiz edin (`symbols` parametresi ile)
