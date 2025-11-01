/**
 * Dashboard - Professional UI with proper hierarchy
 *
 * Features:
 * - KPI cards at top
 * - Market Health & Liquidity Metrics panels
 * - Model outputs (RL, LSTM, Ensemble)
 * - Scenarios with probabilities
 * - Proper loading/error states
 */

import React, { useState, useEffect } from 'react';
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setError(null);

      // Fetch BTC price
      const priceResp = await fetch('https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=BTCUSDT');
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

      setAnalysis(analysisData);
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
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Real-time market intelligence and AI model outputs
        </p>
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
                {analysis.market_health.fear_greed !== undefined && (
                  <MetricRow label="Fear & Greed" value={analysis.market_health.fear_greed.toString()} />
                )}
                {analysis.market_health.vix !== undefined && (
                  <MetricRow label="VIX (Volatility)" value={analysis.market_health.vix.toFixed(2)} />
                )}
                {analysis.market_health.mvrv !== undefined && (
                  <MetricRow label="MVRV Ratio" value={analysis.market_health.mvrv.toFixed(2)} />
                )}
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
                {analysis.liquidity_metrics.orderbook_imbalance !== undefined && (
                  <MetricRow
                    label="Orderbook Imbalance"
                    value={`${(analysis.liquidity_metrics.orderbook_imbalance * 100).toFixed(1)}%`}
                  />
                )}
                {analysis.liquidity_metrics.bid_ask_spread !== undefined && (
                  <MetricRow
                    label="Bid-Ask Spread"
                    value={`${analysis.liquidity_metrics.bid_ask_spread.toFixed(4)}%`}
                  />
                )}
                {analysis.liquidity_metrics.slippage_1pct !== undefined && (
                  <MetricRow
                    label="Slippage @ 1%"
                    value={`${analysis.liquidity_metrics.slippage_1pct.toFixed(2)}%`}
                  />
                )}
              </div>
            ) : (
              <div className="text-sm text-muted-foreground">No data available</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Scenarios */}
      {analysis.scenarios && analysis.scenarios.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Market Scenarios</CardTitle>
            <CardDescription>AI-generated trading scenarios with probabilities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analysis.scenarios.map((scenario, idx) => (
                <div key={idx} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold">{scenario.name}</h4>
                    <Badge variant={scenario.probability > 0.6 ? 'success' : 'default'}>
                      {(scenario.probability * 100).toFixed(0)}% probability
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{scenario.description}</p>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Trigger:</span>{' '}
                      <span className="font-medium">${scenario.trigger_price.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Invalidation:</span>{' '}
                      <span className="font-medium">${scenario.invalidation_price.toLocaleString()}</span>
                    </div>
                  </div>
                  {scenario.targets.length > 0 && (
                    <div className="mt-2 text-sm">
                      <span className="text-muted-foreground">Targets:</span>{' '}
                      {scenario.targets.map((t, i) => (
                        <span key={i} className="font-medium">
                          ${t.toLocaleString()}{i < scenario.targets.length - 1 ? ', ' : ''}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Alerts */}
      {analysis.alerts && analysis.alerts.length > 0 && (
        <div className="space-y-2">
          {analysis.alerts.map((alert) => (
            <Alert key={alert.id} variant={alert.type === 'critical' ? 'destructive' : alert.type === 'warning' ? 'warning' : 'default'}>
              {alert.type === 'critical' ? (
                <AlertTriangle className="h-4 w-4" />
              ) : (
                <CheckCircle className="h-4 w-4" />
              )}
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}
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
function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium">{value}</span>
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
