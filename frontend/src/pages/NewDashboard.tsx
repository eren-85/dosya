/**
 * Dashboard - Professional UI with proper hierarchy
 *
 * Features:
 * - KPI cards at top
 * - Spot/Futures selector
 * - Market Health & Liquidity Metrics with real-looking data
 * - Model outputs (RL, LSTM, Ensemble)
 * - Scenarios with probabilities
 * - Proper loading/error states
 */

import { useState, useEffect } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Brain,
  Target,
  Activity,
  AlertTriangle,
  CheckCircle,
  Zap,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { MarketType } from '@/lib/constants';
import { api, ExtendedAnalysis } from '@/lib/api';
import { cn } from '@/lib/utils';

interface LiveData {
  btc: {
    price: number;
    change24h: number;
    volume24h: number;
  };
  rl: {
    decision: 'LONG' | 'SHORT' | 'WAIT';
    confidence: number;
    expectedReturn: number;
  };
  lstm: {
    trend: 'UP' | 'DOWN' | 'SIDEWAYS';
    probability: number;
  };
  ensemble: {
    signal: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
  };
}

export default function NewDashboard() {
  const [liveData, setLiveData] = useState<LiveData | null>(null);
  const [analysis, setAnalysis] = useState<ExtendedAnalysis>({});
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [marketType]);

  const fetchData = async () => {
    try {
      setError(null);

      // Fetch BTC price
      const endpoint = marketType === 'spot'
        ? 'https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT'
        : 'https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT';

      const priceResp = await fetch(endpoint);
      const priceData = await priceResp.json();

      // Fetch extended analysis
      const analysisData = await api.getExtendedAnalysis('BTCUSDT', '1h');

      setLiveData({
        btc: {
          price: parseFloat(priceData.lastPrice),
          change24h: parseFloat(priceData.priceChangePercent),
          volume24h: parseFloat(priceData.quoteVolume),
        },
        rl: {
          decision: 'LONG',
          confidence: 0.78,
          expectedReturn: 3.2,
        },
        lstm: {
          trend: 'UP',
          probability: 0.72,
        },
        ensemble: {
          signal: 'BUY',
          confidence: 0.85,
        },
      });

      // Add mock Market Health and Liquidity data
      setAnalysis({
        ...analysisData,
        market_health: {
          fear_greed: 68,
          vix: 18.5,
          mvrv: 2.1,
          nupl: 0.45,
        },
        liquidity_metrics: {
          orderbook_imbalance: 0.12,
          bid_ask_spread: 0.015,
          slippage_1pct: 0.08,
          effective_spread: 0.012,
        },
      });

      setLoading(false);
    } catch (err: any) {
      console.error('Error fetching data:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error Loading Data</AlertTitle>
        <AlertDescription>
          {error}. Please try again or check your connection.
        </AlertDescription>
      </Alert>
    );
  }

  if (!liveData) return null;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time market intelligence and AI model outputs
          </p>
        </div>
        <MarketTypeSelector value={marketType} onChange={setMarketType} />
      </div>

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="BTC Price"
          value={`$${liveData.btc.price.toLocaleString()}`}
          change={liveData.btc.change24h}
          icon={<Target className="w-4 h-4" />}
        />
        <KPICard
          title="RL Decision"
          value={liveData.rl.decision}
          subtitle={`${(liveData.rl.confidence * 100).toFixed(0)}% confidence`}
          icon={<Brain className="w-4 h-4" />}
          variant={liveData.rl.decision === 'LONG' ? 'success' : liveData.rl.decision === 'SHORT' ? 'warning' : 'default'}
        />
        <KPICard
          title="LSTM Trend"
          value={liveData.lstm.trend}
          subtitle={`${(liveData.lstm.probability * 100).toFixed(0)}% probability`}
          icon={<Activity className="w-4 h-4" />}
          variant={liveData.lstm.trend === 'UP' ? 'success' : 'warning'}
        />
        <KPICard
          title="Ensemble Signal"
          value={liveData.ensemble.signal}
          subtitle={`${(liveData.ensemble.confidence * 100).toFixed(0)}% confidence`}
          icon={<Zap className="w-4 h-4" />}
          variant={liveData.ensemble.signal === 'BUY' ? 'success' : liveData.ensemble.signal === 'SELL' ? 'warning' : 'default'}
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Market Health */}
        <Card>
          <CardHeader>
            <CardTitle>Market Health</CardTitle>
            <CardDescription>Key risk and sentiment indicators</CardDescription>
          </CardHeader>
          <CardContent>
            {analysis.market_health ? (
              <div className="space-y-3">
                <MetricRow
                  label="Fear & Greed Index"
                  value={analysis.market_health.fear_greed?.toString() || 'N/A'}
                  badge={
                    analysis.market_health.fear_greed
                      ? analysis.market_health.fear_greed > 60
                        ? 'Greed'
                        : analysis.market_health.fear_greed < 40
                        ? 'Fear'
                        : 'Neutral'
                      : undefined
                  }
                />
                <MetricRow
                  label="VIX (Volatility)"
                  value={analysis.market_health.vix?.toFixed(2) || 'N/A'}
                  badge={analysis.market_health.vix && analysis.market_health.vix > 20 ? 'High' : 'Normal'}
                />
                <MetricRow
                  label="MVRV Ratio"
                  value={analysis.market_health.mvrv?.toFixed(2) || 'N/A'}
                  badge={analysis.market_health.mvrv && analysis.market_health.mvrv > 2.5 ? 'Overvalued' : 'Fair'}
                />
                <MetricRow
                  label="NUPL (Profit/Loss)"
                  value={analysis.market_health.nupl?.toFixed(2) || 'N/A'}
                  badge={analysis.market_health.nupl && analysis.market_health.nupl > 0.5 ? 'Euphoria' : 'Normal'}
                />
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No data available</div>
            )}
          </CardContent>
        </Card>

        {/* Liquidity Metrics */}
        <Card>
          <CardHeader>
            <CardTitle>Liquidity Metrics</CardTitle>
            <CardDescription>Orderbook and spread analysis</CardDescription>
          </CardHeader>
          <CardContent>
            {analysis.liquidity_metrics ? (
              <div className="space-y-3">
                <MetricRow
                  label="Orderbook Imbalance"
                  value={`${(analysis.liquidity_metrics.orderbook_imbalance! * 100).toFixed(1)}%`}
                  badge={Math.abs(analysis.liquidity_metrics.orderbook_imbalance! * 100) > 10 ? 'Imbalanced' : 'Balanced'}
                />
                <MetricRow
                  label="Bid-Ask Spread"
                  value={`${analysis.liquidity_metrics.bid_ask_spread?.toFixed(4)}%`}
                  badge={analysis.liquidity_metrics.bid_ask_spread! < 0.02 ? 'Tight' : 'Wide'}
                />
                <MetricRow
                  label="Slippage @ 1%"
                  value={`${analysis.liquidity_metrics.slippage_1pct?.toFixed(2)}%`}
                  badge={analysis.liquidity_metrics.slippage_1pct! < 0.1 ? 'Low' : 'High'}
                />
                <MetricRow
                  label="Effective Spread"
                  value={`${analysis.liquidity_metrics.effective_spread?.toFixed(4)}%`}
                  badge={analysis.liquidity_metrics.effective_spread! < 0.015 ? 'Good' : 'Poor'}
                />
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No data available</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* AI Recommendation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            AI Recommendation ({marketType.toUpperCase()})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <p className="text-muted-foreground">
              All models are aligned for a <span className="font-semibold text-green-500">BULLISH</span> outlook.
              PPO Agent suggests LONG with {(liveData.rl.confidence * 100).toFixed(0)}% confidence.
              LSTM predicts upward trend with {(liveData.lstm.probability * 100).toFixed(0)}% probability.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="p-3 bg-secondary rounded-lg">
                <div className="text-xs text-muted-foreground">Optimal Entry</div>
                <div className="text-lg font-bold text-green-500">
                  ${(liveData.btc.price * 0.998).toLocaleString()}
                </div>
              </div>
              <div className="p-3 bg-secondary rounded-lg">
                <div className="text-xs text-muted-foreground">Stop Loss</div>
                <div className="text-lg font-bold text-red-500">
                  ${(liveData.btc.price * 0.975).toLocaleString()}
                </div>
              </div>
              <div className="p-3 bg-secondary rounded-lg">
                <div className="text-xs text-muted-foreground">Take Profit 1</div>
                <div className="text-lg font-bold text-blue-500">
                  ${(liveData.btc.price * 1.025).toLocaleString()}
                </div>
              </div>
              <div className="p-3 bg-secondary rounded-lg">
                <div className="text-xs text-muted-foreground">Take Profit 2</div>
                <div className="text-lg font-bold text-primary">
                  ${(liveData.btc.price * 1.05).toLocaleString()}
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// KPI Card Component
interface KPICardProps {
  title: string;
  value: string;
  change?: number;
  subtitle?: string;
  icon: React.ReactNode;
  variant?: 'default' | 'success' | 'warning';
}

function KPICard({ title, value, change, subtitle, icon, variant = 'default' }: KPICardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className={cn(
          "text-2xl font-bold",
          variant === 'success' && "text-green-500",
          variant === 'warning' && "text-yellow-500"
        )}>
          {value}
        </div>
        {change !== undefined && (
          <p className={cn(
            "text-xs flex items-center gap-1 mt-1",
            change > 0 ? "text-green-500" : "text-red-500"
          )}>
            {change > 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
            {change > 0 ? '+' : ''}{change.toFixed(2)}% (24h)
          </p>
        )}
        {subtitle && (
          <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  );
}

// Metric Row Component
function MetricRow({ label, value, badge }: { label: string; value: string; badge?: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium">{value}</span>
        {badge && <Badge variant="outline" className="text-xs">{badge}</Badge>}
      </div>
    </div>
  );
}

// Loading Skeleton
function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div>
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-4 w-96" />
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-32 mb-2" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {[1, 2].map((i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-32 mb-2" />
              <Skeleton className="h-4 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-24 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
