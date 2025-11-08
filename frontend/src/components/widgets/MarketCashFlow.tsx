/**
 * Market Cash Flow Widget - Live cash flow analysis
 *
 * Features:
 * - Real-time Binance data
 * - Buyer/seller percentages across timeframes
 * - Risk assessment
 * - Top coins by cash flow
 */

import { useState, useEffect } from 'react';
import { DollarSign, TrendingUp, TrendingDown, AlertTriangle, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface CashFlowData {
  status: string;
  timestamp: string;
  market_metrics: {
    short_term_power: number;
    market_volume_share: number;
    timeframes: {
      '15m': { buyer_percentage: number; indicator: string };
      '1h': { buyer_percentage: number; indicator: string };
      '4h': { buyer_percentage: number; indicator: string };
      '12h': { buyer_percentage: number; indicator: string };
      '1d': { buyer_percentage: number; indicator: string };
    };
  };
  risk_assessment: {
    level: 'low' | 'medium' | 'high';
    message: string;
    buyer_1d: number;
  };
  top_flows: Array<{
    symbol: string;
    cash_share: number;
    buyer_15m: number;
    momentum: number;
    indicators: string;
  }>;
  total_coins: number;
}

export function MarketCashFlow() {
  const [data, setData] = useState<CashFlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCashFlow = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('http://localhost:8000/api/analysis/cash-flow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          live: true,
          format: 'json',
          top_n: 15,
          timeframe: '15m',
        }),
      });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      setLoading(false);
    } catch (err: any) {
      console.error('[Cash Flow] Error:', err);
      setError(err?.message || 'Failed to fetch cash flow data');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCashFlow();
    // Refresh every 2 minutes
    const interval = setInterval(fetchCashFlow, 120000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Market Cash Flow
          </CardTitle>
          <CardDescription>Analyzing market data...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-32 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Market Cash Flow
          </CardTitle>
          <CardDescription className="text-red-500">
            {error || 'No data available'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={fetchCashFlow} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
          <p className="text-xs text-muted-foreground mt-2">
            Make sure the API server is running on http://localhost:8000
          </p>
        </CardContent>
      </Card>
    );
  }

  const riskColor =
    data.risk_assessment.level === 'low'
      ? 'text-green-500'
      : data.risk_assessment.level === 'medium'
      ? 'text-yellow-500'
      : 'text-red-500';

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5" />
              💰 Market Cash Flow (LIVE)
            </CardTitle>
            <CardDescription>Real-time Binance data • Top {data.total_coins} coins</CardDescription>
          </div>
          <Button onClick={fetchCashFlow} variant="ghost" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Risk Assessment */}
        <div className={cn('p-4 rounded-lg border-2', riskColor.replace('text-', 'border-'))}>
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className={cn('w-5 h-5', riskColor)} />
            <span className={cn('font-bold text-lg', riskColor)}>
              {data.risk_assessment.level.toUpperCase()} RISK
            </span>
            <Badge variant="outline" className="ml-auto">
              1d: %{data.risk_assessment.buyer_1d.toFixed(1)}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">{data.risk_assessment.message}</p>
        </div>

        {/* Market Metrics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 bg-secondary rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Market Alım Gücü</div>
            <div className="text-2xl font-bold">{data.market_metrics.short_term_power}X</div>
          </div>
          <div className="p-3 bg-secondary rounded-lg">
            <div className="text-xs text-muted-foreground mb-1">Hacim Payı (Top 15)</div>
            <div className="text-2xl font-bold">%{data.market_metrics.market_volume_share.toFixed(1)}</div>
          </div>
        </div>

        {/* Timeframes */}
        <div>
          <h4 className="text-sm font-medium mb-2">Zaman Dilimlerine Göre Alım Oranları</h4>
          <div className="grid grid-cols-5 gap-2">
            {Object.entries(data.market_metrics.timeframes).map(([tf, metrics]) => (
              <div key={tf} className="p-2 bg-secondary rounded-lg text-center">
                <div className="text-xs text-muted-foreground">{tf}</div>
                <div className={cn(
                  'text-lg font-bold flex items-center justify-center gap-1',
                  metrics.buyer_percentage >= 50 ? 'text-green-500' : 'text-red-500'
                )}>
                  <span>{metrics.buyer_percentage.toFixed(1)}%</span>
                  <span className="text-base">{metrics.indicator}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Coins */}
        <div>
          <h4 className="text-sm font-medium mb-2">En Çok Nakit Girişi Olanlar</h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {data.top_flows.map((coin) => (
              <div
                key={coin.symbol}
                className="flex items-center justify-between p-2 bg-secondary rounded-lg hover:bg-secondary/80 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="font-medium min-w-[80px]">
                    {coin.symbol.replace('USDT', '')}
                  </span>
                  <Badge variant="outline" className="text-xs">
                    %{coin.cash_share.toFixed(1)}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    15m: %{coin.buyer_15m.toFixed(0)}
                  </span>
                  <Badge
                    variant={coin.momentum >= 1 ? 'default' : 'secondary'}
                    className="text-xs"
                  >
                    Mts: {coin.momentum.toFixed(1)}
                  </Badge>
                </div>
                <div className="flex items-center gap-1 text-sm">
                  {coin.indicators}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          Son güncelleme: {new Date(data.timestamp).toLocaleTimeString('tr-TR')} •
          Otomatik yenileme: 2 dakika
        </div>
      </CardContent>
    </Card>
  );
}
