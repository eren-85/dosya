# 💰 Market Cash Flow Bot

**Standalone** Telegram botu - Binance'den canlı veri ile market nakit akışı analizi.

## ✨ Özellikler

- ✅ **Canlı Binance Spot verisi** (API key gerektirmez)
- ✅ **USD bazlı hesaplama** (doğru karşılaştırma)
- ✅ **3 farklı format**: Text, Tablo, HTML (interaktif)
- ✅ **Telegram bot** komutları
- ✅ **REST API** (opsiyonel)
- ✅ **Risk değerlendirmesi** (Low/Medium/High)
- ✅ **Top N coin** otomatik seçimi
- ✅ **5 zaman dilimi** analizi (15m, 1h, 4h, 12h, 1d)
- ✅ **Emoji göstergeleri** (🔼🔻)
- ✅ **Market Hacim Payı** metriği
- ✅ **Momentum Score (MTS)** hesaplama
- ✅ **HTML tooltips** (USD hacim, momentum detayları)

---

## 🚀 Hızlı Başlangıç

### 🪟 Windows (Tek Tıkla!)

**Telegram Bot İçin:**
1. `config.py` dosyasını düzenle, bot token ekle
2. `start_bot.bat` dosyasına çift tıkla
3. Telegram'dan `/start` yaz!

**HTML Rapor İçin:**
1. `generate_report.bat` dosyasına çift tıkla
2. 30-45 saniye bekle
3. Browser'da `cf.html` otomatik açılır!
4. Coin üzerine gel → USD hacim görürsün

**Hızlı Özet İçin:**
1. `quick_report.bat` dosyasına çift tıkla
2. 10 saniye bekle, tablo formatında 10 coin

### 🐧 Linux/Mac (Manuel)

#### 1. Kurulum

```bash
# Gerekli paketleri yükle
pip install -r requirements.txt
```

#### 2. Telegram Bot Ayarla

```bash
# config.py dosyasını düzenle
nano config.py

# Bot token'ını ekle (BotFather'dan al)
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

#### 3. Botu Başlat

```bash
# Telegram bot
python telegram_bot.py

# veya API server (opsiyonel)
python api.py

