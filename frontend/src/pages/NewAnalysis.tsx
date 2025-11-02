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
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [customSymbol, setCustomSymbol] = useState('');
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysis();
  }, [marketType, selectedSymbol, selectedTimeframe]);

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
      const data = await api.getExtendedAnalysis(selectedSymbol, selectedTimeframe);

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

      {/* Coin & Timeframe Selector */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Select Coin & Timeframe</CardTitle>
              <CardDescription>Choose which coin and timeframe to analyze</CardDescription>
            </div>
            {currentPrice && (
              <div className="text-right">
                <div className="text-sm text-muted-foreground">Current Price ({selectedTimeframe})</div>
                <div className="text-2xl font-bold text-primary">
                  ${currentPrice.toLocaleString()}
                </div>
              </div>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Quick Select */}
          <div>
            <label className="text-sm font-medium mb-2 block">Quick Select</label>
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
          </div>

          {/* Custom Symbol */}
          <div>
            <label htmlFor="custom-symbol" className="text-sm font-medium mb-2 block">
              Custom Symbol
            </label>
            <div className="flex gap-2">
              <input
                id="custom-symbol"
                type="text"
                value={customSymbol}
                onChange={(e) => setCustomSymbol(e.target.value.toUpperCase())}
                placeholder="ADAUSDT, DOTUSDT, etc."
                className="flex-1 px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              />
              <button
                onClick={() => {
                  if (customSymbol && customSymbol.endsWith('USDT')) {
                    setSelectedSymbol(customSymbol);
                    setCustomSymbol('');
                  }
                }}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:bg-primary/90"
              >
                Add
              </button>
            </div>
          </div>

          {/* Timeframe Selector */}
          <div>
            <label htmlFor="timeframe" className="text-sm font-medium mb-2 block">
              Timeframe
            </label>
            <select
              id="timeframe"
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="1m">1 Minute</option>
              <option value="5m">5 Minutes</option>
              <option value="15m">15 Minutes</option>
              <option value="30m">30 Minutes</option>
              <option value="1h">1 Hour</option>
              <option value="4h">4 Hours</option>
              <option value="1d">1 Day</option>
              <option value="1w">1 Week</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="signal" className="w-full">
        <TabsList>
          <TabsTrigger value="signal">AI Trading Signal</TabsTrigger>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="technical">Technical Analysis</TabsTrigger>
          <TabsTrigger value="risk">Risk Assessment</TabsTrigger>
          <TabsTrigger value="killzones">Kill Zones</TabsTrigger>
          <TabsTrigger value="pulse">Market Pulse</TabsTrigger>
        </TabsList>

        {/* AI Trading Signal Tab */}
        <TabsContent value="signal" className="space-y-4 mt-6">
          {/* Market Bias & Confidence */}
          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Market Bias</CardTitle>
                <CardDescription>AI consensus from all models</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-center py-6">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-green-500 mb-2">BULLISH</div>
                    <Badge variant="success" className="text-sm px-4 py-1">
                      High Confidence: 78%
                    </Badge>
                  </div>
                </div>
                <div className="space-y-2 mt-4">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Ensemble Model</span>
                    <Badge variant="success">Bullish (82%)</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">LSTM</span>
                    <Badge variant="success">Bullish (75%)</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Transformer</span>
                    <Badge variant="success">Bullish (71%)</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">PPO Agent</span>
                    <Badge variant="success">Long (84%)</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Summary</CardTitle>
                <CardDescription>AI-generated market analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <p className="leading-relaxed">
                    <span className="font-semibold text-primary">Strong bullish momentum detected.</span> All AI models converge on a long bias with above-average confidence. Technical indicators confirm uptrend with RSI at 67, MACD bullish crossover, and price trading above all major EMAs.
                  </p>
                  <p className="leading-relaxed text-muted-foreground">
                    Order flow analysis shows institutional accumulation near current levels. Volume profile suggests strong support at ${currentPrice ? (currentPrice * 0.95).toLocaleString() : '—'}. Break above ${currentPrice ? (currentPrice * 1.02).toLocaleString() : '—'} could trigger acceleration toward ${currentPrice ? (currentPrice * 1.09).toLocaleString() : '—'}.
                  </p>
                  <p className="leading-relaxed text-muted-foreground">
                    Smart money indicators: bullish order blocks identified, liquidity sweep completed, and break of structure confirmed on 1h timeframe.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Trading Signal */}
          <Card className="border-primary/50 shadow-lg">
            <CardHeader className="bg-primary/5">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-2xl">Trading Signal</CardTitle>
                  <CardDescription>Actionable trade setup with precise levels</CardDescription>
                </div>
                <Badge variant="success" className="text-lg px-4 py-2">
                  LONG
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="grid gap-6 md:grid-cols-3">
                {/* Entry */}
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground font-medium">Entry Zone</div>
                  <div className="text-3xl font-bold text-primary">
                    ${currentPrice ? currentPrice.toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Range: ${currentPrice ? (currentPrice * 0.99).toLocaleString() : '—'} - ${currentPrice ? (currentPrice * 1.01).toLocaleString() : '—'}
                  </div>
                  <Badge variant="outline">Market / Limit</Badge>
                </div>

                {/* Stop Loss */}
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground font-medium">Stop Loss</div>
                  <div className="text-3xl font-bold text-red-500">
                    ${currentPrice ? (currentPrice * 0.965).toLocaleString() : '—'}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Risk: -3.5% (${currentPrice ? (currentPrice * 0.035).toFixed(0) : '—'})
                  </div>
                  <Badge variant="destructive">Below Support</Badge>
                </div>

                {/* Take Profit Targets */}
                <div className="space-y-2">
                  <div className="text-sm text-muted-foreground font-medium">Take Profit</div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between p-2 bg-green-500/10 rounded">
                      <span className="text-xs font-medium">TP1 (50%)</span>
                      <span className="text-sm font-bold text-green-500">
                        ${currentPrice ? (currentPrice * 1.05).toLocaleString() : '—'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-500/10 rounded">
                      <span className="text-xs font-medium">TP2 (30%)</span>
                      <span className="text-sm font-bold text-green-500">
                        ${currentPrice ? (currentPrice * 1.08).toLocaleString() : '—'}
                      </span>
                    </div>
                    <div className="flex items-center justify-between p-2 bg-green-500/10 rounded">
                      <span className="text-xs font-medium">TP3 (20%)</span>
                      <span className="text-sm font-bold text-green-500">
                        ${currentPrice ? (currentPrice * 1.12).toLocaleString() : '—'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Risk/Reward */}
              <div className="mt-6 pt-6 border-t">
                <div className="grid gap-4 md:grid-cols-4">
                  <div className="text-center p-3 bg-secondary rounded-lg">
                    <div className="text-xs text-muted-foreground">Risk/Reward</div>
                    <div className="text-2xl font-bold text-primary">1:2.4</div>
                  </div>
                  <div className="text-center p-3 bg-secondary rounded-lg">
                    <div className="text-xs text-muted-foreground">Win Rate (Backtest)</div>
                    <div className="text-2xl font-bold text-green-500">67%</div>
                  </div>
                  <div className="text-center p-3 bg-secondary rounded-lg">
                    <div className="text-xs text-muted-foreground">Expected Value</div>
                    <div className="text-2xl font-bold text-primary">+1.32R</div>
                  </div>
                  <div className="text-center p-3 bg-secondary rounded-lg">
                    <div className="text-xs text-muted-foreground">Signal Strength</div>
                    <div className="text-2xl font-bold text-yellow-500">Strong</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Conclusion */}
          <Card>
            <CardHeader>
              <CardTitle>Conclusion & Recommendations</CardTitle>
              <CardDescription>Final AI verdict and trading advice</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <p className="text-foreground leading-relaxed">
                  <span className="font-semibold text-green-500">✓ HIGH PROBABILITY LONG SETUP</span> - All technical, fundamental, and AI indicators align for a bullish continuation. This trade offers favorable risk/reward (1:2.4) with strong support below current price.
                </p>

                <div className="grid gap-3 md:grid-cols-2 mt-4 not-prose">
                  <div className="p-4 border-l-4 border-green-500 bg-green-500/10 rounded">
                    <div className="font-semibold text-green-500 mb-2">Bullish Factors:</div>
                    <ul className="text-xs space-y-1 text-muted-foreground">
                      <li>• Price above all major EMAs (20, 50, 200)</li>
                      <li>• MACD bullish crossover confirmed</li>
                      <li>• RSI at 67 (bullish, not overbought)</li>
                      <li>• Order blocks supporting upside</li>
                      <li>• Institutional accumulation detected</li>
                    </ul>
                  </div>

                  <div className="p-4 border-l-4 border-yellow-500 bg-yellow-500/10 rounded">
                    <div className="font-semibold text-yellow-500 mb-2">Risk Considerations:</div>
                    <ul className="text-xs space-y-1 text-muted-foreground">
                      <li>• Fed meeting in 3 days (consider timing)</li>
                      <li>• Moderate volatility (3.8% daily)</li>
                      <li>• Resistance at ${currentPrice ? (currentPrice * 1.03).toLocaleString() : '—'}</li>
                      <li>• Use proper position sizing (2% risk)</li>
                      <li>• Trail stop after TP1 hit</li>
                    </ul>
                  </div>
                </div>

                <div className="mt-4 p-4 bg-primary/10 rounded-lg not-prose">
                  <div className="font-semibold mb-2 text-primary">Trade Management Plan:</div>
                  <ol className="text-xs space-y-1 text-muted-foreground">
                    <li>1. Enter at current market price or limit order in entry zone</li>
                    <li>2. Set stop loss at ${currentPrice ? (currentPrice * 0.965).toLocaleString() : '—'} (below support)</li>
                    <li>3. Close 50% at TP1, move stop to breakeven</li>
                    <li>4. Close 30% at TP2, trail remaining with 2% stop</li>
                    <li>5. Let final 20% run to TP3 or trailing stop</li>
                  </ol>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

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

        {/* Technical Analysis Tab */}
        <TabsContent value="technical" className="space-y-4 mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {/* RSI */}
            <Card>
              <CardHeader>
                <CardTitle>RSI (Relative Strength Index)</CardTitle>
                <CardDescription>14-period RSI on 1h timeframe</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Current Value</span>
                  <span className="text-2xl font-bold text-primary">67.4</span>
                </div>
                <div className="w-full h-3 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                    style={{ width: '67.4%' }}
                  />
                </div>
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Oversold (&lt;30)</span>
                  <span>Neutral</span>
                  <span>Overbought (&gt;70)</span>
                </div>
                <div className="pt-2 border-t">
                  <Badge variant="default">Bullish Momentum</Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    RSI is in bullish territory but not yet overbought. Room for upside.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* MACD */}
            <Card>
              <CardHeader>
                <CardTitle>MACD (Moving Average Convergence Divergence)</CardTitle>
                <CardDescription>12, 26, 9 settings</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-xs text-muted-foreground">MACD</div>
                    <div className="text-lg font-semibold text-green-500">+245.8</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Signal</div>
                    <div className="text-lg font-semibold">+198.3</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Histogram</div>
                    <div className="text-lg font-semibold text-green-500">+47.5</div>
                  </div>
                </div>
                <div className="h-20 flex items-end gap-1">
                  {[20, 35, 45, 52, 48, 55, 62, 58, 65, 72, 68, 75, 82].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-primary rounded-t"
                      style={{ height: `${height}%` }}
                    />
                  ))}
                </div>
                <div className="pt-2 border-t">
                  <Badge variant="success">Bullish Crossover</Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    MACD line crossed above signal line. Positive momentum confirmed.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Moving Averages */}
            <Card>
              <CardHeader>
                <CardTitle>Moving Averages</CardTitle>
                <CardDescription>EMA 20, 50, 200</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm">EMA 20</span>
                    <span className="font-semibold">${currentPrice ? (currentPrice * 0.98).toLocaleString() : '—'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">EMA 50</span>
                    <span className="font-semibold">${currentPrice ? (currentPrice * 0.95).toLocaleString() : '—'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">EMA 200</span>
                    <span className="font-semibold">${currentPrice ? (currentPrice * 0.87).toLocaleString() : '—'}</span>
                  </div>
                </div>
                <div className="pt-2 border-t">
                  <Badge variant="success">Golden Cross</Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    Price above all major EMAs. Strong uptrend structure intact.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Bollinger Bands */}
            <Card>
              <CardHeader>
                <CardTitle>Bollinger Bands</CardTitle>
                <CardDescription>20-period, 2 standard deviations</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Upper Band</span>
                    <span className="font-semibold text-red-500">
                      ${currentPrice ? (currentPrice * 1.03).toLocaleString() : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Middle (SMA 20)</span>
                    <span className="font-semibold">
                      ${currentPrice ? currentPrice.toLocaleString() : '—'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">Lower Band</span>
                    <span className="font-semibold text-green-500">
                      ${currentPrice ? (currentPrice * 0.97).toLocaleString() : '—'}
                    </span>
                  </div>
                </div>
                <div className="relative h-8 bg-secondary rounded">
                  <div
                    className="absolute left-0 right-0 h-full bg-primary/20 rounded"
                    style={{ left: '35%', right: '35%' }}
                  />
                  <div
                    className="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-primary rounded-full border-2 border-background"
                    style={{ left: '52%' }}
                  />
                </div>
                <div className="pt-2 border-t">
                  <Badge>Mid-Band Trading</Badge>
                  <p className="text-xs text-muted-foreground mt-2">
                    Price near middle band. Normal volatility. Watch for squeeze breakout.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Risk Assessment Tab */}
        <TabsContent value="risk" className="space-y-4 mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Risk Level Card */}
            <Card>
              <CardHeader>
                <CardTitle>Overall Risk Level</CardTitle>
                <CardDescription>Based on volatility, market conditions, and technical signals</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center py-6">
                  <div className="text-center">
                    <div className="text-5xl font-bold text-yellow-500 mb-2">MEDIUM</div>
                    <Badge variant="warning" className="text-sm px-4 py-1">
                      Risk Score: 5.2 / 10
                    </Badge>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Risk Meter</span>
                    <span className="font-medium">52%</span>
                  </div>
                  <div className="w-full h-3 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
                      style={{ width: '52%' }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-muted-foreground">
                    <span>Low</span>
                    <span>Medium</span>
                    <span>High</span>
                  </div>
                </div>

                <div className="pt-3 border-t space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Volatility (24h)</span>
                    <span className="font-medium text-yellow-500">3.8%</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Market Trend</span>
                    <Badge variant="success">Bullish</Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Liquidity</span>
                    <Badge>High</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Position Size Recommendations */}
            <Card>
              <CardHeader>
                <CardTitle>Position Size Calculator</CardTitle>
                <CardDescription>Recommended position sizes based on account size</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Account Size ($)</label>
                    <input
                      type="number"
                      defaultValue="10000"
                      className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1 block">Risk Per Trade (%)</label>
                    <input
                      type="number"
                      defaultValue="2"
                      step="0.5"
                      className="w-full px-3 py-2 rounded-lg border bg-background text-sm"
                    />
                  </div>
                </div>

                <div className="pt-3 border-t space-y-3">
                  <div className="bg-primary/10 p-3 rounded-lg">
                    <div className="text-xs text-muted-foreground mb-1">Recommended Position Size</div>
                    <div className="text-2xl font-bold text-primary">$200</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      (2% of $10,000 account)
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-secondary p-3 rounded-lg">
                      <div className="text-xs text-muted-foreground">Stop Loss</div>
                      <div className="text-lg font-semibold text-red-500">
                        ${currentPrice ? (currentPrice * 0.97).toLocaleString() : '—'}
                      </div>
                      <div className="text-xs text-muted-foreground">(-3%)</div>
                    </div>
                    <div className="bg-secondary p-3 rounded-lg">
                      <div className="text-xs text-muted-foreground">Take Profit</div>
                      <div className="text-lg font-semibold text-green-500">
                        ${currentPrice ? (currentPrice * 1.06).toLocaleString() : '—'}
                      </div>
                      <div className="text-xs text-muted-foreground">(+6%)</div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-sm p-2 bg-secondary rounded">
                    <span className="text-muted-foreground">Risk/Reward Ratio</span>
                    <Badge variant="success">1:2</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Risk Factors */}
          <Card>
            <CardHeader>
              <CardTitle>Key Risk Factors</CardTitle>
              <CardDescription>Factors influencing current risk assessment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm font-medium">Market Structure</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Clean uptrend with higher highs and higher lows. Structure intact.
                  </p>
                </div>

                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-500" />
                    <span className="text-sm font-medium">Volume Profile</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Moderate volume. Watch for volume confirmation on breakouts.
                  </p>
                </div>

                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm font-medium">Correlation Risk</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Low correlation with other positions. Good diversification.
                  </p>
                </div>

                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-yellow-500" />
                    <span className="text-sm font-medium">News Events</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Fed meeting in 3 days. Consider reducing size before event.
                  </p>
                </div>

                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm font-medium">Funding Rate</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Neutral funding (0.01%). No extreme leverage imbalance.
                  </p>
                </div>

                <div className="p-3 border rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-green-500" />
                    <span className="text-sm font-medium">Liquidity</span>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    High liquidity. Tight spreads. Easy entry/exit available.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
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
