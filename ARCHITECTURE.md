# 🏗️ SIGMA ANALYST - Sistem Mimarisi ve Teknik Öneriler

## 📊 PROJE GENEL BAKIŞ

**Sigma Analyst**: AI-powered Kripto Piyasa Analiz ve İstihbarat Sistemi

### Temel Özellikler
- 🤖 Multi-role AI Agent (5 farklı uzmanlık rolü)
- 📈 Gerçek zamanlı teknik, on-chain ve türev piyasa analizi
- 🧠 Reinforcement Learning ile sürekli öğrenme
- 📱 Modern React-based dashboard
- ⚡ Real-time monitoring ve alerting
- 🎯 Trade fırsatı tespiti ve risk yönetimi

---

## 🎯 1. YANIT: "LSTM, XGBoost, Transformer'ların RL ile Bağlantısı"

### ✅ DOĞRU YAKLAŞIM: Ensemble + RL Hibrit Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                    VERİ KATMANI                              │
│  (Binance, Glassnode, CryptoQuant, Aggr, Coinalyze)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              ÖZELLİK MÜHENDİSLİĞİ (Feature Engineering)     │
│  • Teknik indikatörler (200+ features)                      │
│  • On-chain metrikler                                        │
│  • Market microstructure                                     │
│  • Sentiment scores                                          │
└────────────────────┬────────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐   ┌──────────────────────┐
│  SUPERVISED ML   │   │  UNSUPERVISED ML     │
│  (Tahmin Layer)  │   │  (Pattern/Regime)    │
├──────────────────┤   ├──────────────────────┤
│ • GradBoost      │   │ • Clustering         │
│ • XGBoost        │   │ • Anomaly Detection  │
│ • LightGBM       │   │ • PCA/t-SNE          │
│ • RandomForest   │   │                      │
│                  │   │                      │
│ ÇIKIŞ:          │   │ ÇIKIŞ:              │
│ - Fiyat tahmin  │   │ - Market regime     │
│ - Trend prob.   │   │ - Pattern clusters  │
│ - Volatility    │   │ - Anomalies         │
└────────┬─────────┘   └──────────┬───────────┘
         │                        │
         └────────┬───────────────┘
                  ▼
         ┌─────────────────────┐
         │  ENSEMBLE LAYER     │
         │  (Meta-learner)     │
         │  Weighted Combine   │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────────────────────┐
         │     REINFORCEMENT LEARNING LAYER    │
         │     (Decision Transformer + PPO)    │
         ├─────────────────────────────────────┤
         │  STATE:                             │
         │   - Ensemble tahminleri             │
         │   - Market regime                   │
         │   - Portfolio durumu                │
         │   - Risk metrikleri                 │
         │                                     │
         │  ACTION SPACE:                      │
         │   - LONG (0-100% position)         │
         │   - SHORT (0-100% position)        │
         │   - HOLD                            │
         │   - CLOSE                           │
         │                                     │
         │  REWARD:                            │
         │   R = PnL - λ₁·Risk - λ₂·DrawDown  │
         └──────────┬──────────────────────────┘
                    │
                    ▼
         ┌─────────────────────────┐
         │  CLAUDE REASONING       │
         │  (Final Decision)       │
         │  • RL önerisi + context │
         │  • Risk kontrolü        │
         │  • Psikoloji analizi    │
         │  • RAG knowledge        │
         └─────────────────────────┘
```

### 🔗 BAĞLANTI AÇIKLAMASI:

**1. Supervised ML (XGBoost, LightGBM, LSTM, Transformer) ROLÜ:**
- ❌ Doğrudan trade kararı VERMEZLER
- ✅ RL agent'a **STATE bilgisi** sağlarlar
- ✅ RL agent'ın öğrenmesini **hızlandırırlar** (warm start)

**2. RL'nin Supervised ML Çıktılarını Kullanma Şekli:**

```python
# ÖRNEK STATE VECTOR (RL INPUT)
state = {
    # Supervised tahminler
    "xgb_price_pred_1h": 67234.5,        # XGBoost 1h fiyat tahmini
    "lgbm_trend_prob": 0.73,             # LightGBM trend olasılığı
    "lstm_volatility": 0.042,            # LSTM volatilite tahmini
    "transformer_pattern": "bullish_flag", # Pattern recognition

    # Market features
    "current_price": 67100,
    "rsi_14": 58.3,
    "funding_rate": 0.01,

    # Portfolio state
    "position": 0.5,  # %50 long
    "unrealized_pnl": 234.5,

    # Risk metrics
    "var_95": -1234,
    "sharpe_ratio": 1.8
}

# RL AGENT bu state'e bakarak ACTION karar verir
action = rl_agent.decide(state)  # → "HOLD" veya "INCREASE_LONG" vb.
```

**3. NEDEN BU HİBRİT YAKLAŞIM ÜSTÜNDÜr:**

| Yöntem | Avantaj | Dezavantaj |
|--------|---------|------------|
| **Sadece Supervised** | Tahmin hızlı, basit | Dinamik karar verme yok, piyasa değişimlerine uyum yavaş |
| **Sadece RL** | Adaptif, optimal strateji öğrenir | Convergence çok yavaş, çok veri gerekir |
| **HİBRİT (ÖNERİMİZ)** | ✅ Supervised hızlı insight + RL optimal karar | Kompleks sistem |

---

## 🧠 2. RL MEKANİZMASI: Decision Transformer + PPO Fine-tuning

### A. NEDEN DECISION TRANSFORMER?

**Klasik RL (DQN, PPO) Problemi:**
```
t=0: State → Action → Reward = -5
t=1: State → Action → Reward = -3
t=2: State → Action → Reward = +10  ← Bu reward'a ulaşmak için önceki -5, -3'ü görmesi gerek
```
→ Kredi atama problemi (credit assignment) kripto'da çok zor çünkü:
- Position açma ve kapama arasında 100+ timestep var
- Gecikmeli ödüller (delayed rewards)

**Decision Transformer Çözümü:**
```python
# Transformer, geçmiş trajectory'yi bütünsel görür
trajectory = [
    (s₀, a₀, r₀),
    (s₁, a₁, r₁),
    ...,
    (sₙ, aₙ, rₙ)
]

