/**
 * AI Analysis Page
 * - Market scenarios with probabilities
 * - Market pulse & kill zones
 * - Spot/Futures selector
 * - On-chain & derivatives data
 * - Alert system
 */

import { useState, useEffect } from 'react';
import { Activity, AlertCircle, Clock, Zap, TrendingUp } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { MarketType, COMMON_SYMBOLS } from '@/lib/constants';
import { api, ExtendedAnalysis } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';

// Generate scenarios based on current price
function generateScenarios(currentPrice: number) {
  return [
    {
      name: 'Bull Breakout Scenario',
      probability: 0.72,
      trigger_price: currentPrice * 1.02,
      invalidation_price: currentPrice * 0.97,
      targets: [currentPrice * 1.05, currentPrice * 1.09, currentPrice * 1.12],
      description: 'Price breaks above resistance with strong volume. PPO Agent confidence 78%.',
    },
    {
      name: 'Range Continuation',
      probability: 0.58,
      trigger_price: currentPrice * 1.00,
      invalidation_price: currentPrice * 0.95,
      targets: [currentPrice * 1.015, currentPrice * 1.03],
      description: 'Market remains range-bound. LSTM predicts sideways movement.',
    },
    {
      name: 'Bear Retracement',
      probability: 0.43,
      trigger_price: currentPrice * 0.96,
      invalidation_price: currentPrice * 1.03,
      targets: [currentPrice * 0.93, currentPrice * 0.90, currentPrice * 0.87],
      description: 'Potential correction if support breaks. Lower probability scenario.',
    },
  ];
}

const MOCK_ALERTS = [
  {
    id: '1',
    type: 'warning' as const,
    message: 'RSI approaching overbought zone (72). Consider taking profits.',
    timestamp: Date.now(),
  },
  {
    id: '2',
    type: 'info' as const,
    message: 'MACD bullish crossover detected on 4h timeframe.',
    timestamp: Date.now(),
  },
];

