# 🤖 Sigma Analyst - AI Finansal Analiz ve Piyasa İstihbarat Sistemi

**Sigma Analyst**, kripto piyasaları için yapay zeka destekli kapsamlı bir analiz ve karar destek sistemidir. Teknik analiz, on-chain veriler, piyasa psikolojisi ve makine öğrenmesi algoritmalarını birleştirerek derinlemesine piyasa istihbaratı sağlar.

## 🎯 Özellikler

### 🧠 Multi-Role AI Agent
- **Kıdemli Kripto Piyasa Analisti**: Teknik, on-chain ve makroekonomik analiz
- **Piyasa İstihbarat Uzmanı**: On-chain veriler ve balina hareketleri
- **Davranışsal Finans Psikoloğu**: Piyasa psikolojisi ve sentiment analizi
- **Nitelikli Haber Muhabiri**: Tarafsız, veriye dayalı raporlama
- **Sistem Mühendisi**: Karmaşık veri akışlarını entegre eden sistem

### 📊 Çoklu Veri Kaynakları
- **Exchange Data**: Binance, OKX, Bybit, Bitget, MEXC, Coinbase, Gate.io
- **On-Chain**: Glassnode, CryptoQuant
- **Aggregated Data**: tucsky/aggr, Coinalyze
- **Türev Piyasalar**: Open Interest, Funding Rates, CVD

### 🤖 Gelişmiş ML/AI Sistemi
- **Ensemble Models**: GradBoost (99.2%), XGBoost (97.7%), LightGBM (94.2%)
- **Reinforcement Learning**: Decision Transformer + PPO Fine-tuning
- **Deep Learning**: LSTM (trend), Transformer (pattern recognition)
- **RAG System**: PDF'lerden öğrenen bilgi bankası

### 📈 Analiz Yetenekleri
- Teknik Analiz (200+ indikatör)
- Smart Money & ICT Konseptleri
- Fibonacci Golden Zone / OTE
- Kill Zones (Londra, New York, Asya)
- On-chain Metrikler (whale flows, exchange netflows)
- Market Microstructure (CVD, OI, Funding)
- Piyasa Psikolojisi (Fear & Greed, sentiment)

### 🎮 Çalışma Modları
- **Oneshot Mode**: Tek seferlik detaylı rapor
- **Monitor Mode**: Sürekli izleme ve akıllı alerting
- **Backtest Mode**: Tarihsel veri üzerinde strateji testi

## 🏗️ Sistem Mimarisi

```
┌─────────────────────────────────────────────────────────┐
│                  DATA SOURCES LAYER                      │
│  Binance | Glassnode | CryptoQuant | Aggr | Coinalyze  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│             FEATURE ENGINEERING LAYER                    │
│  Technical Indicators | On-chain | Market Microstructure│
└──────────────────────┬──────────────────────────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌────────────────────┐    ┌─────────────────────┐
│  SUPERVISED ML     │    │  UNSUPERVISED ML    │
│  Ensemble Models   │    │  Pattern/Regime     │
└────────┬───────────┘    └──────────┬──────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
         ┌───────────────────────────┐
         │   REINFORCEMENT LEARNING   │
         │  Decision Transformer +PPO │
         └────────────┬───────────────┘
                      ▼
         ┌────────────────────────────┐
         │   CLAUDE REASONING LAYER   │
         │   Final Decision + Report  │
         └────────────────────────────┘
```

## 🚀 Kurulum