# TARGET RETURN ile koşullandırma
action = DecisionTransformer(
    states=trajectory_states,
    actions=trajectory_actions,
    returns_to_go=target_return  # ← "Toplam +50% PnL istiyorum"
)
```

### B. MİMARİ DETAY

```python
# models/rl/decision_transformer.py

import torch
import torch.nn as nn
from transformers import GPT2Config, GPT2Model

class CryptoDecisionTransformer(nn.Module):
    def __init__(
        self,
        state_dim=256,         # Supervised ML + market features
        action_dim=4,          # LONG, SHORT, HOLD, CLOSE
        hidden_size=768,
        num_layers=6,
        num_heads=8,
        context_length=50      # Son 50 timestep'i hatırla
    ):
        super().__init__()

        # GPT-2 benzeri transformer backbone
        config = GPT2Config(
            n_embd=hidden_size,
            n_layer=num_layers,
            n_head=num_heads,
            n_positions=context_length * 3  # (s,a,r) üçlüleri
        )
        self.transformer = GPT2Model(config)

        # Embedding layers
        self.state_encoder = nn.Linear(state_dim, hidden_size)
        self.action_encoder = nn.Embedding(action_dim, hidden_size)
        self.return_encoder = nn.Linear(1, hidden_size)
        self.timestep_encoder = nn.Embedding(context_length, hidden_size)

        # Output head
        self.action_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_dim)
        )

        self.context_length = context_length

    def forward(self, states, actions, returns_to_go, timesteps):
        B, T, _ = states.shape

        # Embeddings
        state_emb = self.state_encoder(states)
        action_emb = self.action_encoder(actions)
        return_emb = self.return_encoder(returns_to_go.unsqueeze(-1))
        time_emb = self.timestep_encoder(timesteps)

        # Interleave: (R_0, s_0, a_0, R_1, s_1, a_1, ...)
        sequence = torch.stack([
            return_emb, state_emb, action_emb
        ], dim=2).reshape(B, 3 * T, -1)

        # Add time embeddings
        sequence = sequence + time_emb.repeat_interleave(3, dim=1)

        # Transformer forward
        transformer_out = self.transformer(inputs_embeds=sequence).last_hidden_state

        # Extract action predictions
        action_logits = self.action_head(transformer_out[:, 1::3])  # s pozisyonları

        return action_logits


# PPO Fine-tuning wrapper
class PPOFineTuner:
    def __init__(self, dt_model, learning_rate=3e-5):
        self.dt_model = dt_model
        self.optimizer = torch.optim.AdamW(dt_model.parameters(), lr=learning_rate)
        self.clip_epsilon = 0.2

    def update(self, trajectories, advantages):
        """PPO objective ile fine-tune"""
        for epoch in range(4):  # PPO epochs
            for batch in trajectories:
                # Compute policy ratio
                old_log_probs = batch['log_probs']
                new_logits = self.dt_model(
                    batch['states'],
                    batch['actions'],
                    batch['returns_to_go'],
                    batch['timesteps']
                )
                new_log_probs = torch.log_softmax(new_logits, dim=-1)

                ratio = torch.exp(new_log_probs - old_log_probs)

                # PPO clipped objective
                clipped_ratio = torch.clamp(ratio, 1 - self.clip_epsilon, 1 + self.clip_epsilon)
                loss = -torch.min(
                    ratio * advantages,
                    clipped_ratio * advantages
                ).mean()

                # Backward
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.dt_model.parameters(), 1.0)
                self.optimizer.step()
```

### C. EĞİTİM SÜRECİ

```python
# training/rl_training.py

def train_decision_transformer():
    """
    ÜÇ AŞAMALI EĞİTİM
    """

    # AŞAMA 1: Offline Pre-training (Historical Data)
    print("AŞAMA 1: Offline BC (Behavioral Cloning) - Expert demonstrations")
    # Geçmiş başarılı trade'leri taklit et
    for epoch in range(100):
        for batch in expert_trajectories:  # İyi performans gösteren geçmiş trade'ler
            loss = behavioral_cloning_loss(model, batch)
            loss.backward()
            optimizer.step()

    # AŞAMA 2: Online Fine-tuning (Simüle Backtest)
    print("AŞAMA 2: Online RL - Simulated trading")
    env = BacktestEnv(historical_data)  # Simülasyon ortamı
    for episode in range(10000):
        trajectory = collect_trajectory(env, model, target_return=0.15)  # %15 hedef
        returns = compute_returns(trajectory)

        # Decision Transformer güncelle
        model_loss = dt_loss(model, trajectory, returns)
        model_loss.backward()
        optimizer.step()

    # AŞAMA 3: PPO Fine-tuning (Risk-adjusted optimization)
    print("AŞAMA 3: PPO fine-tuning - Risk kontrolü")
    ppo = PPOFineTuner(model)
    for iteration in range(1000):
        trajectories = collect_multiple_trajectories(env, model, n=16)
        advantages = compute_gae(trajectories)  # Generalized Advantage Estimation
        ppo.update(trajectories, advantages)