# veya HTML rapor oluştur
python generate_report.py
```

---

## 📱 Telegram Komutları

| Komut | Açıklama | Format | Süre |
|-------|----------|--------|------|
| `/cashflow` | Tam market analizi (30 coin) | Text | 30-45 sn |
| `/table` | Tablo formatında analiz | Table | 30-45 sn |
| `/html` | HTML raporu (browser'da açılabilir) | HTML | 30-45 sn |
| `/risk` | Risk değerlendirmesi | Text | 10 sn |
| `/top10` | Top 10 coin analizi | Text | 15 sn |
| `/quick` | Hızlı özet (5 coin) | Text | 5-10 sn |
| `/help` | Yardım ve açıklamalar | - | - |

### 📊 Format Tipleri

#### 1. **Text Format** (klasik)
Basit metin formatında rapor. Telegram'da hızlıca okunabilir.

#### 2. **Table Format** (yeni!)
Tablo formatında düzenli görünüm:
```
╔═══════╦═══════╦═══════╦══════╦═══════╦═══════╦═══════╦═══════╦═══════╦═══════════════╗
║  Coin ║ Nakit ║  15m% ║  MTS ║  15m  ║  1h   ║  4h   ║  12h  ║  1d   ║  Trend        ║
╠═══════╬═══════╬═══════╬══════╬═══════╬═══════╬═══════╬═══════╬═══════╬═══════════════╣
║ BTC   ║ %35.2 ║ %54.0 ║ 1.1X ║  🔼  ║  🔻  ║  🔼  ║  🔻  ║  🔼  ║ 🔼🔻🔼🔻🔼 ║
```

**Sütunlar:**
- **Coin**: Coin adı (USDT hariç)
- **Nakit**: Market hacim payı (%)
- **15m%**: 15 dakikalık alım yüzdesi
- **MTS**: Momentum Score (1.0X = normal, >1.0 = güçlü)
- **15m, 1h, 4h, 12h, 1d**: Her zaman dilimindeki trend (🔼 = alım >%50, 🔻 = satış >%50)
- **Trend**: Tüm zaman dilimlerinin özeti

#### 3. **HTML Format** (interaktif!)
Browser'da açılabilir, modern, interaktif rapor:
- 🎨 Profesyonel gradient tasarım
- 📊 Metrik kartları (hover efekti)
- 🖱️ **Tooltip'ler**: Coin üzerine gelince USD hacim, momentum detayları görünür
- 📱 Responsive tasarım
- 🎯 Risk seviyesi renk kodlu

**Kullanım:** `/html` komutu ile HTML dosyası indirilir, browser'da açılır.

---

## 📈 Metrik Açıklamaları

### **Kısa Vadeli Alım Gücü (Short-Term Power)**
**Formül:** `15m alım % / 1d alım %`

**Örnek:**
- 15m alım: %43.6
- 1d alım: %40.0
- Sonuç: 43.6 / 40.0 = **1.09X**

**Anlamı:**
- **1.0X** = Normal (15m ve 1d alım gücü eşit)
- **>1.0X** = Kısa vadede alım momentumu artıyor 🔼
- **<1.0X** = Kısa vadede alım momentumu düşüyor 🔻

### **Marketteki Hacim Payı (Market Share)**
**Formül:** `(Top 30 coin volume / Tüm analiz edilen coin volume) * 100`

**Örnek:**
- Top 30 coin'in 24h volume'ü: $120B
- Tüm 30 coin'in 24h volume'ü: $120B
- Sonuç: (120/120) * 100 = **%100**

**Anlamı:**
Analiz edilen top 30 coin'in, tüm analiz edilen coin'ler içindeki hacim payı. Genellikle %90-100 arası olur (çünkü top coin'ler çoğu hacmi kapsıyor).

### **Nakit Payı (Cash Share)**
**Formül:** `(Coin volume / Toplam market volume) * 100`

**Örnek:**
- BTC'nin 24h volume'ü: $50B
- Toplam market volume: $150B
- BTC nakit payı: (50/150) * 100 = **%33.3**

**Anlamı:**
Bir coin'in, toplam market hacmindeki payı. BTC %35.2 ise, toplam paranın %35.2'si BTC'de işlem görüyor demek.

### **MTS (Momentum Score)**
**Formül:** `15m alım % / Ortalama alım %`

**Örnek:**
- 15m alım: %54
- Ortalama alım (5 timeframe ortalaması): %49
- MTS: 54 / 49 = **1.1X**

**Anlamı:**
- **1.0X** = Normal momentum
- **>1.0X** = Güçlü alım momentumu (örn: 1.5X = %50 daha güçlü)
- **<1.0X** = Zayıf alım momentumu

### **Timeframe İndikatörleri (🔼/🔻)**
- **🔼** = Alım baskınlığı (buyer % ≥ %50)
- **🔻** = Satış baskınlığı (buyer % < %50)

**Örnek:** `🔼🔻🔼🔻🔼`
- 15m: 🔼 Alım dominant
- 1h: 🔻 Satış dominant
- 4h: 🔼 Alım dominant
- 12h: 🔻 Satış dominant
- 1d: 🔼 Alım dominant

---

## 🪟 Windows Bat Dosyaları

### `start_bot.bat`
Telegram botunu başlatır (tek tıkla).

**Ne yapar?**
- Python ve bağımlılıkları kontrol eder
- `config.py`'de bot token var mı kontrol eder
- Eksik paketleri otomatik yükler
- Telegram botunu başlatır

**Kullanım:**
1. Çift tıkla
2. Telegram'da `/start` yaz

### `generate_report.bat`
HTML raporu oluşturur ve browser'da açar.

**Ne yapar?**
- 30 coin için canlı Binance verisi çeker
- `cf.html` dosyasına kaydeder
- Browser'da otomatik açar
- **Her çalıştırdığında aynı dosyayı günceller!**

**Kullanım:**
1. Çift tıkla
2. 30-45 saniye bekle
3. Browser'da `cf.html` açılır
4. Coin üzerine gel → USD hacim + momentum görürsün

**💡 İpucu:**
- `cf.html`'i browser'da bookmark yap
- Her gün `generate_report.bat` çalıştır
- Browser'da F5 bas, yeni veri gör!

### `quick_report.bat`
Hızlı özet (10 coin, tablo format).

**Ne yapar?**
- 10 coin için analiz (daha hızlı)
- `cf_table.txt` dosyasına tablo formatında kaydeder
- Konsola da yazdırır

**Kullanım:**
1. Çift tıkla
2. 10-15 saniye bekle
3. Tablo formatında özet görürsün

### `setup.bat`
İlk kurulum için.

**Ne yapar?**
- Python versiyonunu kontrol eder
- `requirements.txt`'den tüm bağımlılıkları yükler
- Kurulum sonrası yönlendirme

**Kullanım:**
1. İlk defa kuruyorsan bunu çift tıkla
2. Sonra `start_bot.bat` veya `generate_report.bat` kullan

---

## 🎯 Kullanım Örnekleri

### Telegram Bot

```
Kullanıcı: /cashflow
Bot: 📊 Analiz yapılıyor (30-45 saniye)...

(30 saniye sonra)
Bot:
============================================================
📊 Market Nakit Akışı Raporu
🔴 CANLI VERİ - Binance Spot
============================================================

Kısa Vadeli Alım Gücü: 0.7X

15m=> %37.0 🔻
1h=> %43.9 🔻
4h=> %44.7 🔻
12h=> %46.7 🔻
1d=> %50.0 🔼

------------------------------------------------------------
BTC Nakit:%35.2 15m:%54 Mts:1.1 🔼🔻🔼🔻🔼
ETH Nakit:%19.1 15m:%48 Mts:0.9 🔻🔻🔻🔻🔻
...
```

### Python Scripti

```python
from cashflow_analyzer import CashFlowAnalyzer

