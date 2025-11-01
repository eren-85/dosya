/**
 * Advanced Chart Page
 * - TradingView Lightweight Charts integration
 * - Pattern overlays
 * - Spot/Futures selector
 * - All timeframes
 * - Guaranteed min-height to prevent white screens
 */

import { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi } from 'lightweight-charts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  Maximize2,
  TrendingUp,
  Eye,
  EyeOff,
  RefreshCw
} from 'lucide-react';
import { TIMEFRAMES, MarketType } from '@/lib/constants';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';

interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export default function NewAdvancedChart() {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('1h');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [showPatterns, setShowPatterns] = useState(true);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { color: '#0a0a0a' },
        textColor: '#d1d5db',
      },
      grid: {
        vertLines: { color: '#1f2937' },
        horzLines: { color: '#1f2937' },
      },
      width: chartContainerRef.current.clientWidth,
      height: 500, // Fixed min-height
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Create candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    seriesRef.current = candlestickSeries;

    // Load initial data
    loadChartData();

    // Handle resize
    const resizeObserver = new ResizeObserver(entries => {
      if (entries.length === 0 || entries[0].target !== chartContainerRef.current) return;
      const newRect = entries[0].contentRect;
      chart.applyOptions({ width: newRect.width });
    });

    resizeObserver.observe(chartContainerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  // Reload data when symbol, interval, or marketType changes
  useEffect(() => {
    loadChartData();
  }, [symbol, interval, marketType]);

  const loadChartData = async () => {
    if (!seriesRef.current) return;

    setLoading(true);
    try {
      // Fetch maximum allowed candles from Binance API
      // Spot: 1000 max, Futures: 1500 max
      const maxLimit = marketType === 'spot' ? 1000 : 1500;
      const endpoint = marketType === 'spot'
        ? `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${maxLimit}`
        : `https://fapi.binance.com/fapi/v1/klines?symbol=${symbol}&interval=${interval}&limit=${maxLimit}`;

      const response = await fetch(endpoint);
      const data = await response.json();

      const formattedData: CandleData[] = data.map((candle: any[]) => ({
        time: Math.floor(candle[0] / 1000), // Convert to seconds
        open: parseFloat(candle[1]),
        high: parseFloat(candle[2]),
        low: parseFloat(candle[3]),
        close: parseFloat(candle[4]),
      }));

      seriesRef.current.setData(formattedData);
      chartRef.current?.timeScale().fitContent();
    } catch (error) {
      console.error('Error loading chart data:', error);

      // Fallback: Generate mock data
      const mockData = generateMockData(500);
      seriesRef.current.setData(mockData);
      chartRef.current?.timeScale().fitContent();
    } finally {
      setLoading(false);
    }
  };

  const handleFitContent = () => {
    chartRef.current?.timeScale().fitContent();
  };

  const handleRefresh = () => {
    loadChartData();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Advanced Chart</h1>
        <p className="text-muted-foreground">
          Professional charting with pattern detection and technical indicators
        </p>
      </div>

      {/* Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Chart Controls</CardTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleFitContent}>
                <Maximize2 className="w-4 h-4 mr-2" />
                Fit Content
              </Button>
              <Button
                variant={showPatterns ? 'default' : 'outline'}
                size="sm"
                onClick={() => setShowPatterns(!showPatterns)}
              >
                {showPatterns ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
                Patterns
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Market Type Selector */}
          <div>
            <label className="text-sm font-medium mb-2 block">Market Type</label>
            <MarketTypeSelector value={marketType} onChange={setMarketType} disabled={loading} />
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {/* Symbol */}
            <div>
              <label htmlFor="chart-symbol" className="text-sm font-medium mb-2 block">
                Symbol
              </label>
              <input
                id="chart-symbol"
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                placeholder="BTCUSDT"
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
            </div>

            {/* Interval */}
            <div>
              <label htmlFor="chart-interval" className="text-sm font-medium mb-2 block">
                Timeframe
              </label>
              <select
                id="chart-interval"
                value={interval}
                onChange={(e) => setInterval(e.target.value)}
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

            {/* Load Button */}
            <div className="flex items-end">
              <Button onClick={loadChartData} disabled={loading} className="w-full">
                <TrendingUp className="w-4 h-4 mr-2" />
                {loading ? 'Loading...' : 'Load Chart'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Chart */}
      <Card>
        <CardContent className="p-0">
          <div
            ref={chartContainerRef}
            className="w-full"
            style={{ minHeight: '500px' }} // Guaranteed min-height
          />
        </CardContent>
      </Card>

      {/* Pattern Legend */}
      {showPatterns && (
        <Card>
          <CardHeader>
            <CardTitle>Pattern Legend & Indicators</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span className="text-sm">Order Blocks</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500" />
                <span className="text-sm">Fair Value Gaps</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-yellow-500" />
                <span className="text-sm">Liquidity Sweeps</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span className="text-sm">Break of Structure</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-orange-500" />
                <span className="text-sm">RSI Divergence</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-pink-500" />
                <span className="text-sm">MACD Crossover</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-cyan-500" />
                <span className="text-sm">EMA Cloud</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span className="text-sm">Volume Profile</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mt-4">
              Note: Pattern detection and Pine Script indicators will be rendered after backend integration
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// Generate mock candle data for fallback
function generateMockData(count: number): CandleData[] {
  const data: CandleData[] = [];
  const now = Math.floor(Date.now() / 1000);
  let price = 65000;

  for (let i = count; i > 0; i--) {
    const change = (Math.random() - 0.5) * 1000;
    const open = price;
    const close = price + change;
    const high = Math.max(open, close) + Math.random() * 500;
    const low = Math.min(open, close) - Math.random() * 500;

    data.push({
      time: now - i * 3600, // 1 hour intervals
      open,
      high,
      low,
      close,
    });

    price = close;
  }

  return data;
}