```

---

## 💾 3. BELLEK VE STATE MANAGEMENT ÖNERİSİ

### A. HİBRİT BELLEK SİSTEMİ

```
┌─────────────────────────────────────────────────────────────┐
│                  ÇOKLU BELLEK SİSTEMİ                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  SHORT-TERM      │  │  WORKING MEMORY  │                │
│  │  (Redis)         │  │  (In-Memory)     │                │
│  ├──────────────────┤  ├──────────────────┤                │
│  │ • Live prices    │  │ • Current state  │                │
│  │ • Recent trades  │  │ • Active orders  │                │
│  │ • Order book     │  │ • Risk metrics   │                │
│  │ TTL: 1 hour      │  │ Volatile         │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────────────────────────┐                   │
│  │  MEDIUM-TERM (PostgreSQL TimescaleDB)│                   │
│  ├──────────────────────────────────────┤                   │
│  │ • OHLCV candles (compress after 30d) │                   │
│  │ • Indicators (RSI, MACD, etc.)       │                   │
│  │ • Trade history                       │                   │
│  │ • Model predictions                   │                   │
│  │ Retention: 2 years                    │                   │
│  └──────────────────────────────────────┘                   │
│                                                              │
│  ┌──────────────────────────────────────┐                   │
│  │  LONG-TERM KNOWLEDGE (Vector DB)     │                   │
│  ├──────────────────────────────────────┤                   │
│  │ • RAG embeddings (PDF içerikler)     │                   │
│  │ • Pattern library                     │                   │
│  │ • Historical regime data              │                   │
│  │ • Model checkpoints                   │                   │
│  │ DB: Pinecone / Weaviate              │                   │
│  └──────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### B. IMPLEMENTATION

```python
# core/memory/memory_manager.py

from redis import Redis
from sqlalchemy import create_engine
from pinecone import Pinecone
import pandas as pd

class MemoryManager:
    """Hibrit bellek yöneticisi"""

    def __init__(self):
        # Short-term: Redis
        self.redis = Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )

        # Medium-term: TimescaleDB
        self.timescale = create_engine('postgresql://user:pass@localhost/sigma_db')

        # Long-term: Pinecone
        self.vector_db = Pinecone(api_key="...")
        self.index = self.vector_db.Index("sigma-knowledge")

        # In-memory cache
        self.working_memory = {
            'current_state': {},
            'active_positions': {},
            'pending_orders': []
        }

    # ===== SHORT-TERM OPERATIONS =====
    def cache_price(self, symbol: str, price: float, ttl: int = 3600):
        """Cache live price with TTL"""
        self.redis.setex(f"price:{symbol}", ttl, price)

    def get_recent_trades(self, symbol: str, limit: int = 100):
        """Get recent trades from Redis"""
        return self.redis.lrange(f"trades:{symbol}", 0, limit - 1)

    # ===== MEDIUM-TERM OPERATIONS =====
    def store_candle(self, symbol: str, timeframe: str, candle: dict):
        """Store OHLCV to TimescaleDB"""
        query = """
        INSERT INTO candles (symbol, timeframe, timestamp, open, high, low, close, volume)
        VALUES (%(symbol)s, %(timeframe)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
        ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
        """
        with self.timescale.connect() as conn:
            conn.execute(query, {
                'symbol': symbol,
                'timeframe': timeframe,
                **candle
            })

    def get_historical_candles(self, symbol: str, timeframe: str,
                               start: str, end: str) -> pd.DataFrame:
        """Retrieve historical OHLCV"""
        query = """
        SELECT * FROM candles
        WHERE symbol = %(symbol)s
          AND timeframe = %(timeframe)s
          AND timestamp BETWEEN %(start)s AND %(end)s
        ORDER BY timestamp ASC
        """
        return pd.read_sql(query, self.timescale, params={
            'symbol': symbol,
            'timeframe': timeframe,
            'start': start,
            'end': end
        })

    # ===== LONG-TERM KNOWLEDGE =====
    def store_pattern(self, pattern_name: str, embedding: list, metadata: dict):
        """Store learned pattern to vector DB"""
        self.index.upsert(vectors=[{
            'id': pattern_name,
            'values': embedding,
            'metadata': metadata
        }])

    def search_similar_patterns(self, current_embedding: list, top_k: int = 5):
        """RAG: Find similar historical patterns"""
        results = self.index.query(
            vector=current_embedding,
            top_k=top_k,
            include_metadata=True
        )
        return results['matches']

    # ===== WORKING MEMORY =====
    def update_state(self, key: str, value):
        """Update current agent state"""
        self.working_memory['current_state'][key] = value

    def get_state(self) -> dict:
        """Get full current state"""
        return {
            **self.working_memory['current_state'],
            'positions': self.working_memory['active_positions'],
            'orders': self.working_memory['pending_orders']
        }
```

### C. STATE PERSISTENCE STRATEGY

```python
# core/state/state_manager.py

class StatePersistence:
    """Agent state'ini güvenli şekilde sakla/geri yükle"""

    def save_checkpoint(self, agent_state: dict, checkpoint_id: str):
        """
        Checkpoint içeriği:
        - Model weights
        - Optimizer state
        - Memory buffers
        - Performance metrics
        """
        checkpoint = {
            'timestamp': datetime.utcnow(),
            'agent_state': agent_state,
            'model_state': self.model.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'metrics': self.get_current_metrics()
        }

        # S3 / local disk'e kaydet
        torch.save(checkpoint, f"checkpoints/{checkpoint_id}.pt")

    def load_checkpoint(self, checkpoint_id: str):
        """Checkpoint'ten geri yükle"""
        checkpoint = torch.load(f"checkpoints/{checkpoint_id}.pt")

        self.model.load_state_dict(checkpoint['model_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])

        return checkpoint['agent_state']
```

---

## 🔬 4. BACKTEST SİSTEMİ MİMARİSİ

### A. EVENT-DRIVEN BACKTEST ENGINE

