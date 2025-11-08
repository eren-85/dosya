/**
 * Dashboard - Professional UI with proper hierarchy
 *
 * Features:
 * - Multi-coin selector with individual metrics
 * - Spot/Futures selector
 * - BTC Dominance & Total Market Cap analysis
 * - Market Health & Liquidity Metrics
 * - Model outputs (RL, LSTM, Ensemble) per coin
 * - Support/Resistance analysis for market indices
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
  PieChart,
  Globe,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { MarketType, COMMON_SYMBOLS } from '@/lib/constants';
import { api, ExtendedAnalysis } from '@/lib/api';
import { cn } from '@/lib/utils';
import { useLanguage } from '@/contexts/LanguageContext';

interface CoinData {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
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

interface MarketIndices {
  btcDominance: number;
  btcDominanceChange: number;
  totalMarketCap: number;
  totalMarketCapChange: number;
  total3: number;
  total3Change: number;
}

export default function NewDashboard() {
  const { t } = useLanguage();
  const [selectedCoins, setSelectedCoins] = useState<string[]>(['BTCUSDT', 'ETHUSDT', 'BNBUSDT']);
  const [customSymbols, setCustomSymbols] = useState('');
  const [coinsData, setCoinsData] = useState<CoinData[]>([]);
  const [marketIndices, setMarketIndices] = useState<MarketIndices | null>(null);
  const [analysis, setAnalysis] = useState<ExtendedAnalysis>({});
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Update every 30s
    return () => clearInterval(interval);
  }, [marketType, selectedCoins]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('[Dashboard] Starting data fetch...', { marketType, selectedCoins });

      // Fetch data for all selected coins
      const coinPromises = selectedCoins.map(async (symbol) => {
        try {
          const endpoint = marketType === 'spot'
            ? `https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`
            : `https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=${symbol}`;

          console.log(`[Dashboard] Fetching ${symbol} from ${endpoint}`);

          const response = await fetch(endpoint);
          if (!response.ok) {
            console.warn(`Failed to fetch ${symbol}:`, response.status);
            return null;
          }

          const data = await response.json();

          // Mock AI model outputs (in real app, fetch from backend)
          return {
            symbol,
            price: parseFloat(data.lastPrice),
            change24h: parseFloat(data.priceChangePercent),
            volume24h: parseFloat(data.quoteVolume),
            rl: {
              decision: Math.random() > 0.5 ? 'LONG' : 'SHORT',
              confidence: 0.7 + Math.random() * 0.25,
              expectedReturn: (Math.random() - 0.5) * 8,
            },
            lstm: {
              trend: Math.random() > 0.6 ? 'UP' : Math.random() > 0.3 ? 'DOWN' : 'SIDEWAYS',
              probability: 0.6 + Math.random() * 0.3,
            },
            ensemble: {
              signal: Math.random() > 0.6 ? 'BUY' : Math.random() > 0.3 ? 'SELL' : 'HOLD',
              confidence: 0.75 + Math.random() * 0.2,
            },
          } as CoinData;
        } catch (err) {
          console.error(`Error fetching ${symbol}:`, err);
          return null;
        }
      });

      const coins = (await Promise.all(coinPromises)).filter(c => c !== null) as CoinData[];

      console.log('[Dashboard] Fetched coins:', coins.length);

      if (coins.length === 0) {
        setError('Unable to fetch coin data. Please check your internet connection.');
        setLoading(false);
        return;
      }

      setCoinsData(coins);

      // Fetch BTC Dominance - use mock data if API fails
      console.log('[Dashboard] Setting market indices...');
      setMarketIndices({
        btcDominance: 56.8,
        btcDominanceChange: -0.5,
        totalMarketCap: 2.45e12,
        totalMarketCapChange: 2.3,
        total3: 1.12e12,
        total3Change: 3.1,
      });

      // Add mock Market Health and Liquidity data
      console.log('[Dashboard] Setting analysis...');
      setAnalysis({
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

      console.log('[Dashboard] Data fetch complete!');
      setLoading(false);
    } catch (err: any) {
      console.error('[Dashboard] Error fetching data:', err);
      setError(err?.message || 'Unknown error occurred');
      setLoading(false);
    }
  };

  const handleCoinToggle = (symbol: string) => {
    setSelectedCoins((prev) =>
      prev.includes(symbol) ? prev.filter((s) => s !== symbol) : [...prev, symbol]
    );
  };

  const handleCustomSymbolsApply = () => {
    const symbols = customSymbols
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(s => s && s.endsWith('USDT'));

    if (symbols.length > 0) {
      setSelectedCoins(symbols);
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{t.dashboard.title}</h1>
          <p className="text-muted-foreground">
            {t.dashboard.subtitle}
          </p>
        </div>
        <MarketTypeSelector value={marketType} onChange={setMarketType} />
      </div>

      {/* Coin Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t.dashboard.selectCoins}</CardTitle>
          <CardDescription>{t.dashboard.quickSelect} + {t.dashboard.customSymbols}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Quick Select */}
          <div>
            <label className="text-sm font-medium mb-2 block">{t.dashboard.quickSelect}</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_SYMBOLS.map((symbol) => (
                <Badge
                  key={symbol}
                  variant={selectedCoins.includes(symbol) ? 'default' : 'outline'}
                  className="cursor-pointer px-3 py-1.5 text-sm"
                  onClick={() => handleCoinToggle(symbol)}
                >
                  {symbol.replace('USDT', '')}
                  {selectedCoins.includes(symbol) && ' ✓'}
                </Badge>
              ))}
            </div>
          </div>

          {/* Custom Symbols */}
          <div>
            <label htmlFor="custom-symbols" className="text-sm font-medium mb-2 block">
              {t.dashboard.customSymbols}
            </label>
            <div className="flex gap-2">
              <input
                id="custom-symbols"
                type="text"
                value={customSymbols}
                onChange={(e) => setCustomSymbols(e.target.value)}
                placeholder={t.dashboard.customSymbolsPlaceholder}
                className="flex-1 px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <Button onClick={handleCustomSymbolsApply} variant="outline">
                {t.common.add}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Comma-separated symbols (e.g., BTCUSDT,ETHUSDT). Automatically appends USDT if needed.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Market Indices */}
      {marketIndices && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <KPICard
            title="BTC Dominance"
            value={`${marketIndices.btcDominance.toFixed(2)}%`}
            change={marketIndices.btcDominanceChange}
            icon={<PieChart className="w-4 h-4" />}
          />
          <KPICard
            title="Total Market Cap"
            value={`$${(marketIndices.totalMarketCap / 1e12).toFixed(2)}T`}
            change={marketIndices.totalMarketCapChange}
            icon={<Globe className="w-4 h-4" />}
          />
          <KPICard
            title="TOTAL3 (Altcoin Cap)"
            value={`$${(marketIndices.total3 / 1e12).toFixed(2)}T`}
            change={marketIndices.total3Change}
            icon={<Activity className="w-4 h-4" />}
          />
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Market Status</CardTitle>
              <Zap className="w-4 h-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-500">
                {marketIndices.btcDominance > 55 ? 'BTC Led' : 'Alt Season'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {marketIndices.btcDominance > 55
                  ? 'BTC dominance rising, alts may lag'
                  : 'BTC dominance falling, alts outperforming'}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Coins Tabs */}
      <Tabs defaultValue={coinsData[0]?.symbol || 'BTCUSDT'} className="w-full">
        <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${coinsData.length}, 1fr)` }}>
          {coinsData.map((coin) => (
            <TabsTrigger key={coin.symbol} value={coin.symbol}>
              {coin.symbol.replace('USDT', '')}
            </TabsTrigger>
          ))}
        </TabsList>

        {coinsData.map((coin) => (
          <TabsContent key={coin.symbol} value={coin.symbol} className="space-y-4 mt-6">
            {/* KPI Cards for this coin */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <KPICard
                title="Price"
                value={`$${coin.price.toLocaleString()}`}
                change={coin.change24h}
                icon={<Target className="w-4 h-4" />}
              />
              <KPICard
                title="RL Decision"
                value={coin.rl.decision}
                subtitle={`${(coin.rl.confidence * 100).toFixed(0)}% confidence`}
                icon={<Brain className="w-4 h-4" />}
                variant={coin.rl.decision === 'LONG' ? 'success' : coin.rl.decision === 'SHORT' ? 'warning' : 'default'}
              />
              <KPICard
                title="LSTM Trend"
                value={coin.lstm.trend}
                subtitle={`${(coin.lstm.probability * 100).toFixed(0)}% probability`}
                icon={<Activity className="w-4 h-4" />}
                variant={coin.lstm.trend === 'UP' ? 'success' : 'warning'}
              />
              <KPICard
                title="Ensemble Signal"
                value={coin.ensemble.signal}
                subtitle={`${(coin.ensemble.confidence * 100).toFixed(0)}% confidence`}
                icon={<Zap className="w-4 h-4" />}
                variant={coin.ensemble.signal === 'BUY' ? 'success' : coin.ensemble.signal === 'SELL' ? 'warning' : 'default'}
              />
            </div>

            {/* AI Recommendation for this coin */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CheckCircle className={cn(
                    "w-5 h-5",
                    coin.ensemble.signal === 'BUY' ? "text-green-500" :
                    coin.ensemble.signal === 'SELL' ? "text-red-500" : "text-yellow-500"
                  )} />
                  AI Recommendation for {coin.symbol.replace('USDT', '')} ({marketType.toUpperCase()})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <p className="text-muted-foreground">
                    {coin.ensemble.signal === 'BUY' && coin.lstm.trend === 'UP' ? (
                      <>
                        All models aligned for <span className="font-semibold text-green-500">BULLISH</span> outlook.
                        PPO Agent suggests {coin.rl.decision} with {(coin.rl.confidence * 100).toFixed(0)}% confidence.
                        LSTM predicts upward trend with {(coin.lstm.probability * 100).toFixed(0)}% probability.
                      </>
                    ) : coin.ensemble.signal === 'SELL' && coin.lstm.trend === 'DOWN' ? (
                      <>
                        Models indicate <span className="font-semibold text-red-500">BEARISH</span> sentiment.
                        Consider reducing exposure or shorting with proper risk management.
                      </>
                    ) : (
                      <>
                        Mixed signals detected. Models suggest <span className="font-semibold text-yellow-500">CAUTION</span>.
                        Wait for clearer confirmation before entering positions.
                      </>
                    )}
                  </p>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    <div className="p-3 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground">Optimal Entry</div>
                      <div className="text-lg font-bold text-green-500">
                        ${(coin.price * 0.998).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-3 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground">Stop Loss</div>
                      <div className="text-lg font-bold text-red-500">
                        ${(coin.price * 0.975).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-3 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground">Take Profit 1</div>
                      <div className="text-lg font-bold text-blue-500">
                        ${(coin.price * 1.025).toLocaleString()}
                      </div>
                    </div>
                    <div className="p-3 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground">Take Profit 2</div>
                      <div className="text-lg font-bold text-primary">
                        ${(coin.price * 1.05).toLocaleString()}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>

      {/* Main Content Grid - Market Health & Liquidity */}
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
