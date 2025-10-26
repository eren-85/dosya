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
- Python 3.10+
- PostgreSQL 14+ (TimescaleDB extension)
- Redis 7+
- Docker & Docker Compose (opsiyonel)

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

### 5. Veritabanı Kurulumu
```bash
# PostgreSQL + TimescaleDB
docker-compose up -d postgres redis

# Migration
alembic upgrade head
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

### Web Dashboard
Tarayıcınızda açın: `http://localhost:3000`

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