```python
# backtest/engine.py

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

@dataclass
class Order:
    symbol: str
    side: str  # 'buy' / 'sell'
    quantity: float
    price: float
    timestamp: datetime
    order_type: str  # 'market' / 'limit'

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float

class BacktestEngine:
    """
    Gerçekçi backtest ortamı:
    - Slippage simulation
    - Commission fees
    - Market impact modeling
    - Partial fills
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.0004,  # %0.04
        slippage_model: str = 'volume_based'
    ):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_model = slippage_model

        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.trades: List[Dict] = []

        self.equity_curve = []
        self.current_time = None

    def load_data(self, symbols: List[str], start: str, end: str):
        """Mum verilerini yükle"""
        self.data = {}
        for symbol in symbols:
            # TimescaleDB'den çek
            df = memory_manager.get_historical_candles(
                symbol=symbol,
                timeframe='1m',  # En düşük granülarite
                start=start,
                end=end
            )
            self.data[symbol] = df

    def calculate_slippage(self, symbol: str, side: str, quantity: float) -> float:
        """
        Gerçekçi slippage hesapla
        - Market depth'e göre
        - Volatility'ye göre
        """
        if self.slippage_model == 'volume_based':
            current_bar = self.data[symbol].loc[self.current_time]
            volume = current_bar['volume']

            # Eğer işlem hacmi toplam hacmin %1'inden fazlaysa impact var
            impact_ratio = (quantity / volume) * 100
            slippage_pct = min(impact_ratio * 0.1, 0.5)  # Max %0.5 slippage

            return slippage_pct / 100

        return 0.0001  # Sabit %0.01 default

    def execute_order(self, order: Order) -> bool:
        """Emir çalıştır (komisyon + slippage ile)"""
        slippage = self.calculate_slippage(order.symbol, order.side, order.quantity)

        if order.side == 'buy':
            execution_price = order.price * (1 + slippage)
        else:
            execution_price = order.price * (1 - slippage)

        commission = order.quantity * execution_price * self.commission_rate
        total_cost = (order.quantity * execution_price) + commission

        # Sermaye kontrolü
        if order.side == 'buy' and total_cost > self.capital:
            print(f"Insufficient capital for {order}")
            return False

        # Position güncelle
        if order.side == 'buy':
            if order.symbol in self.positions:
                pos = self.positions[order.symbol]
                new_quantity = pos.quantity + order.quantity
                new_entry = (pos.entry_price * pos.quantity + execution_price * order.quantity) / new_quantity
                pos.quantity = new_quantity
                pos.entry_price = new_entry
            else:
                self.positions[order.symbol] = Position(
                    symbol=order.symbol,
                    quantity=order.quantity,
                    entry_price=execution_price,
                    current_price=execution_price,
                    unrealized_pnl=0
                )

            self.capital -= total_cost

        else:  # sell
            if order.symbol not in self.positions:
                print(f"No position to sell for {order.symbol}")
                return False

            pos = self.positions[order.symbol]
            sell_quantity = min(order.quantity, pos.quantity)

            realized_pnl = (execution_price - pos.entry_price) * sell_quantity - commission
            self.capital += sell_quantity * execution_price - commission

            pos.quantity -= sell_quantity
            if pos.quantity <= 0:
                del self.positions[order.symbol]

            self.trades.append({
                'timestamp': self.current_time,
                'symbol': order.symbol,
                'side': 'sell',
                'quantity': sell_quantity,
                'price': execution_price,
                'pnl': realized_pnl
            })

        return True

    def run(self, agent, start_date: str, end_date: str):
        """Backtest döngüsü"""
        timestamps = pd.date_range(start_date, end_date, freq='1min')

        for ts in timestamps:
            self.current_time = ts

            # Pozisyonları güncelle
            for symbol, pos in self.positions.items():
                try:
                    current_price = self.data[symbol].loc[ts, 'close']
                    pos.current_price = current_price
                    pos.unrealized_pnl = (current_price - pos.entry_price) * pos.quantity
                except KeyError:
                    continue

            # Toplam equity hesapla
            total_equity = self.capital + sum(
                pos.quantity * pos.current_price for pos in self.positions.values()
            )
            self.equity_curve.append({
                'timestamp': ts,
                'equity': total_equity,
                'cash': self.capital,
                'positions_value': total_equity - self.capital
            })

            # Agent'tan state al
            state = self.build_state(ts)

            # Agent karar ver
            action = agent.decide(state)

            # Action'ı emirlere çevir
            if action['type'] == 'LONG':
                order = Order(
                    symbol=action['symbol'],
                    side='buy',
                    quantity=action['quantity'],
                    price=self.data[action['symbol']].loc[ts, 'close'],
                    timestamp=ts,
                    order_type='market'
                )
                self.execute_order(order)

            elif action['type'] == 'SHORT':
                # Short için satış
                pass

            # Risk kontrolü - her 1000 bar'da checkpoint
            if len(self.equity_curve) % 1000 == 0:
                self.save_checkpoint()

    def build_state(self, timestamp) -> dict:
        """Agent için state oluştur"""
        # Teknik indikatörler, on-chain vb. hesapla
        state = {
            'timestamp': timestamp,
            'prices': {},
            'indicators': {},
            'positions': self.positions,
            'capital': self.capital
        }

        for symbol in self.data.keys():
            try:
                current_bar = self.data[symbol].loc[timestamp]
                state['prices'][symbol] = current_bar['close']
                # ... daha fazla feature
            except KeyError:
                continue

        return state

    def get_performance_metrics(self) -> dict:
        """Performans metrikleri"""
        equity_df = pd.DataFrame(self.equity_curve)

        returns = equity_df['equity'].pct_change().dropna()

        total_return = (equity_df['equity'].iloc[-1] / self.initial_capital - 1) * 100
        sharpe = returns.mean() / returns.std() * (365 * 24 * 60) ** 0.5  # Yıllık Sharpe

        max_drawdown = self.calculate_max_drawdown(equity_df['equity'])

        win_trades = [t for t in self.trades if t.get('pnl', 0) > 0]
        win_rate = len(win_trades) / len(self.trades) if self.trades else 0

        return {
            'total_return_pct': total_return,
            'sharpe_ratio': sharpe,
            'max_drawdown_pct': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'final_equity': equity_df['equity'].iloc[-1]
        }

    def calculate_max_drawdown(self, equity_series):
        """Maximum drawdown hesapla"""
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax * 100
        return drawdown.min()
```