analyzer = CashFlowAnalyzer()
report = analyzer.analyze(top_n=30)

print(report['text_report'])
```

### REST API

```bash
# Risk kontrolü
curl http://localhost:8000/risk

# Top 10 coin
curl http://localhost:8000/top/10

# Tam analiz
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"top_n": 30, "format": "text"}'
```

---

## 📊 Rapor Formatı

### Risk Seviyeleri

| Risk | Koşul | Mesaj |
|------|-------|-------|
| 🟢 **LOW** | 1d alım ≥ %50 | Piyasa düşük risk. Alım yapılabilir. |
| 🟡 **MEDIUM** | 1d alım %45-50 | Orta risk. Dikkatli olun. |
| 🔴 **HIGH** | 1d alım < %45 | Yüksek risk. Piyasaya bulaşma! |

### Göstergeler

- **🔼** = Alım baskınlığı (%50+)
- **🔻** = Satış baskınlığı (%50-)

### Metrikler

- **Nakit Payı**: Toplam USD hacmi içindeki yüzde
- **15m**: Son 15 dakika alım oranı
- **Mts (Momentum)**: Kısa vade / ortalama oran
- **Göstergeler**: 5 timeframe için 🔼/🔻

---

## ⚙️ Konfigürasyon

`config.py` dosyasını düzenleyin:

```python
# Telegram Bot
TELEGRAM_BOT_TOKEN = "YOUR_TOKEN_HERE"

# Varsayılan ayarlar
DEFAULT_TOP_N = 30          # Coin sayısı
DEFAULT_TIMEFRAME = "15m"   # Zaman dilimi
DEFAULT_LIMIT = 500         # Candle sayısı

# API ayarları
API_HOST = "0.0.0.0"
API_PORT = 8000
```

---

## 🔧 API Referansı

### POST /analyze

**Request:**
```json
{
  "top_n": 30,
  "timeframe": "15m",
  "limit": 500,
  "format": "text"
}
```

**Response:**
```json
{
  "status": "success",
  "timestamp": "2025-11-08T15:30:00",
  "market_metrics": { ... },
  "risk_assessment": { ... },
  "top_flows": [ ... ],
  "text_report": "..."
}
```

### GET /risk

Risk değerlendirmesi döner.

### GET /top/{n}

Top N coin analizi döner.

---

## 📦 Dosya Yapısı

```
cashflow-bot/
├── cashflow_analyzer.py   # Ana analiz motoru (400 satır)
├── telegram_bot.py         # Telegram bot (150 satır)
├── api.py                  # REST API (140 satır)
├── config.py               # Ayarlar
├── requirements.txt        # Bağımlılıklar
└── README.md               # Bu dosya
```

**Toplam:** ~700 satır temiz kod, bağımlılıklar minimal.

---

## 🐛 Sorun Giderme

### "TELEGRAM_BOT_TOKEN ayarlanmamış"

```bash
# config.py'yi düzenle
nano config.py

# Token ekle (BotFather'dan al)
TELEGRAM_BOT_TOKEN = "123456789:ABC..."
```

### "403 Forbidden" (Binance)

- Ev internetinden deneyin (kurumsal ağ engelliyor olabilir)
- VPN kullanın

### "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

---

## 🎯 Performans

| Coin Sayısı | Süre |
|-------------|------|
| 10 coin | ~10-15 sn |
| 20 coin | ~20-30 sn |
| 30 coin | ~30-45 sn |

**İpucu:** Hızlı yanıt için `top_n=20` kullanın.

---

## 📚 Ek Bilgiler

### BotFather'dan Token Alma

1. Telegram'da [@BotFather](https://t.me/BotFather) ara
2. `/newbot` komutuyla yeni bot oluştur
3. Bot ismi belirle
4. Token'ı kopyala
5. `config.py`'ye yapıştır

### Sunucuda Çalıştırma

```bash
# tmux veya screen ile
tmux new -s cashflow
python telegram_bot.py

# Ctrl+B D ile detach
```

### Otomatik Başlatma (systemd)

```bash
# /etc/systemd/system/cashflow-bot.service
[Unit]
Description=Market Cash Flow Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/cashflow-bot
ExecStart=/usr/bin/python3 telegram_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable cashflow-bot
sudo systemctl start cashflow-bot
```

---

## ✅ Özet

### Avantajlar:
- Standalone (bağımsız)
- Minimal bağımlılıklar
- API key gerektirmez
- USD bazlı doğru hesaplama
- Telegram/Discord entegre
- REST API dahil

### Kullanım Alanları:
- Telegram kanalınız için bot
- Discord sunucunuz için bot
- Web siteniz için API
- Kendi trade stratejiniz

**Artık tamamen bağımsız, kullanıma hazır Cash Flow Bot!** 🚀

---

## 📄 Lisans

MIT License - Özgürce kullanın!

## 💬 Destek

Sorular için issue açın veya Telegram'dan ulaşın.

**İyi tradeler!** 💰