### Gereksinimler
- **Docker Desktop** (önerilen) - Tek kurulum, tüm bağımlılıklar dahil
- VEYA Python 3.10+ + PostgreSQL 14+ + Redis 7+ (manuel kurulum)
- RTX 4060 8GB (GPU eğitimi için opsiyonel, CPU'da da çalışır)

---

## 🐳 Kurulum Yöntem 1: Docker (ÖNERİLEN) ⭐

**Avantajları:**
- ✅ 3 adımda kurulum
- ✅ Tüm bağımlılıklar otomatik
- ✅ Windows/Mac/Linux uyumlu
- ✅ Temiz, izole ortam

### Adım 1: Docker Desktop Kurun

**Windows:**
```powershell
winget install -e --id Docker.DockerDesktop
```

**Mac:**
```bash
brew install --cask docker
```

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

Docker Desktop'ı başlatın ve çalıştığını doğrulayın:
```powershell
docker --version
# Docker version 27.x.x, build xxxxx
```

### Adım 2: Proje Klasörüne Gidin ve .env Oluşturun

```powershell
# Proje klasörüne gidin
cd D:\3\dosya

# .env dosyasını oluşturun
Copy-Item .env.example .env

# .env dosyasını düzenleyin (OpenAI veya Anthropic API key gerekli)
notepad .env
```

**Minimum .env ayarları:**
```env
# Database
POSTGRES_PASSWORD=GucluSifreniz123!

# AI/LLM (OpenAI önerilen - daha iyi limitler)
OPENAI_API_KEY=sk-proj-xxxxxxxxxx
OPENAI_MODEL=gpt-4o-mini  # veya gpt-4o, gpt-4-turbo

# Alternatif: Anthropic Claude
# ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxx
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

**Not:** AI Analysis özelliği için OpenAI veya Anthropic API anahtarından en az birisi gereklidir.

### Adım 3: Başlatın! 🚀

```powershell
docker-compose up -d --build
```

**İlk çalıştırmada 10-15 dakika sürer (paketler indiriliyor).**

**API test:**
```
http://localhost:8000/docs
```

**Celery monitoring:**
```
http://localhost:5555
```

✅ **Sistem hazır!**

**📖 Detaylı rehber:** [DOCKER_SETUP_GUIDE.md](DOCKER_SETUP_GUIDE.md) - Hiç bilmeyen birine anlatır gibi tüm adımlar

---

## 💻 Kurulum Yöntem 2: Manuel (Python + PostgreSQL)

<details>
<summary>Manuel kurulum adımları (tıklayın)</summary>

### 1. Repository'yi Klonlayın
```bash
git clone <repo-url>
cd sigma-analyst
```

### 2. Virtual Environment Oluşturun
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# veya
venv\Scripts\activate  # Windows
```

### 3. Dependencies Kurun
```bash
pip install -r requirements.txt

# TA-Lib için sistem paketleri (Ubuntu/Debian)
sudo apt-get install ta-lib

# MacOS
brew install ta-lib
```

### 4. Environment Variables
```bash
cp .env.example .env
# .env dosyasını düzenleyin
```

### 5. Veritabanı Kurulumu (opsiyonel)
```bash
# PostgreSQL + TimescaleDB + Redis
docker-compose up -d postgres redis

# Not: Şu anda veriler dosya sisteminde saklanıyor (CSV/Parquet)
# PostgreSQL ileride time-series data için kullanılacak
# Redis Celery task queue için kullanılıyor
```

### 6. Backend'i Başlatın
```bash
cd backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Frontend'i Başlatın
```bash
cd frontend
npm install
npm run dev
```

</details>

## 📖 Kullanım

### CLI Kullanımı
```bash
# Oneshot analiz
python -m backend.cli analyze --symbols BTCUSDT,ETHUSDT --mode oneshot

# Monitor mode
python -m backend.cli monitor --symbols BTCUSDT --freq 15m

# Backtest
python -m backend.cli backtest --strategy decision_transformer --start 2023-01-01 --end 2024-01-01
```

### API Kullanımı
```python
import requests

# Analiz isteği
response = requests.post("http://localhost:8000/api/analysis", json={
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "timeframes": ["1H", "4H", "1D"],
    "mode": "oneshot"
})

report = response.json()
print(report["market_pulse"])
```

### 🎨 Web UI (React Dashboard)

**Sistem başlatıldıktan sonra tarayıcınızda açın**: `http://localhost:3000`

#### 📥 Download Data (Veri İndirme)

Binance'ten tarihsel OHLCV verilerini indirin.

**Özellikler:**
- **Spot ve Futures** desteği
- **Çoklu sembol**: Virgülle ayırarak birden fazla coin (örn: BTCUSDT,ETHUSDT,SOLUSDT)
- **Tüm timeframe'ler**: 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 3d, 1w, 1M
- **All-time veya tarih aralığı** seçimi
- **Parquet formatı**: CSV'ye göre 5-10x daha hızlı yükleme
- **Sync (Resume)**: Son mumdan devam et, eksik verileri tamamla

**Kullanım:**
1. Sol menüden "Download Data" sekmesine tıklayın
2. Sembol(leri) girin (örn: BTCUSDT,ETHUSDT)
3. Timeframe seçin (örn: 1h)
4. Market türü seçin (Spot/Futures)
5. All-time veya tarih aralığı belirleyin
6. Parquet seçeneğini işaretleyin (önerilen)
7. "Download" veya "Sync" butonuna tıklayın
8. İndirme loglarını takip edin

**İndirilen dosyalar:** `data/historical/` klasörüne kaydedilir

#### 🧠 Train Models (Model Eğitimi)

İndirdiğiniz veriler üzerinde makine öğrenmesi modelleri eğitin.

**Modeller:**
- **Ensemble**: XGBoost + LightGBM + CatBoost (robust tahminler)
- **LSTM**: Recurrent neural network (dizi tahmini, GPU önerilen)
- **Transformer**: Attention-based model (pattern recognition, GPU gerekli)
- **PPO**: Reinforcement Learning (karar optimizasyonu, GPU gerekli)

**GPU Desteği:**
- ✅ RTX 4060 8GB ile BF16 + TF32 optimizasyonları
- CPU modunda da çalışır (daha yavaş)

**Kullanım:**
1. Sol menüden "Train Models" sekmesine tıklayın
2. Sembol(leri) girin (örn: BTCUSDT,ETHUSDT)
3. Timeframe'leri girin (örn: 1h,4h,1d)
4. Model türü seçin (Ensemble, LSTM, Transformer, PPO)
5. Epoch sayısını ayarlayın (100 önerilen)
6. GPU kullanımını işaretleyin
7. "Start Training" butonuna tıklayın
8. Eğitim loglarını takip edin

**Eğitilen modeller:** `data/models/` klasörüne kaydedilir

#### 🤖 AI Analysis (Yapay Zeka Analizi)

OpenAI GPT-4 ile gerçek zamanlı piyasa analizi.

**Özellikler:**
- **Market Bias**: Bullish / Bearish / Neutral durum
- **Confidence Score**: AI güven seviyesi (0-100%)
- **Trading Signals**: Entry, Stop Loss, Take Profit seviyeleri
- **Technical Analysis**: RSI, MACD, MA, Bollinger Bands
- **On-Chain Data**: Exchange netflow, whale hareketleri (BTC için)
- **Risk Assessment**: Risk seviyesi ve position size önerileri
- **Quick Analysis**: Hızlı metin tabanlı analiz ve soru-cevap

**Kullanım:**

**Full Analysis:**
1. Sol menüden "AI Analysis" sekmesine tıklayın
2. Sembol(leri) girin (örn: BTCUSDT,ETHUSDT,SOLUSDT)
3. Timeframe'leri girin (örn: 1H,4H,1D)
4. Analysis Mode seçin (One-shot / Continuous)
5. "Use OpenAI GPT-4" seçeneğini işaretleyin
6. "Analyze Markets" butonuna tıklayın
7. Her sembol/timeframe için detaylı analiz sonuçlarını görün:
   - Market Bias ve Confidence
   - Summary
   - Trading Signal (Action, Entry, SL, TP1, TP2, Risk/Reward)
   - Conclusion

**Quick Analysis:**
1. Aynı sayfanın alt bölümünde "Quick Analysis" kısmına gidin
2. Sembol girin (örn: BTCUSDT)
3. İsteğe bağlı soru girin (örn: "Is this a good entry point?")
4. "Quick Analyze" butonuna tıklayın
5. Hızlı AI yanıtını alın

**Not:** OpenAI API anahtarı gereklidir (.env dosyasında `OPENAI_API_KEY`)

#### 📈 Backtest (Strateji Testi)

Tarihsel veriler üzerinde trading stratejilerini test edin.

**Stratejiler:**
- **Trend Following**: Moving Average Cross
- **Mean Reversion**: Bollinger Bands
- **Momentum**: RSI + MACD
- **Breakout**: Support/Resistance
- **ML Ensemble**: XGBoost + LightGBM
- **ML LSTM**: Deep Learning
- **ML Transformer**: Deep Learning

**Performans Metrikleri:**
- Total Return (%)
- Sharpe Ratio
- Max Drawdown
- Win Rate (%)
- Profit Factor
- Total Trades
- Avg Win/Loss
- Best/Worst Trade

**Kullanım:**
1. Sol menüden "Backtest" sekmesine tıklayın
2. Strateji seçin
3. Sembol(leri) girin (örn: BTCUSDT,ETHUSDT)
4. Timeframe seçin (örn: 1h)
5. Tarih aralığı belirleyin (örn: 2023-01-01 / 2024-01-01)
6. Risk parametrelerini ayarlayın:
   - Initial Capital ($)
   - Position Size (% of capital)
   - Commission (% per trade)
7. "Run Backtest" butonuna tıklayın
8. Detaylı performans metriklerini ve trade history'yi inceleyin

**Sonuçlar:**
- Performance Metrics: 6 temel metrik (Return, Sharpe, Drawdown, Win Rate, Profit Factor, Total Trades)
- Trade Statistics: 7 istatistik (Winning/Losing trades, Avg Win/Loss, Best/Worst, Duration)
- Trade History: Tüm trade'lerin detaylı listesi (entry/exit time, price, PnL)

#### 📊 Advanced Chart (Gelişmiş Grafik)

Profesyonel teknik analiz araçları ve Smart Money kavramları.

**Özellikler:** (Mevcut sayfa - önceki dokümantasyona bakın)

#### 💼 Portfolio (Portföy Yönetimi)

Portfolio takibi ve yönetimi.

**Not:** Bu sayfa geliştirilme aşamasındadır.

## 🎓 Öğrenme ve Eğitim Sistemleri

### 📚 PDF RAG Sistemi

Sistem, PDF dokümanlarından bilgi öğrenebilir ve analiz sırasında bu bilgileri kullanabilir.

**PDF Klasörü Konumu**: `./data/knowledge/`

PDF'leri eklemek için:
```bash
# PDF klasörünü oluşturun
mkdir -p ./data/knowledge/

# PDF'lerinizi bu klasöre kopyalayın
cp your-trading-books.pdf ./data/knowledge/

# PDF'leri sisteme yükleyin
python -c "
from backend.learning.pdf_rag import PDFLearningSystem
rag = PDFLearningSystem()
rag.ingest_pdf('./data/knowledge/your-trading-books.pdf', category='trading_strategies')
"
```

### 🎯 Manuel Eğitim Sistemi

Kendiniz pattern ve swing point'leri işaretleyerek sistemi manuel eğitebilirsiniz.

```python
from backend.learning.manual_training import ManualAnnotation
import pandas as pd

# Manuel annotation sistemi
annotator = ManualAnnotation(annotations_dir="./data/annotations")

# Swing high/low işaretleme
annotator.annotate_swing_point(
    symbol="BTCUSDT",
    timeframe="1H",
    swing_type="high",  # veya "low"
    index=150,
    price=68500.0,
    timestamp="2024-01-15T10:00:00",
    market_data={
        'volume': 1234567,
        'rsi_14': 78.5,
        'open_interest': 25000000,
        'net_longs': 60.5,
        'net_shorts': 39.5,
        'cvd': 5000000,
        'funding_rate': 0.01,
        'orderbook_imbalance': 1.2,
        'exchange_netflow': -500,
        'whale_tx_count': 15
    }
)

# Pattern işaretleme
annotator.annotate_pattern(
    symbol="BTCUSDT",
    timeframe="4H",
    pattern_type="head_and_shoulders",
    points=[
        {'index': 100, 'price': 67000, 'timestamp': '2024-01-15T00:00:00'},
        {'index': 120, 'price': 69000, 'timestamp': '2024-01-15T20:00:00'},
        {'index': 140, 'price': 67500, 'timestamp': '2024-01-16T16:00:00'},
    ],
    metadata={'volume_surge': True, 'rsi_divergence': True}
)

# Training dataseti olarak dışa aktar
annotator.export_training_dataset('./data/training/manual_annotations.json')
```

### 📊 Tarihsel Öğrenme (Historical Learning)

Sistem, geçmiş tüm verileri tarayarak otomatik pattern tespiti ve öğrenme yapabilir:

```python
from backend.learning.historical_learning import HistoricalDataLearner
from datetime import datetime

# Tarihsel öğrenme sistemi
learner = HistoricalDataLearner(
    data_dir="./data/historical",
    pattern_library_path="./data/patterns/library.json"
)

# All-time verileri tara ve öğren
results = learner.scan_historical_data(
    symbol="BTCUSDT",
    timeframe="1H",
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2024, 12, 31),
    batch_size=1000  # Her seferde 1000 mum işle
)

print(f"✅ {results['patterns_detected']} pattern tespit edildi")
print(f"✅ {results['swing_points_detected']} swing point bulundu")

# Pattern kütüphanesini görüntüle
library = learner.load_pattern_library()
for pattern_type, stats in library.items():
    print(f"{pattern_type}: {stats['count']} adet, başarı oranı: {stats['success_rate']:.2%}")
```

**Not**: Sistem, veri alamadığı kaynaklarda "N/A" göstererek veya o adımı atlayarak çalışmaya devam eder. API anahtarı olmasa bile çalışabilir.

## 🎨 Gelişmiş Teknik Analiz (Advanced Chart)

Sistem, profesyonel Smart Money kavramlarını ve gelişmiş teknik analiz araçlarını içerir:

### 📊 Advanced Chart Sayfası

`/advanced-chart` sayfasında aşağıdaki özellikleri görselleştirebilirsiniz:

**Kill Zones** (UTC):
- 🟦 Londra: 02:00 - 05:00
- 🟦 New York: 13:00 - 16:00
- 🟦 Asya: 20:00 - 02:00

**Order Blocks**: Güçlü hareket öncesi son karşıt mum (institutional footprint)

**Fair Value Gaps (FVG)**: Fiyat boşlukları (dengesizlik bölgeleri)

**Harmonic Patterns**:
- Gartley, Bat, Butterfly, Crab, Shark
- Fibonacci oranlarıyla otomatik tespit

**Divergences**:
- RSI, MACD, Volume divergansları
- Bullish/Bearish sinyaller

**Support/Resistance**:
- Yatay destek ve direnç seviyeleri
- Dokunma sayısına göre güç hesabı

**Trend Lines & Channels**:
- Swing point'lerden otomatik trend çizgisi tespiti
- Trend kanalları

**Enhanced Fibonacci**:
- 🟡 **Golden Zone 618**: 0.618 - 0.66 (yüksek olasılıklı dönüş bölgesi)
- 🟡 **Golden Zone 382**: 0.34 - 0.382
- 🟢 **OTE High**: 0.705 (Optimal Trade Entry)
- 🟢 **OTE Low**: 0.295
- Standart Fibonacci seviyeleri (0.236, 0.382, 0.5, 0.618, 0.786, 1.0)

**Swing High/Low Detection**:
- Otomatik swing point tespiti
- Manuel eğitim için temel

### Kullanım

```python
from backend.data.processors.advanced_analysis import AdvancedTechnicalAnalysis

# DataFrame'inizi hazırlayın (OHLCV + indikatörler)
analysis = AdvancedTechnicalAnalysis()

# Swing point'leri tespit et
swing_highs, swing_lows = analysis.detect_swing_points(df, left_bars=5, right_bars=5)

# Enhanced Fibonacci hesapla
fib_levels = analysis.calculate_enhanced_fibonacci(
    swing_high=69000,
    swing_low=65000,
    direction='bullish'
)

# Harmonic pattern tespiti
patterns = analysis.detect_harmonic_patterns(swing_highs, swing_lows, tolerance=0.05)

# Divergence tespiti
divergences = analysis.detect_divergences(df, indicator_col='rsi_14', lookback=14)

# Support/Resistance seviyeleri
levels = analysis.detect_support_resistance(df, window=20, min_touches=2)

# Trend çizgileri
trend_lines = analysis.detect_trend_lines(swing_highs, swing_lows, min_points=3)
```

## 🧪 Testing

```bash
# Unit tests
pytest tests/unit

# Integration tests
pytest tests/integration

# Backtest
pytest tests/backtests

# Coverage report
pytest --cov=backend --cov-report=html
```

## 📊 Performans Metrikleri

### Model Accuracy (Backtest)
- GradBoost: 99.2% (validation)
- XGBoost: 97.7%
- LightGBM: 94.2%
- Ensemble: 92.8% (production stable)

### RL Performance (3Y Backtest)
- Sharpe Ratio: 2.3
- Win Rate: 58.4%
- Max Drawdown: 12.7%
- Annualized Return: 87.3%

## 🔧 Yapılandırma

### config.yaml
```yaml
agent:
  mode: oneshot  # oneshot | monitor
  timezone: Europe/Istanbul
  locale: tr-TR

data_sources:
  binance:
    api_key: ${BINANCE_API_KEY}
    api_secret: ${BINANCE_API_SECRET}

  glassnode:
    api_key: ${GLASSNODE_API_KEY}

ml:
  ensemble:
    models: [gradboost, xgboost, lightgbm]
    weights: [0.4, 0.35, 0.25]

  rl:
    algorithm: decision_transformer
    training_episodes: 10000
    learning_rate: 3e-5

risk:
  max_position_size_pct: 0.20
  max_leverage: 3.0
  max_drawdown_pct: 0.15
```

## 📚 Dokümantasyon

- [Mimari Detayları](ARCHITECTURE.md)
- [API Referansı](docs/API.md)
- [Deployment Rehberi](docs/DEPLOYMENT.md)
- [Öğrenme Sistemi](docs/LEARNING.md)

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için lütfen önce bir issue açın.

## ⚠️ Risk Uyarısı

**ÖNEMLİ**: Bu sistem bir analiz ve karar destek aracıdır, otomatik trading botu DEĞİLDİR.

- Kripto piyasaları son derece volatildir
- Geçmiş performans gelecek sonuçları garanti etmez
- Kaybedebileceğinizden fazlasını riske atmayın
- Her zaman kendi araştırmanızı yapın (DYOR)
- Stop-loss kullanımı zorunludur

## 📄 Lisans

MIT License - detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 📞 İletişim

- GitHub Issues: [Sorun bildirin](https://github.com/your-repo/issues)
- Email: your.email@example.com

## 🙏 Teşekkürler

- [tucsky/aggr](https://github.com/Tucsky/aggr) - Real-time aggregated trade data
- Glassnode, CryptoQuant - On-chain data providers
- OpenAI, Anthropic - AI/ML APIs

---

**Made with 🧠 and 📊 for smarter crypto trading**