### B. WALK-FORWARD OPTIMIZATION

```python
# backtest/walk_forward.py

class WalkForwardOptimizer:
    """
    Rolling window ile model optimization

    ├─ Train ──┤─ Validate ─┤
              ├─ Train ──┤─ Validate ─┤
                        ├─ Train ──┤─ Validate ─┤
    """

    def __init__(self, train_period_days=180, test_period_days=30):
        self.train_period = train_period_days
        self.test_period = test_period_days

    def run(self, start_date, end_date, agent):
        """Walk-forward test"""
        results = []

        current_start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        while current_start < end:
            train_end = current_start + pd.Timedelta(days=self.train_period)
            test_end = train_end + pd.Timedelta(days=self.test_period)

            if test_end > end:
                break

            print(f"Training: {current_start} to {train_end}")
            # Agent'ı train et
            agent.train(start=current_start, end=train_end)

            print(f"Testing: {train_end} to {test_end}")
            # Test et
            backtest = BacktestEngine()
            backtest.load_data(['BTCUSDT'], train_end, test_end)
            backtest.run(agent, train_end, test_end)

            metrics = backtest.get_performance_metrics()
            results.append({
                'test_period_start': train_end,
                'test_period_end': test_end,
                **metrics
            })

            # Sonraki window'a geç
            current_start = train_end

        return pd.DataFrame(results)
```

---

## 📚 5. VERİ KAYNAĞI ENTEGRASYONU

### A. AGGREGATOR PATTERN

```python
# data/sources/aggregator.py

from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio

class DataSource(ABC):
    """Abstract base class for data sources"""

    @abstractmethod
    async def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int):
        pass

    @abstractmethod
    async def fetch_orderbook(self, symbol: str, depth: int):
        pass

class BinanceSource(DataSource):
    async def fetch_ohlcv(self, symbol, timeframe, limit):
        # Binance API çağrısı
        pass

class GlassnodeSource(DataSource):
    async def fetch_onchain_metric(self, metric: str):
        # Glassnode API
        pass

# ... Diğer kaynaklar (OKX, Bybit, CryptoQuant, vb.)

class DataAggregator:
    """Tüm kaynaklardan veri topla ve birleştir"""

    def __init__(self):
        self.sources = {
            'binance': BinanceSource(),
            'okx': OKXSource(),
            'glassnode': GlassnodeSource(),
            'cryptoquant': CryptoQuantSource(),
            'aggr': AggrSource(),  # tucsky/aggr entegrasyonu
            'coinalyze': CoinalyzeSource()
        }

    async def fetch_all_ohlcv(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Paralel olarak tüm kaynaklardan çek, birleştir"""
        tasks = [
            source.fetch_ohlcv(symbol, timeframe, 500)
            for name, source in self.sources.items()
            if hasattr(source, 'fetch_ohlcv')
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Merge ve outlier filtering
        combined_df = self.merge_ohlcv(results)
        return combined_df

    def merge_ohlcv(self, dataframes: List[pd.DataFrame]) -> pd.DataFrame:
        """
        Birden fazla kaynaktan gelen OHLCV'yi birleştir
        - Timestamp alignment
        - Median price kullan (outlier'lara karşı robust)
        """
        merged = pd.concat(dataframes, axis=0)
        merged = merged.groupby('timestamp').agg({
            'open': 'median',
            'high': 'max',
            'low': 'min',
            'close': 'median',
            'volume': 'sum'
        })
        return merged
```

### B. TUCSKY/AGGR ENTEGRASYONU

```python
# data/sources/aggr_client.py

import websocket
import json

class AggrWebSocketClient:
    """
    tucsky/aggr WebSocket client
    Real-time trade aggregation
    """

    def __init__(self, url="wss://api.aggr.trade"):
        self.url = url
        self.ws = None
        self.subscriptions = []

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        self.ws.run_forever()

    def on_open(self, ws):
        # Subscribe to symbols
        subscribe_msg = {
            "op": "subscribe",
            "args": ["BINANCE:BTCUSDT", "OKEX:BTC-USDT"]
        }
        ws.send(json.dumps(subscribe_msg))

    def on_message(self, ws, message):
        data = json.loads(message)

        # Process aggregated trade data
        if data['type'] == 'trade':
            self.handle_trade(data)

        elif data['type'] == 'liquidation':
            self.handle_liquidation(data)

    def handle_trade(self, trade_data):
        """
        Aggregated trade verisi:
        - Exchange
        - Price
        - Size
        - Side (buy/sell)
        - Timestamp
        """
        # Redis'e yaz
        memory_manager.redis.lpush(
            f"trades:{trade_data['symbol']}",
            json.dumps(trade_data)
        )
        memory_manager.redis.ltrim(f"trades:{trade_data['symbol']}", 0, 999)  # Son 1000
```

---

## 🎨 6. REACT UI MİMARİSİ

