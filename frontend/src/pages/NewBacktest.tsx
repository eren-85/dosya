/**
 * Backtest Page
 * - Parameters configuration
 * - Run/stop controls
 * - PnL curve visualization
 * - Performance metrics (Sharpe, MDD, Win Rate)
 */

import React, { useState } from 'react';
import { Play, Square, TrendingUp, TrendingDown, Target, Activity } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  const [strategy, setStrategy] = useState('ppo');
  const [initialCapital, setInitialCapital] = useState(10000);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BacktestResults | null>(null);

  const handleRunBacktest = async () => {
    setLoading(true);
    try {
      const data = await api.runBacktest({
        symbol,
        timeframe,
        initial_capital: initialCapital,
        strategy,
      });

      // Mock results for demo
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Backtest</h1>
        <p className="text-muted-foreground">
          Test your strategies on historical data
        </p>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Backtest Configuration</CardTitle>
          <CardDescription>Set parameters for your backtest</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Symbol</label>
              <input
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              >
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Strategy</label>
              <select
                value={strategy}
                onChange={(e) => setStrategy(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              >
                <option value="ppo">PPO Agent</option>
                <option value="ensemble">Ensemble</option>
                <option value="lstm">LSTM</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Initial Capital ($)</label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
            </div>
          </div>

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
              <div className="flex items-center gap-2">
                {results.sharpe > 2 && results.maxDrawdown > -15 ? (
                  <>
                    <Badge variant="success">Excellent Performance</Badge>
                    <p className="text-sm text-muted-foreground">
                      High risk-adjusted returns with controlled drawdown
                    </p>
                  </>
                ) : (
                  <>
                    <Badge variant="default">Good Performance</Badge>
                    <p className="text-sm text-muted-foreground">
                      Positive results with room for optimization
                    </p>
                  </>
                )}
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
