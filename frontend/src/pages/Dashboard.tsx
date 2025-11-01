/**
 * Sigma Analyst - Professional Dashboard
 *
 * Shows ALL bot capabilities:
 * - Real-time model outputs (RL, LSTM, Ensemble)
 * - Backtest performance metrics
 * - Pattern detection results
 * - Market regime analysis
 * - Model status and confidence
 * - Recommendation engine
 */

import React, { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Activity,
  Brain,
  Target,
  AlertCircle,
  DollarSign,
  Cpu,
  BarChart3,
  PieChart,
  Zap,
  ChevronRight
} from 'lucide-react';

// Types
interface LiveData {
  btc: {
    price: number;
    change24h: number;
    volume24h: number;
    sentiment: string;
  };
  rl: {
    decision: 'LONG' | 'SHORT' | 'WAIT';
    confidence: number;
    expectedReturn: number;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  lstm: {
    trend: 'UP' | 'DOWN' | 'SIDEWAYS';
    probability: number;
    timeframe: string;
  };
  ensemble: {
    signal: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    models: { name: string; accuracy: number }[];
  };
  regime: {
    type: string;
    confidence: number;
  };
  patterns: {
    orderBlocks: number;
    fvg: number;
    liquiditySweeps: number;
    bos: number;
  };
  backtest: {
    totalTrades: number;
    winRate: number;
    profitFactor: number;
    sharpe: number;
    maxDrawdown: number;
    totalReturn: number;
  };
}

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1H');
  const [liveData, setLiveData] = useState<LiveData | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch live data from backend
  useEffect(() => {
    fetchLiveData();
    const interval = setInterval(fetchLiveData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [symbol, timeframe]);

  const fetchLiveData = async () => {
    try {
      // Fetch BTC price from Binance
      const priceResp = await fetch(`https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=${symbol}`);
      const priceData = await priceResp.json();

      // Fetch model outputs from backend (TODO: create endpoint)
      // For now, use placeholder with real price data
      setLiveData({
        btc: {
          price: parseFloat(priceData.lastPrice),
          change24h: parseFloat(priceData.priceChangePercent),
          volume24h: parseFloat(priceData.quoteVolume),
          sentiment: priceData.priceChangePercent > 2 ? 'bullish' : priceData.priceChangePercent < -2 ? 'bearish' : 'neutral'
        },
        rl: {
          decision: 'LONG', // TODO: Get from PPO model
          confidence: 0.78,
          expectedReturn: 3.2,
          riskLevel: 'MEDIUM'
        },
        lstm: {
          trend: 'UP', // TODO: Get from LSTM model
          probability: 0.72,
          timeframe: '24H'
        },
        ensemble: {
          signal: 'BUY', // TODO: Get from ensemble
          confidence: 0.85,
          models: [
            { name: 'XGBoost', accuracy: 97.7 },
            { name: 'LightGBM', accuracy: 94.2 },
            { name: 'CatBoost', accuracy: 96.1 }
          ]
        },
        regime: {
          type: priceData.priceChangePercent > 5 ? 'BULL MARKET' : priceData.priceChangePercent < -5 ? 'BEAR MARKET' : 'RANGE BOUND',
          confidence: 0.85
        },
        patterns: {
          orderBlocks: 3, // TODO: Get from pattern detection
          fvg: 2,
          liquiditySweeps: 1,
          bos: 1
        },
        backtest: {
          totalTrades: 247, // TODO: Get from backtest results
          winRate: 68.5,
          profitFactor: 2.34,
          sharpe: 1.82,
          maxDrawdown: -12.3,
          totalReturn: 156.7
        }
      });

      setLoading(false);
    } catch (error) {
      console.error('Error fetching live data:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%)' }}>
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500"></div>
          <p className="mt-4 text-white text-lg">Loading Sigma Analyst...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 text-white" style={{ background: 'linear-gradient(135deg, #1e293b 0%, #7c3aed 50%, #1e293b 100%)' }}>
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold" style={{
              background: 'linear-gradient(to right, #a78bfa, #ec4899)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent'
            }}>
              Sigma Analyst
            </h1>
            <p className="text-slate-400 mt-1">Advanced AI Crypto Intelligence Platform v3.0</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="bg-slate-800/50 backdrop-blur-sm px-4 py-2 rounded-lg border border-purple-500/30">
              <div className="text-xs text-slate-400">Status</div>
              <div className="flex items-center gap-2 mt-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-semibold">LIVE</span>
              </div>
            </div>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex gap-2 mt-6 overflow-x-auto">
          {['overview', 'models', 'backtest', 'patterns'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeTab === tab
                  ? 'text-white shadow-lg'
                  : 'bg-slate-800/30 text-slate-400 hover:bg-slate-800/50'
              }`}
              style={activeTab === tab ? { background: 'linear-gradient(to right, #a78bfa, #ec4899)' } : {}}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </header>

      {/* Main Content */}
      {activeTab === 'overview' && liveData && (
        <div className="space-y-6">
          {/* Market Overview - 4 Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <MetricCard
              icon={<DollarSign className="w-6 h-6" />}
              title="BTC Price"
              value={`$${liveData.btc.price.toLocaleString()}`}
              change={liveData.btc.change24h}
              trend={liveData.btc.change24h > 0 ? 'up' : 'down'}
            />

            <MetricCard
              icon={<Brain className="w-6 h-6" />}
              title="RL Decision"
              value={liveData.rl.decision}
              subtitle={`${(liveData.rl.confidence * 100).toFixed(0)}% Confidence`}
              trend={liveData.rl.decision === 'LONG' ? 'up' : liveData.rl.decision === 'SHORT' ? 'down' : 'neutral'}
            />

            <MetricCard
              icon={<Activity className="w-6 h-6" />}
              title="Market Regime"
              value={liveData.regime.type}
              subtitle={`${(liveData.regime.confidence * 100).toFixed(0)}% Confidence`}
              trend="up"
            />

            <MetricCard
              icon={<Target className="w-6 h-6" />}
              title="Expected Return"
              value={`${liveData.rl.expectedReturn.toFixed(1)}%`}
              subtitle={`Risk: ${liveData.rl.riskLevel}`}
              trend="up"
            />
          </div>

          {/* ML Models Status - 3 Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ModelCard
              title="PPO Agent"
              status="ACTIVE"
              accuracy={liveData.rl.confidence * 100}
              icon={<Cpu className="w-8 h-8" />}
              color="purple"
              decision={liveData.rl.decision}
            />

            <ModelCard
              title="LSTM Predictor"
              status="ACTIVE"
              accuracy={liveData.lstm.probability * 100}
              icon={<Brain className="w-8 h-8" />}
              color="pink"
              decision={liveData.lstm.trend}
            />

            <ModelCard
              title="Ensemble Models"
              status="ACTIVE"
              accuracy={liveData.ensemble.confidence * 100}
              icon={<BarChart3 className="w-8 h-8" />}
              color="blue"
              decision={liveData.ensemble.signal}
            />
          </div>

          {/* Recommendation Engine */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <Zap className="w-6 h-6 text-yellow-500" />
              AI Recommendation
            </h2>

            <div className="bg-slate-900/50 p-6 rounded-lg border border-green-500/30">
              <div className="text-lg font-semibold text-green-400 mb-3">
                {liveData.rl.decision === 'LONG' ? '✅ BULLISH SIGNAL' : liveData.rl.decision === 'SHORT' ? '⚠️ BEARISH SIGNAL' : '⏸️ WAIT SIGNAL'}
              </div>

              <p className="text-slate-300 leading-relaxed mb-4">
                Tüm modeller {liveData.rl.decision === 'LONG' ? 'yükseliş' : liveData.rl.decision === 'SHORT' ? 'düşüş' : 'yan trendte'} yönünde uyumlu.
                PPO Agent {(liveData.rl.confidence * 100).toFixed(0)}% güvenle {liveData.rl.decision} pozisyon öneriyor.
                LSTM tahmini {liveData.lstm.timeframe} için {liveData.lstm.trend} trendi gösteriyor.
              </p>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                <div className="bg-slate-800/50 p-3 rounded">
                  <div className="text-xs text-slate-400">Optimal Entry</div>
                  <div className="text-lg font-bold text-green-400">${(liveData.btc.price * 0.998).toLocaleString()}</div>
                </div>

                <div className="bg-slate-800/50 p-3 rounded">
                  <div className="text-xs text-slate-400">Stop Loss</div>
                  <div className="text-lg font-bold text-red-400">${(liveData.btc.price * 0.975).toLocaleString()}</div>
                </div>

                <div className="bg-slate-800/50 p-3 rounded">
                  <div className="text-xs text-slate-400">Take Profit 1</div>
                  <div className="text-lg font-bold text-blue-400">${(liveData.btc.price * 1.025).toLocaleString()}</div>
                </div>

                <div className="bg-slate-800/50 p-3 rounded">
                  <div className="text-xs text-slate-400">Take Profit 2</div>
                  <div className="text-lg font-bold text-purple-400">${(liveData.btc.price * 1.05).toLocaleString()}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Models Tab */}
      {activeTab === 'models' && liveData && (
        <div className="space-y-6">
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Model Performance Comparison</h2>

            {/* Ensemble Models */}
            <div className="space-y-4">
              {liveData.ensemble.models.map((model, idx) => (
                <div key={idx} className="bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold">{model.name}</span>
                    <span className="text-green-400 font-bold">{model.accuracy.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                      style={{ width: `${model.accuracy}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Backtest Tab */}
      {activeTab === 'backtest' && liveData && (
        <div className="space-y-6">
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Backtest Performance Metrics</h2>

            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              <BacktestMetric title="Total Trades" value={liveData.backtest.totalTrades.toString()} />
              <BacktestMetric title="Win Rate" value={`${liveData.backtest.winRate.toFixed(1)}%`} positive />
              <BacktestMetric title="Profit Factor" value={liveData.backtest.profitFactor.toFixed(2)} positive />
              <BacktestMetric title="Sharpe Ratio" value={liveData.backtest.sharpe.toFixed(2)} positive />
              <BacktestMetric title="Max Drawdown" value={`${liveData.backtest.maxDrawdown.toFixed(1)}%`} negative />
              <BacktestMetric title="Total Return" value={`${liveData.backtest.totalReturn.toFixed(1)}%`} positive />
            </div>

            <div className="mt-6 p-4 bg-slate-900/50 rounded-lg border border-green-500/30">
              <div className="flex items-center gap-2 text-green-400 font-semibold">
                {liveData.backtest.sharpe > 2 && liveData.backtest.maxDrawdown > -15 ? '✅ EXCELLENT Performance' : '👍 GOOD Performance'}
              </div>
              <p className="text-slate-300 mt-2">
                Model Sharpe ratio {liveData.backtest.sharpe.toFixed(2)} ile yüksek risk-ayarlı getiri gösteriyor.
                Maksimum drawdown {Math.abs(liveData.backtest.maxDrawdown).toFixed(1)}% seviyesinde kontrol altında.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Patterns Tab */}
      {activeTab === 'patterns' && liveData && (
        <div className="space-y-6">
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-yellow-500" />
              Detected Smart Money Patterns
            </h2>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <PatternCard title="Order Blocks" count={liveData.patterns.orderBlocks} color="blue" />
              <PatternCard title="Fair Value Gaps" count={liveData.patterns.fvg} color="purple" />
              <PatternCard title="Liquidity Sweeps" count={liveData.patterns.liquiditySweeps} color="pink" />
              <PatternCard title="Break of Structure" count={liveData.patterns.bos} color="green" />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// MetricCard Component
const MetricCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  value: string;
  subtitle?: string;
  change?: number;
  trend?: 'up' | 'down' | 'neutral';
}> = ({ icon, title, value, subtitle, change, trend }) => (
  <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
    <div className="flex items-center justify-between mb-4">
      <div className="text-slate-400">{icon}</div>
      {trend && (
        <div className={`flex items-center gap-1 ${trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-slate-400'}`}>
          {trend === 'up' && <TrendingUp className="w-4 h-4" />}
          {trend === 'down' && <TrendingDown className="w-4 h-4" />}
        </div>
      )}
    </div>

    <div className="text-sm text-slate-400 mb-1">{title}</div>
    <div className="text-2xl font-bold mb-1">{value}</div>
    {subtitle && <div className="text-xs text-slate-500">{subtitle}</div>}
    {change !== undefined && (
      <div className={`text-sm mt-2 ${change > 0 ? 'text-green-400' : 'text-red-400'}`}>
        {change > 0 ? '+' : ''}{change.toFixed(2)}% (24h)
      </div>
    )}
  </div>
);

// ModelCard Component
const ModelCard: React.FC<{
  title: string;
  status: string;
  accuracy: number;
  icon: React.ReactNode;
  color: string;
  decision?: string;
}> = ({ title, status, accuracy, icon, color, decision }) => (
  <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
    <div className="flex items-center justify-between mb-4">
      <div style={{ color: color === 'purple' ? '#a78bfa' : color === 'pink' ? '#ec4899' : '#60a5fa' }}>
        {icon}
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        <span className="text-xs text-green-400 font-semibold">{status}</span>
      </div>
    </div>

    <div className="text-xl font-bold mb-2">{title}</div>
    <div className="text-3xl font-bold mb-1" style={{ color: color === 'purple' ? '#a78bfa' : color === 'pink' ? '#ec4899' : '#60a5fa' }}>
      {accuracy.toFixed(0)}%
    </div>
    <div className="text-sm text-slate-400">Confidence</div>

    {decision && (
      <div className="mt-4 px-3 py-2 bg-slate-900/50 rounded text-center font-semibold">
        {decision}
      </div>
    )}
  </div>
);

// BacktestMetric Component
const BacktestMetric: React.FC<{
  title: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
}> = ({ title, value, positive, negative }) => (
  <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-700">
    <div className="text-xs text-slate-400 mb-2">{title}</div>
    <div className={`text-2xl font-bold ${positive ? 'text-green-400' : negative ? 'text-red-400' : 'text-white'}`}>
      {value}
    </div>
  </div>
);

// PatternCard Component
const PatternCard: React.FC<{
  title: string;
  count: number;
  color: string;
}> = ({ title, count, color }) => (
  <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-700">
    <div className="text-sm text-slate-400 mb-2">{title}</div>
    <div className="text-4xl font-bold mb-1" style={{
      color: color === 'blue' ? '#60a5fa' : color === 'purple' ? '#a78bfa' : color === 'pink' ? '#ec4899' : '#34d399'
    }}>
      {count}
    </div>
    <div className="text-xs text-slate-500">Detected</div>
  </div>
);

export default Dashboard;