### A. COMPONENT HIERARCHY

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Dashboard.tsx          # Ana dashboard
│   │   ├── Analysis.tsx           # Detaylı analiz sayfası
│   │   ├── Backtest.tsx           # Backtest interface
│   │   ├── Settings.tsx           # Ayarlar
│   │   └── Alerts.tsx             # Uyarılar
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── Layout.tsx
│   │   │
│   │   ├── charts/
│   │   │   ├── TradingViewChart.tsx     # Ana fiyat grafiği
│   │   │   ├── EquityCurve.tsx          # Equity curve
│   │   │   ├── HeatMap.tsx              # Korelasyon/flow heatmap
│   │   │   └── VolumeProfile.tsx
│   │   │
│   │   ├── widgets/
│   │   │   ├── MarketPulse.tsx          # Genel sentiment
│   │   │   ├── FlowWidget.tsx           # Nakit akışı
│   │   │   ├── OnChainMetrics.tsx       # On-chain data
│   │   │   ├── ScenarioCard.tsx         # Bull/Base/Bear senaryolar
│   │   │   ├── AlertsList.tsx           # Aktif uyarılar
│   │   │   └── PositionsTable.tsx       # Açık pozisyonlar
│   │   │
│   │   └── common/
│   │       ├── Card.tsx
│   │       ├── Button.tsx
│   │       ├── Badge.tsx
│   │       └── Modal.tsx
│   │
│   ├── hooks/
│   │   ├── useWebSocket.ts              # Real-time data
│   │   ├── useBacktest.ts
│   │   └── useAnalysis.ts
│   │
│   ├── services/
│   │   ├── api.ts                       # Backend API client
│   │   └── websocket.ts
│   │
│   ├── store/                           # Redux/Zustand
│   │   ├── slices/
│   │   │   ├── marketSlice.ts
│   │   │   ├── analysisSlice.ts
│   │   │   └── backtestSlice.ts
│   │   └── store.ts
│   │
│   └── types/
│       └── index.ts                     # TypeScript types
```

### B. UI MOCKUP & DESIGN

```typescript
// src/pages/Dashboard.tsx

import React from 'react';
import { Grid, Card, Typography } from '@mui/material';
import TradingViewChart from '../components/charts/TradingViewChart';
import MarketPulse from '../components/widgets/MarketPulse';
import FlowWidget from '../components/widgets/FlowWidget';
import ScenarioCard from '../components/widgets/ScenarioCard';

const Dashboard: React.FC = () => {
  return (
    <Grid container spacing={3}>
      {/* Top Row: Market Pulse + Key Metrics */}
      <Grid item xs={12} md={8}>
        <MarketPulse />
      </Grid>
      <Grid item xs={12} md={4}>
        <FlowWidget />
      </Grid>

      {/* Main Chart */}
      <Grid item xs={12} lg={8}>
        <Card sx={{ height: 600 }}>
          <TradingViewChart symbol="BTCUSDT" />
        </Card>
      </Grid>

      {/* Scenarios */}
      <Grid item xs={12} lg={4}>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <ScenarioCard type="bull" />
          </Grid>
          <Grid item xs={12}>
            <ScenarioCard type="base" />
          </Grid>
          <Grid item xs={12}>
            <ScenarioCard type="bear" />
          </Grid>
        </Grid>
      </Grid>

      {/* On-Chain Metrics */}
      <Grid item xs={12}>
        <OnChainMetrics />
      </Grid>
    </Grid>
  );
};

export default Dashboard;
```

### C. REAL-TIME DATA FLOW

```typescript
// src/hooks/useWebSocket.ts

import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  volume: number;
  timestamp: string;
}

export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const socketInstance = io(url);

    socketInstance.on('connect', () => {
      console.log('WebSocket connected');
    });

    // Real-time price updates
    socketInstance.on('market_update', (data: MarketData) => {
      setMarketData(data);
    });

    // Alert notifications
    socketInstance.on('alert', (alert) => {
      setAlerts((prev) => [alert, ...prev].slice(0, 50));
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [url]);

  return { socket, marketData, alerts };
};
```

---

## 🎯 7. PDF ÖĞRENME SİSTEMİ (RAG)

```python
# learning/pdf_processor.py

import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

class PDFLearningSystem:
    """
    PDF'lerden öğrenen RAG sistemi
    """

    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        self.vector_store = Pinecone.from_existing_index("sigma-knowledge", self.embeddings)

    def ingest_pdf(self, pdf_path: str, metadata: dict = None):
        """PDF'i oku ve vector DB'ye ekle"""
        # PDF oku
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()

        # Chunk'lara böl
        chunks = self.text_splitter.split_text(text)

        # Embed ve kaydet
        self.vector_store.add_texts(
            texts=chunks,
            metadatas=[{
                'source': pdf_path,
                **(metadata or {})
            }] * len(chunks)
        )

        print(f"✅ {pdf_path} ingested: {len(chunks)} chunks")

    def query(self, question: str, k: int = 5) -> List[str]:
        """Bilgi bankasından ilgili bilgileri çek"""
        docs = self.vector_store.similarity_search(question, k=k)
        return [doc.page_content for doc in docs]

# Kullanım
pdf_learner = PDFLearningSystem()
pdf_learner.ingest_pdf("books/technical_analysis.pdf", {"category": "technical"})
pdf_learner.ingest_pdf("books/market_psychology.pdf", {"category": "psychology"})