export default function NewAnalysis() {
  const [analysis, setAnalysis] = useState<ExtendedAnalysis>({});
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysis();
  }, [marketType, selectedSymbol]);

  const fetchAnalysis = async () => {
    setLoading(true);
    try {
      // Fetch current price
      const endpoint = marketType === 'spot'
        ? `https://api.binance.com/api/v3/ticker/24hr?symbol=${selectedSymbol}`
        : `https://fapi.binance.com/fapi/v1/ticker/24hr?symbol=${selectedSymbol}`;

      const priceResp = await fetch(endpoint);
      const priceData = await priceResp.json();
      const price = parseFloat(priceData.lastPrice);
      setCurrentPrice(price);

      // Fetch AI analysis
      const data = await api.getExtendedAnalysis(selectedSymbol, '1h');

      // Generate scenarios based on current price
      const scenarios = generateScenarios(price);

      // Add mock data for demo
      setAnalysis({
        ...data,
        scenarios: scenarios,
        alerts: MOCK_ALERTS,
        market_pulse: `${marketType === 'spot' ? 'Spot' : 'Futures'} market for ${selectedSymbol.replace('USDT', '')} showing ${price > 50000 ? 'bullish' : 'neutral'} momentum with institutional interest. Order flow analysis suggests ${price > 50000 ? 'accumulation' : 'consolidation'} phase. Current price: $${price.toLocaleString()}.`,
        asian_killzone: { start: '00:00', end: '09:00', active: false },
        london_killzone: { start: '07:00', end: '16:00', active: true },
        ny_killzone: { start: '13:00', end: '22:00', active: false },
      });

      setLoading(false);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Analysis</h1>
          <p className="text-muted-foreground">
            Advanced market intelligence and AI-generated scenarios
          </p>
        </div>
        <MarketTypeSelector value={marketType} onChange={setMarketType} />
      </div>

      {/* Coin Selector */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Select Coin</CardTitle>
              <CardDescription>Choose which coin to analyze</CardDescription>
            </div>
            {currentPrice && (
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Current Price</div>
                <div className="text-2xl font-bold text-primary">
                  ${currentPrice.toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {COMMON_SYMBOLS.map((symbol) => (
              <Badge
                key={symbol}
                variant={selectedSymbol === symbol ? 'default' : 'outline'}
                className="cursor-pointer px-3 py-1.5 text-sm"
                onClick={() => setSelectedSymbol(symbol)}
              >
                {symbol.replace('USDT', '')}
                {selectedSymbol === symbol && ' ✓'}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="scenarios" className="w-full">
        <TabsList>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="killzones">Kill Zones</TabsTrigger>
          <TabsTrigger value="pulse">Market Pulse</TabsTrigger>
        </TabsList>

        {/* Scenarios Tab */}
        <TabsContent value="scenarios" className="space-y-4 mt-6">
          {analysis.scenarios && analysis.scenarios.length > 0 ? (
            analysis.scenarios.map((scenario, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      {scenario.probability > 0.6 ? (
                        <TrendingUp className="w-5 h-5 text-green-500" />
                      ) : (
                        <Activity className="w-5 h-5 text-muted-foreground" />
                      )}
                      {scenario.name}
                    </CardTitle>
                    <Badge variant={scenario.probability > 0.6 ? 'success' : 'default'}>
                      {(scenario.probability * 100).toFixed(0)}% probability
                    </Badge>
                  </div>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div>
                      <div className="text-sm text-muted-foreground">Trigger Price</div>
                      <div className="text-lg font-semibold text-green-500">
                        ${scenario.trigger_price.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Invalidation</div>
                      <div className="text-lg font-semibold text-red-500">
                        ${scenario.invalidation_price.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Targets</div>
                      <div className="text-sm font-medium">
                        {scenario.targets.map((t, i) => (
                          <span key={i} className="text-primary">
                            ${t.toLocaleString()}{i < scenario.targets.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Alert>
              <Activity className="h-4 w-4" />
              <AlertDescription>
                No scenarios available. Scenarios are generated based on current market conditions and AI model predictions.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Kill Zones Tab */}
        <TabsContent value="killzones" className="space-y-4 mt-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Asian Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.asian_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.asian_killzone.start} - {analysis.asian_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.asian_killzone.active ? 'success' : 'default'}>
                      {analysis.asian_killzone.active ? 'Active Now' : 'Inactive'}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-2">
                      Low volatility, ranging behavior
                    </p>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  London Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.london_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.london_killzone.start} - {analysis.london_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.london_killzone.active ? 'success' : 'default'}>
                      {analysis.london_killzone.active ? 'Active Now' : 'Inactive'}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-2">
                      High volume, trend establishment
                    </p>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  New York Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.ny_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.ny_killzone.start} - {analysis.ny_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.ny_killzone.active ? 'success' : 'default'}>
                      {analysis.ny_killzone.active ? 'Active Now' : 'Inactive'}
                    </Badge>
                    <p className="text-xs text-muted-foreground mt-2">
                      High volatility, reversals common
                    </p>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Market Pulse Tab */}
        <TabsContent value="pulse" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                Market Pulse
              </CardTitle>
              <CardDescription>AI-generated market sentiment analysis for {marketType}</CardDescription>
            </CardHeader>
            <CardContent>
              {analysis.market_pulse ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p className="text-foreground leading-relaxed">{analysis.market_pulse}</p>

                  <div className="grid gap-4 md:grid-cols-2 mt-6 not-prose">
                    <div className="p-4 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground mb-1">Market Regime</div>
                      <div className="text-lg font-semibold">Bullish Trend</div>
                    </div>
                    <div className="p-4 bg-secondary rounded-lg">
                      <div className="text-xs text-muted-foreground mb-1">Volatility</div>
                      <div className="text-lg font-semibold">Moderate (VIX: 18.5)</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Market pulse analysis is not available. This feature provides AI-generated
                  insights based on current market conditions.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alerts */}
      {analysis.alerts && analysis.alerts.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Active Alerts</h2>
          {analysis.alerts.map((alert) => (
            <Alert
              key={alert.id}
              variant={
                alert.type === 'critical' ? 'destructive' :
                alert.type === 'warning' ? 'warning' : 'default'
              }
            >
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>{alert.type.toUpperCase()}</AlertTitle>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}
    </div>
  );
}
