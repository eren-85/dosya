import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Brain, Target, AlertCircle, ChevronRight, DollarSign, Zap, BarChart3, PieChart, Cpu, Database } from 'lucide-react';

const SigmaAnalystDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [liveData, setLiveData] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Simulated real-time data
  useEffect(() => {
    // Simulate API call
    const fetchData = () => {
      setLiveData({
        btc: {
          price: 43250.50,
          change24h: 2.45,
          volume24h: 24500000000,
          sentiment: 'bullish'
        },
        rl: {
          decision: 'LONG',
          confidence: 0.78,
          expectedReturn: 3.2,
          riskLevel: 'MEDIUM'
        },
        lstm: {
          trend: 'UP',
          probability: 0.72,
          timeframe: '24H'
        },
        regime: {
          type: 'BULL MARKET',
          confidence: 0.85,
          indicators: {
            trend: 0.9,
            volatility: 0.6,
            momentum: 0.8,
            volume: 0.7
          }
        },
        patterns: {
          orderBlocks: 3,
          fvg: 2,
          liquiditySweeps: 1,
          bos: 1
        },
        backtest: {
          totalTrades: 247,
          winRate: 68.5,
          profitFactor: 2.34,
          sharpe: 1.82,
          maxDrawdown: -12.3,
          totalReturn: 156.7
        }
      });
      setLoading(false);
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5s
    
    return () => clearInterval(interval);
  }, []);
  
  // Sample chart data
  const priceData = Array.from({ length: 24 }, (_, i) => ({
    time: `${i}:00`,
    price: 42000 + Math.random() * 2000,
    volume: Math.random() * 100000000
  }));
  
  const equityCurveData = Array.from({ length: 100 }, (_, i) => ({
    day: i + 1,
    equity: 10000 * (1 + (Math.random() * 0.5 + 0.1) * (i / 100)),
    benchmark: 10000 * (1 + 0.3 * (i / 100))
  }));
  
  const performanceData = [
    { metric: 'Accuracy', value: 73 },
    { metric: 'Precision', value: 78 },
    { metric: 'Recall', value: 71 },
    { metric: 'F1 Score', value: 74 }
  ];
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500"></div>
          <p className="mt-4 text-white text-lg">Loading Sigma Analyst...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-6">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-600">
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
            
            <div className="bg-slate-800/50 backdrop-blur-sm px-4 py-2 rounded-lg border border-purple-500/30">
              <div className="text-xs text-slate-400">Next Update</div>
              <div className="text-sm font-semibold mt-1">00:04:32</div>
            </div>
          </div>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex gap-2 mt-6 overflow-x-auto">
          {['overview', 'analysis', 'backtest', 'models'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                activeTab === tab
                  ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
                  : 'bg-slate-800/30 text-slate-400 hover:bg-slate-800/50'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </header>
      
      {/* Main Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Market Overview */}
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
          
          {/* Price Chart */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold">BTC/USDT Price Action</h2>
              <div className="flex gap-2">
                {['1H', '4H', '1D'].map(tf => (
                  <button key={tf} className="px-3 py-1 bg-slate-700/50 hover:bg-purple-500/30 rounded text-sm transition-colors">
                    {tf}
                  </button>
                ))}
              </div>
            </div>
            
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={priceData}>
                <defs>
                  <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" domain={['dataMin - 500', 'dataMax + 500']} />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1e293b', 
                    border: '1px solid #8b5cf6',
                    borderRadius: '8px'
                  }} 
                />
                <Area type="monotone" dataKey="price" stroke="#8b5cf6" fillOpacity={1} fill="url(#priceGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          
          {/* ML Models Status */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ModelCard
              title="PPO Agent"
              status="ACTIVE"
              accuracy={liveData.rl.confidence * 100}
              icon={<Cpu className="w-8 h-8" />}
              color="purple"
            />
            
            <ModelCard
              title="LSTM Predictor"
              status="ACTIVE"
              accuracy={liveData.lstm.probability * 100}
              icon={<Brain className="w-8 h-8" />}
              color="pink"
            />
            
            <ModelCard
              title="XGBoost Classifier"
              status="ACTIVE"
              accuracy={liveData.regime.confidence * 100}
              icon={<BarChart3 className="w-8 h-8" />}
              color="blue"
            />
          </div>
          
          {/* Detected Patterns */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
              <AlertCircle className="w-6 h-6 text-yellow-500" />
              Detected Patterns
            </h2>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <PatternBadge label="Order Blocks" count={liveData.patterns.orderBlocks} />
              <PatternBadge label="Fair Value Gaps" count={liveData.patterns.fvg} />
              <PatternBadge label="Liquidity Sweeps" count={liveData.patterns.liquiditySweeps} />
              <PatternBadge label="Break of Structure" count={liveData.patterns.bos} />
            </div>
          </div>
        </div>
      )}
      
      {activeTab === 'analysis' && (
        <div className="space-y-6">
          {/* Market Regime Radar */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Market Regime Analysis</h2>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={Object.entries(liveData.regime.indicators).map(([key, value]) => ({
                    metric: key.charAt(0).toUpperCase() + key.slice(1),
                    value: value * 100
                  }))}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis dataKey="metric" stroke="#9ca3af" />
                    <PolarRadiusAxis stroke="#9ca3af" />
                    <Radar name="Current" dataKey="value" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.6} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
              
              <div className="space-y-4">
                <AnalysisItem
                  label="Regime Type"
                  value={liveData.regime.type}
                  confidence={liveData.regime.confidence * 100}
                />
                <AnalysisItem
                  label="LSTM Trend"
                  value={liveData.lstm.trend}
                  confidence={liveData.lstm.probability * 100}
                />
                <AnalysisItem
                  label="RL Decision"
                  value={liveData.rl.decision}
                  confidence={liveData.rl.confidence * 100}
                />
                
                <div className="mt-6 p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <h3 className="font-semibold mb-2 flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-500" />
                    Recommendation
                  </h3>
                  <p className="text-sm text-slate-300">
                    Tüm modeller yükseliş yönünde uyumlu. Optimal entry: $42,800-43,000 aralığı. 
                    Stop loss: $42,200. Take profit targets: $44,500 / $46,000.
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Volume Analysis */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Volume Profile</h2>
            
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={priceData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #8b5cf6' }} />
                <Bar dataKey="volume" fill="#8b5cf6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {activeTab === 'backtest' && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <BacktestMetric label="Total Trades" value={liveData.backtest.totalTrades} />
            <BacktestMetric label="Win Rate" value={`${liveData.backtest.winRate}%`} trend="up" />
            <BacktestMetric label="Profit Factor" value={liveData.backtest.profitFactor} trend="up" />
            <BacktestMetric label="Sharpe Ratio" value={liveData.backtest.sharpe} trend="up" />
            <BacktestMetric label="Max DD" value={`${liveData.backtest.maxDrawdown}%`} trend="down" />
            <BacktestMetric label="Total Return" value={`${liveData.backtest.totalReturn}%`} trend="up" />
          </div>
          
          {/* Equity Curve */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Equity Curve</h2>
            
            <ResponsiveContainer width="100%" height={350}>
              <LineChart data={equityCurveData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="day" stroke="#9ca3af" label={{ value: 'Days', position: 'insideBottom', offset: -5 }} />
                <YAxis stroke="#9ca3af" label={{ value: 'Equity ($)', angle: -90, position: 'insideLeft' }} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #8b5cf6' }} />
                <Legend />
                <Line type="monotone" dataKey="equity" stroke="#8b5cf6" strokeWidth={3} name="Strategy" />
                <Line type="monotone" dataKey="benchmark" stroke="#6b7280" strokeWidth={2} strokeDasharray="5 5" name="Buy & Hold" />
              </LineChart>
            </ResponsiveContainer>
          </div>
          
          {/* Performance Breakdown */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h2 className="text-2xl font-bold mb-6">Model Performance Breakdown</h2>
            
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={performanceData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis type="number" stroke="#9ca3af" domain={[0, 100]} />
                <YAxis type="category" dataKey="metric" stroke="#9ca3af" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #8b5cf6' }} />
                <Bar dataKey="value" fill="#8b5cf6" radius={[0, 8, 8, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      
      {activeTab === 'models' && (
        <div className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* PPO Details */}
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Cpu className="w-6 h-6 text-purple-500" />
                PPO Agent
              </h3>
              
              <div className="space-y-3">
                <InfoRow label="State Dimension" value="150" />
                <InfoRow label="Action Space" value="3 (Long/Neutral/Short)" />
                <InfoRow label="Learning Rate" value="0.0003" />
                <InfoRow label="Epsilon Clip" value="0.2" />
                <InfoRow label="Total Episodes" value="5,247" />
                <InfoRow label="Avg Reward" value="+2.34" />
              </div>
            </div>
            
            {/* LSTM Details */}
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <Brain className="w-6 h-6 text-pink-500" />
                LSTM Predictor
              </h3>
              
              <div className="space-y-3">
                <InfoRow label="Input Sequence" value="50 timesteps" />
                <InfoRow label="Hidden Units" value="128" />
                <InfoRow label="Layers" value="2" />
                <InfoRow label="Dropout" value="0.2" />
                <InfoRow label="Training Accuracy" value="74.3%" />
                <InfoRow label="Validation Accuracy" value="71.8%" />
              </div>
            </div>
            
            {/* XGBoost Details */}
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <BarChart3 className="w-6 h-6 text-blue-500" />
                XGBoost Classifier
              </h3>
              
              <div className="space-y-3">
                <InfoRow label="Estimators" value="100" />
                <InfoRow label="Max Depth" value="5" />
                <InfoRow label="Learning Rate" value="0.1" />
                <InfoRow label="Features" value="5" />
                <InfoRow label="Training Accuracy" value="82.1%" />
                <InfoRow label="F1 Score" value="0.79" />
              </div>
            </div>
            
            {/* Pattern Recognizer */}
            <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
              <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
                <PieChart className="w-6 h-6 text-green-500" />
                Pattern Recognizer
              </h3>
              
              <div className="space-y-3">
                <InfoRow label="Algorithm" value="Rule-based + ML" />
                <InfoRow label="Patterns Tracked" value="4 types" />
                <InfoRow label="Detection Rate" value="95.2%" />
                <InfoRow label="False Positives" value="4.8%" />
                <InfoRow label="Last 24h Detected" value="12" />
                <InfoRow label="Hit Rate" value="78%" />
              </div>
            </div>
          </div>
          
          {/* Data Sources */}
          <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30">
            <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
              <Database className="w-6 h-6 text-purple-500" />
              Data Sources
            </h3>
            
            <div className="grid md:grid-cols-3 gap-4">
              <DataSourceCard name="Binance" status="CONNECTED" latency="45ms" />
              <DataSourceCard name="OKX" status="CONNECTED" latency="52ms" />
              <DataSourceCard name="Bybit" status="CONNECTED" latency="48ms" />
              <DataSourceCard name="Bitget" status="CONNECTED" latency="61ms" />
              <DataSourceCard name="MEXC" status="CONNECTED" latency="73ms" />
              <DataSourceCard name="Glassnode" status="LIMITED" latency="120ms" />
            </div>
          </div>
        </div>
      )}
      
      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-slate-700 text-center text-sm text-slate-400">
        <p>Sigma Analyst v3.0 | Advanced Crypto Intelligence System</p>
        <p className="mt-1">⚠️ Bu bir yatırım tavsiyesi değildir. Kendi araştırmanızı yapın.</p>
      </footer>
    </div>
  );
};

// Component Helpers
const MetricCard = ({ icon, title, value, subtitle, change, trend }) => (
  <div className="bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-purple-500/30 hover:border-purple-500/60 transition-all">
    <div className="flex items-center justify-between mb-3">
      <div className="text-slate-400">{icon}</div>
      {change !== undefined && (
        <div className={`flex items-center gap-1 text-sm font-semibold ${
          change > 0 ? 'text-green-500' : 'text-red-500'
        }`}>
          {change > 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
          {Math.abs(change)}%
        </div>
      )}
    </div>
    
    <div className="text-sm text-slate-400 mb-1">{title}</div>
    <div className="text-2xl font-bold">{value}</div>
    {subtitle && <div className="text-xs text-slate-500 mt-1">{subtitle}</div>}
  </div>
);

const ModelCard = ({ title, status, accuracy, icon, color }) => (
  <div className={`bg-slate-800/30 backdrop-blur-sm rounded-xl p-6 border border-${color}-500/30`}>
    <div className="flex items-center justify-between mb-4">
      <div className={`text-${color}-500`}>{icon}</div>
      <div className="px-3 py-1 bg-green-500/20 text-green-500 text-xs font-semibold rounded-full">
        {status}
      </div>
    </div>
    
    <h3 className="text-lg font-bold mb-2">{title}</h3>
    <div className="flex items-end gap-2">
      <span className="text-3xl font-bold">{accuracy.toFixed(1)}</span>
      <span className="text-slate-400 mb-1">% accuracy</span>
    </div>
    
    <div className="mt-4 bg-slate-700 rounded-full h-2">
      <div 
        className={`bg-gradient-to-r from-${color}-500 to-${color}-600 h-2 rounded-full transition-all`}
        style={{ width: `${accuracy}%` }}
      ></div>
    </div>
  </div>
);

const PatternBadge = ({ label, count }) => (
  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
    <div className="text-3xl font-bold text-purple-400">{count}</div>
    <div className="text-xs text-slate-400 mt-1">{label}</div>
  </div>
);

const AnalysisItem = ({ label, value, confidence }) => (
  <div className="bg-slate-700/30 rounded-lg p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-slate-400">{label}</span>
      <span className="text-xs text-slate-500">{confidence.toFixed(0)}%</span>
    </div>
    <div className="text-xl font-bold">{value}</div>
  </div>
);

const BacktestMetric = ({ label, value, trend }) => (
  <div className="bg-slate-800/30 backdrop-blur-sm rounded-lg p-4 border border-slate-700">
    <div className="text-xs text-slate-400 mb-1">{label}</div>
    <div className="flex items-center gap-2">
      <span className="text-xl font-bold">{value}</span>
      {trend === 'up' && <TrendingUp className="w-4 h-4 text-green-500" />}
      {trend === 'down' && <TrendingDown className="w-4 h-4 text-red-500" />}
    </div>
  </div>
);

const InfoRow = ({ label, value }) => (
  <div className="flex items-center justify-between py-2 border-b border-slate-700/50">
    <span className="text-sm text-slate-400">{label}</span>
    <span className="text-sm font-semibold">{value}</span>
  </div>
);

const DataSourceCard = ({ name, status, latency }) => (
  <div className="bg-slate-700/30 rounded-lg p-4">
    <div className="flex items-center justify-between mb-2">
      <span className="font-semibold">{name}</span>
      <div className={`w-2 h-2 rounded-full ${
        status === 'CONNECTED' ? 'bg-green-500' : 'bg-yellow-500'
      }`}></div>
    </div>
    <div className="text-xs text-slate-400">Latency: {latency}</div>
  </div>
);

export default SigmaAnalystDashboard;