# Agent karar verirken:
context = pdf_learner.query("What is the golden zone in Fibonacci retracement?")
# → RL agent'a ekstra context olarak ver
```

---

## 🚀 8. DEPLOYMENT MİMARİSİ

```
┌─────────────────────────────────────────────────────────────┐
│                       PRODUCTION STACK                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐  │
│  │   NGINX     │─────▶│  Frontend   │     │  Monitoring │  │
│  │  (Reverse   │      │  (React)    │     │  (Grafana)  │  │
│  │   Proxy)    │      │  Port: 3000 │     │             │  │
│  └──────┬──────┘      └─────────────┘     └─────────────┘  │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────────────────────────┐                        │
│  │     FastAPI Backend             │                        │
│  │     (Uvicorn + Gunicorn)        │                        │
│  │     Port: 8000                  │                        │
│  │  ┌──────────────────────────┐   │                        │
│  │  │  /api/analysis           │   │                        │
│  │  │  /api/backtest           │   │                        │
│  │  │  /ws/realtime            │   │                        │
│  │  └──────────────────────────┘   │                        │
│  └────────┬─────────────────────────┘                       │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────┐                │
│  │       WORKER SERVICES (Celery)          │                │
│  ├─────────────────────────────────────────┤                │
│  │  • Data ingestion workers               │                │
│  │  • ML training workers                  │                │
│  │  • Backtest workers                     │                │
│  └──────────┬──────────────────────────────┘                │
│             │                                                │
│             ▼                                                │
│  ┌─────────────────────────────────────────┐                │
│  │         DATA LAYER                      │                │
│  ├─────────────────────────────────────────┤                │
│  │  Redis (Cache + Queue)                  │                │
│  │  PostgreSQL + TimescaleDB               │                │
│  │  Pinecone (Vector DB)                   │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 9. PROJE KLASÖR YAPISI (FİNAL)

```
sigma-analyst/
├── backend/
│   ├── api/
│   │   ├── routers/
│   │   │   ├── analysis.py
│   │   │   ├── backtest.py
│   │   │   ├── data.py
│   │   │   └── alerts.py
│   │   ├── dependencies.py
│   │   └── main.py              # FastAPI app
│   │
│   ├── core/
│   │   ├── config.py            # Settings
│   │   ├── memory/
│   │   │   ├── memory_manager.py
│   │   │   └── state_manager.py
│   │   └── agents/
│   │       ├── sigma_agent.py   # Main agent
│   │       └── roles/
│   │           ├── analyst.py
│   │           ├── intelligence.py
│   │           └── psychologist.py
│   │
│   ├── models/
│   │   ├── ml/
│   │   │   ├── ensemble.py      # GradBoost, XGBoost, LightGBM
│   │   │   ├── lstm.py
│   │   │   └── transformer.py
│   │   ├── rl/
│   │   │   ├── decision_transformer.py
│   │   │   └── ppo.py
│   │   └── schemas/
│   │       └── report.py        # Pydantic models
│   │
│   ├── data/
│   │   ├── sources/
│   │   │   ├── binance.py
│   │   │   ├── glassnode.py
│   │   │   ├── cryptoquant.py
│   │   │   ├── aggr.py
│   │   │   └── aggregator.py
│   │   ├── processors/
│   │   │   ├── technical_indicators.py
│   │   │   ├── onchain.py
│   │   │   └── features.py
│   │   └── downloaders/
│   │       └── candle_downloader.py
│   │
│   ├── backtest/
│   │   ├── engine.py
│   │   ├── walk_forward.py
│   │   └── metrics.py
│   │
│   ├── learning/
│   │   ├── pdf_processor.py     # RAG
│   │   ├── trainer.py           # RL training
│   │   └── evaluator.py
│   │
│   ├── tasks/                   # Celery tasks
│   │   ├── data_tasks.py
│   │   ├── training_tasks.py
│   │   └── monitoring_tasks.py
│   │
│   └── utils/
│       ├── logger.py
│       └── helpers.py
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── pages/               # (yukarıda detaylandırıldı)
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── store/
│   │   └── types/
│   ├── package.json
│   └── tsconfig.json
│
├── notebooks/                   # Jupyter research notebooks
│   ├── exploratory/
│   └── experiments/
│
├── data/                        # Local data storage
│   ├── raw/
│   ├── processed/
│   └── models/                  # Saved model checkpoints
│
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── LEARNING.md
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── backtests/
│
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

---

## ✅ 10. ÖNCELİKLENDİRİLMİŞ UYGULAMA PLANI

### FAZA 1: TEMEL ALT YAPI (Hafta 1-2)
1. ✅ Proje yapısı oluştur
2. ✅ Veri kaynaklarını entegre et (Binance, Glassnode API)
3. ✅ Memory Manager (Redis + PostgreSQL) kur
4. ✅ Basit FastAPI backend
5. ✅ React frontend iskelet

### FAZA 2: ML PİPELİNE (Hafta 3-4)
1. ✅ Feature engineering (teknik indikatörler)
2. ✅ GradBoost + XGBoost + LightGBM ensemble
3. ✅ Backtest engine (basit)
4. ✅ Model eğitimi pipeline

### FAZA 3: RL SİSTEMİ (Hafta 5-6)
1. ✅ Decision Transformer implementasyonu
2. ✅ PPO fine-tuning
3. ✅ Offline BC pre-training
4. ✅ Walk-forward testing

### FAZA 4: CLAUDE ENTEGRASYONu (Hafta 7)
1. ✅ PDF RAG sistemi
2. ✅ Claude Reasoning API entegrasyonu
3. ✅ Multi-role prompt engineering
4. ✅ JSON output formatting

### FAZA 5: UI & DEPLOYMENT (Hafta 8-9)
1. ✅ React dashboard tamamla
2. ✅ WebSocket real-time data
3. ✅ Docker containerization
4. ✅ Production deployment

---

## 🎓 11. ÖĞRENME METRİKLERİ & EVALUATION

```python
# learning/evaluator.py

