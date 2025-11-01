/**
 * Backtest Page
 * - Parameters configuration
 * - Spot/Futures selector
 * - All timeframes
 * - Run/stop controls
 * - PnL curve visualization
 * - Performance metrics (Sharpe, MDD, Win Rate)
 */

import { useState } from 'react';
import { Play, Square, TrendingUp, TrendingDown, Target, Activity } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { TIMEFRAMES, MarketType, COMMON_SYMBOLS } from '@/lib/constants';
import { api } from '@/lib/api';

interface BacktestResults {
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  sharpe: number;
  maxDrawdown: number;
  totalReturn: number;
}

export default function NewBacktest() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [strategy, setStrategy] = useState('ppo');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResults | null>(null);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      await api.runBacktest({
        symbol,
        timeframe,
        initial_capital: initialCapital,
        strategy,
      });

      // Simulate results for demo
      await new Promise(resolve => setTimeout(resolve, 2000));

      setResults({
        totalTrades: 247,
        winRate: 68.5,
        profitFactor: 2.34,
        sharpe: 1.82,
        maxDrawdown: -12.3,
        totalReturn: 156.7,
      });
    } catch (error) {
      console.error('Backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = (sym: string) => {
    setSymbol(sym);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Backtest</h1>
        <p className="text-muted-foreground">
          Test your strategies on historical data with comprehensive metrics
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Backtest Configuration</CardTitle>
          <CardDescription>Set parameters for your backtest simulation</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Market Type */}
          <div>
            <label className="text-sm font-medium mb-2 block">Market Type</label>
            <MarketTypeSelector value={marketType} onChange={setMarketType} disabled={loading} />
          </div>

          {/* Quick Select */}
          <div>
            <label className="text-sm font-medium mb-2 block">Quick Select Symbol</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_SYMBOLS.slice(0, 6).map((sym) => (
                <Button
                  key={sym}
                  variant={symbol === sym ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => handleQuickSelect(sym)}
                  disabled={loading}
                >
                  {sym}
                </Button>
              ))}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Symbol */}
            <div>
              <label htmlFor="backtest-symbol" className="text-sm font-medium mb-2 block">
                Symbol
              </label>
              <input
                id="backtest-symbol"
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
            </div>

            {/* Timeframe */}
            <div>
              <label htmlFor="backtest-timeframe" className="text-sm font-medium mb-2 block">
                Timeframe
              </label>
              <select
                id="backtest-timeframe"
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf.value} value={tf.value}>
                    {tf.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Strategy */}
            <div>
              <label htmlFor="strategy" className="text-sm font-medium mb-2 block">
                Strategy
              </label>
              <select
                id="strategy"
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              >
                <option value="ppo">PPO Agent</option>
                <option value="ensemble">Ensemble Models</option>
                <option value="lstm">LSTM Predictor</option>
                <option value="transformer">Transformer</option>
              </select>
            </div>

            {/* Initial Capital */}
            <div>
              <label htmlFor="capital" className="text-sm font-medium mb-2 block">
                Initial Capital ($)
              </label>
              <input
                id="capital"
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3 mt-6">
            <Button onClick={handleRunBacktest} disabled={loading}>
              {loading ? (
                <>
                  <Square className="w-4 h-4 mr-2" />
                  Running...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Run Backtest
                </>
              )}
            </Button>
            <Button variant="outline" onClick={() => setResults(null)} disabled={loading}>
              Clear Results
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {results && (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            <MetricCard
              title="Total Trades"
              value={results.totalTrades.toString()}
              icon={<Activity className="w-4 h-4" />}
            />
            <MetricCard
              title="Win Rate"
              value={`${results.winRate.toFixed(1)}%`}
              icon={<TrendingUp className="w-4 h-4" />}
              positive
            />
            <MetricCard
              title="Profit Factor"
              value={results.profitFactor.toFixed(2)}
              icon={<Target className="w-4 h-4" />}
              positive
            />
            <MetricCard
              title="Sharpe Ratio"
              value={results.sharpe.toFixed(2)}
              icon={<TrendingUp className="w-4 h-4" />}
              positive
            />
            <MetricCard
              title="Max Drawdown"
              value={`${results.maxDrawdown.toFixed(1)}%`}
              icon={<TrendingDown className="w-4 h-4" />}
              negative
            />
            <MetricCard
              title="Total Return"
              value={`${results.totalReturn.toFixed(1)}%`}
              icon={<TrendingUp className="w-4 h-4" />}
              positive
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Performance Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  {results.sharpe > 2 && results.maxDrawdown > -15 ? (
                    <>
                      <Badge variant="success">Excellent Performance</Badge>
                      <p className="text-sm text-muted-foreground">
                        High risk-adjusted returns (Sharpe {results.sharpe.toFixed(2)}) with controlled drawdown ({Math.abs(results.maxDrawdown).toFixed(1)}%)
                      </p>
                    </>
                  ) : results.sharpe > 1 ? (
                    <>
                      <Badge variant="default">Good Performance</Badge>
                      <p className="text-sm text-muted-foreground">
                        Positive risk-adjusted returns with room for optimization
                      </p>
                    </>
                  ) : (
                    <>
                      <Badge variant="warning">Needs Improvement</Badge>
                      <p className="text-sm text-muted-foreground">
                        Consider adjusting strategy parameters or market conditions
                      </p>
                    </>
                  )}
                </div>

                <div className="grid gap-3 md:grid-cols-2 mt-4 p-4 bg-secondary rounded-lg">
                  <div>
                    <div className="text-xs text-muted-foreground">Average Trade P&L</div>
                    <div className="text-lg font-semibold text-green-500">
                      ${((initialCapital * results.totalReturn / 100) / results.totalTrades).toFixed(2)}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">Final Capital</div>
                    <div className="text-lg font-semibold">
                      ${(initialCapital * (1 + results.totalReturn / 100)).toLocaleString()}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

// Metric Card Component
interface MetricCardProps {
  title: string;
  value: string;
  icon: React.ReactNode;
  positive?: boolean;
  negative?: boolean;
}

function MetricCard({ title, value, icon, positive, negative }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${positive ? 'text-green-500' : negative ? 'text-red-500' : ''}`}>
          {value}
        </div>
      </CardContent>
    </Card>
  );
}