class ModelEvaluator:
    """
    Model performansını sürekli izle
    """

    def evaluate_ensemble(self, y_true, y_pred_ensemble):
        """Ensemble tahmin kalitesi"""
        from sklearn.metrics import mean_absolute_error, r2_score

        mae = mean_absolute_error(y_true, y_pred_ensemble)
        r2 = r2_score(y_true, y_pred_ensemble)

        return {
            'mae': mae,
            'r2': r2,
            'mape': np.mean(np.abs((y_true - y_pred_ensemble) / y_true)) * 100
        }

    def evaluate_rl_policy(self, trajectories):
        """RL policy performansı"""
        returns = [sum(t['rewards']) for t in trajectories]
        sharpes = [self.calculate_sharpe(t) for t in trajectories]

        return {
            'avg_return': np.mean(returns),
            'avg_sharpe': np.mean(sharpes),
            'win_rate': sum(r > 0 for r in returns) / len(returns)
        }

    def calibration_check(self, predicted_probs, outcomes):
        """
        Model kalibrasyonu - tahmin edilen olasılıklar gerçekle uyumlu mu?
        """
        from sklearn.calibration import calibration_curve

        prob_true, prob_pred = calibration_curve(outcomes, predicted_probs, n_bins=10)

        # Brier Score (düşük = iyi)
        brier = np.mean((predicted_probs - outcomes) ** 2)

        return {
            'brier_score': brier,
            'calibration_curve': (prob_true, prob_pred)
        }
```

---

## 🔒 12. RİSK YÖNETİMİ & GÜVENLİK

```python
# core/risk/risk_manager.py

class RiskManager:
    """
    Trade seviyesinde risk kontrolü
    """

    def __init__(self, max_position_size_pct=0.2, max_leverage=3, max_drawdown_pct=0.15):
        self.max_position_size_pct = max_position_size_pct  # Portföyün max %20'si
        self.max_leverage = max_leverage
        self.max_drawdown_pct = max_drawdown_pct

        self.current_drawdown = 0
        self.peak_equity = 100000

    def validate_order(self, order: Order, current_portfolio: dict) -> tuple[bool, str]:
        """
        Emir risk kontrolünden geçer mi?
        """
        # 1. Position size check
        order_value = order.quantity * order.price
        portfolio_value = current_portfolio['equity']

        if order_value > portfolio_value * self.max_position_size_pct:
            return False, f"Position size exceeds {self.max_position_size_pct*100}% limit"

        # 2. Leverage check
        total_exposure = sum(pos['value'] for pos in current_portfolio['positions'].values())
        if total_exposure + order_value > portfolio_value * self.max_leverage:
            return False, f"Leverage would exceed {self.max_leverage}x"

        # 3. Drawdown circuit breaker
        if self.current_drawdown >= self.max_drawdown_pct:
            return False, f"Circuit breaker: Drawdown {self.current_drawdown*100:.1f}% >= {self.max_drawdown_pct*100}%"

        # 4. Correlation check (aynı yönde çok fazla pozisyon açma)
        correlated_positions = self.get_correlated_positions(order.symbol, current_portfolio)
        if len(correlated_positions) >= 5:
            return False, "Too many correlated positions"

        return True, "OK"

    def update_drawdown(self, current_equity):
        """Drawdown güncelle"""
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity

        self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
```

---

## 🎯 SONUÇ VE ÖNERİLER

### ✅ Projenin Güçlü Yönleri:
1. **Hibrit ML yaklaşımı** (Supervised + RL) - en güncel ve etkili
2. **Multi-modal veri** (teknik, on-chain, türev, psikoloji)
3. **Gerçekçi backtest** (slippage, komisyon, market impact)
4. **Sürekli öğrenme** (PDF RAG + RL fine-tuning)
5. **Professional UI** (React + real-time)

### ⚠️ Riskler ve Zorluklar:
1. **Kompleksite** - çok katmanlı sistem, debug zor olabilir
2. **Veri kalitesi** - farklı kaynaklardan gelen data tutarsızlıkları
3. **Overfitting** - özellikle RL'de, gerçek piyasada performans düşebilir
4. **Latency** - real-time karar vermede gecikme kritik

### 🚀 İyileştirme Önerileri:
1. **A/B Testing** - farklı RL stratejilerini paralel test et
2. **Ensemble of Ensembles** - birden fazla RL agent'ı bir araya getir
3. **Adversarial Training** - kriz senaryolarına karşı robust yap
4. **Human-in-the-loop** - kritik kararlarda insan onayı

### 📊 Başarı Metrikleri (6 Ay Sonrası Hedef):
- Sharpe Ratio: > 2.0
- Win Rate: > 55%
- Max Drawdown: < 15%
- Backtest-to-Live Performance Gap: < 10%

---

## 📚 Ek Kaynaklar

1. **RL for Trading Papers:**
   - "Deep Reinforcement Learning for Trading" (2019)
   - "Decision Transformer: Reinforcement Learning via Sequence Modeling" (2021)
   - "Generative Adversarial Imitation Learning" (2016)

2. **Crypto-specific:**
   - "Machine Learning for Cryptocurrency Trading" (2020)
   - "On-Chain Metrics for Bitcoin Price Prediction" (2021)

3. **Implementation Guides:**
   - Stable-Baselines3 documentation
   - RLlib documentation
   - FinRL library

---

**SON NOT:**
Bu mimari, akademik düzeyde bir sistem için sağlam bir temel oluşturuyor. Production'a geçmeden önce mutlaka:
1. Extensive backtesting (en az 3 yıl)
2. Paper trading (en az 3 ay)
3. Small capital live testing (en az 1 ay)
yapılmalı.

**Risk Uyarısı:** Kripto piyasaları son derece volatil. Hiçbir AI sistemi %100 doğru tahmin yapamaz. Her zaman stop-loss kullanın ve kaybedebileceğinizden fazlasını riske atmayın.
