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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  const chartCardRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);
  const emaSeriesRefs = useRef<{
    ema21?: ISeriesApi<'Line'>;
    ema50?: ISeriesApi<'Line'>;
    ema100?: ISeriesApi<'Line'>;
    ema200?: ISeriesApi<'Line'>;
  }>({});

  const [symbol, setSymbol] = useState('BTCUSDT');
  const [interval, setInterval] = useState('1h');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [showPatterns, setShowPatterns] = useState(true);
  const [showEMA, setShowEMA] = useState(true);
  const [showOrderBlocks, setShowOrderBlocks] = useState(true);
  const [showFVG, setShowFVG] = useState(true);
  const [showLiquiditySweeps, setShowLiquiditySweeps] = useState(true);
  const [loading, setLoading] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

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

  // Reload data when symbol, interval, marketType, or toggles change
  useEffect(() => {
    loadChartData();
  }, [symbol, interval, marketType, showEMA, showOrderBlocks, showFVG, showLiquiditySweeps]);

  const loadChartData = async () => {
    if (!seriesRef.current || !chartRef.current) return;

    setLoading(true);
    try {
      // Clear existing EMA series before reloading
      if (emaSeriesRefs.current.ema21) {
        chartRef.current.removeSeries(emaSeriesRefs.current.ema21);
        emaSeriesRefs.current.ema21 = undefined;
      }
      if (emaSeriesRefs.current.ema50) {
        chartRef.current.removeSeries(emaSeriesRefs.current.ema50);
        emaSeriesRefs.current.ema50 = undefined;
      }
      if (emaSeriesRefs.current.ema100) {
        chartRef.current.removeSeries(emaSeriesRefs.current.ema100);
        emaSeriesRefs.current.ema100 = undefined;
      }
      if (emaSeriesRefs.current.ema200) {
        chartRef.current.removeSeries(emaSeriesRefs.current.ema200);
        emaSeriesRefs.current.ema200 = undefined;
      }

      let formattedData: CandleData[];

      console.log('[Chart] Loading data from backend...');

      // Fetch ALL data from backend (Parquet files)
      // Backend will prioritize: 1. Parquet files, 2. Binance API, 3. Mock data
      const marketTypeParam = marketType === 'spot' ? 'spot' : 'futures';
      const endpoint = `http://localhost:8000/api/data/ohlcv?symbol=${symbol}&timeframe=${interval}&market_type=${marketTypeParam}&limit=0`;

      const response = await fetch(endpoint);
      const result = await response.json();

      console.log('[Chart] Backend response:', result.source, result.count, 'candles');

      if (result.status === 'success' && result.data && result.data.length > 0) {
        formattedData = result.data.map((candle: any) => ({
          time: candle.time,
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        }));
      } else {
        throw new Error('No data received from backend');
      }

      // Ensure we have valid data
      if (!formattedData || formattedData.length === 0) {
        throw new Error('No data received from API');
      }

      seriesRef.current.setData(formattedData);

      // Add EMA lines (if enabled)
      if (showEMA) {
        addEMALines(formattedData);
      }

      // Add pattern indicators (if enabled)
      if (formattedData.length > 0) {
        addPatternIndicators(formattedData);
      }

      chartRef.current?.timeScale().fitContent();
    } catch (error) {
      console.error('[Chart] Error loading chart data:', error);
      alert(`Failed to load chart data for ${symbol}. Backend error: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  const addPatternIndicators = (data: CandleData[]) => {
    if (!seriesRef.current || !chartRef.current) return;

    console.log('[Chart] Adding pattern indicators, data length:', data.length);

    // Detect Order Blocks (simplified algorithm)
    const orderBlocks = detectOrderBlocks(data);
    console.log('[Chart] Order Blocks detected:', orderBlocks.length, orderBlocks);

    // Detect Fair Value Gaps
    const fvgAreas = detectFairValueGaps(data);
    console.log('[Chart] FVG Areas detected:', fvgAreas.length, fvgAreas);

    // Detect Liquidity Sweeps
    const liquiditySweeps = detectLiquiditySweeps(data);
    console.log('[Chart] Liquidity Sweeps detected:', liquiditySweeps.length, liquiditySweeps);

    // Add markers for patterns (conditionally based on toggles)
    const markers: any[] = [];

    // Order Block markers (if enabled)
    if (showOrderBlocks) {
      orderBlocks.forEach((ob) => {
        markers.push({
          time: ob.time,
          position: ob.type === 'bullish' ? 'belowBar' : 'aboveBar',
          color: ob.type === 'bullish' ? '#22c55e' : '#ef4444',
          shape: 'square',
          text: 'OB',
        });
      });
    }

    // Fair Value Gap markers (if enabled)
    if (showFVG) {
      fvgAreas.forEach((fvg, idx) => {
        const marker = {
          time: fvg.time,
          position: fvg.type === 'bullish' ? 'belowBar' : 'aboveBar',
          color: fvg.type === 'bullish' ? '#3b82f6' : '#f97316',
          shape: 'arrowUp', // Changed from 'circle' to 'arrowUp' for better visibility
          text: 'FVG',
        };
        if (idx === 0) console.log('[Chart] FVG marker sample:', marker);
        markers.push(marker);
      });
    }

    // Liquidity Sweep markers (if enabled)
    if (showLiquiditySweeps) {
      liquiditySweeps.forEach((ls) => {
        markers.push({
          time: ls.time,
          position: ls.type === 'high' ? 'aboveBar' : 'belowBar',
          color: '#eab308',
          shape: 'arrowDown',
          text: 'LS',
        });
      });
    }

    // Sort markers by time (REQUIRED by TradingView Lightweight Charts)
    markers.sort((a, b) => a.time - b.time);
    console.log('[Chart] Total markers to add (sorted):', markers.length);

    seriesRef.current.setMarkers(markers);

    // Add price lines for FVG zones (if enabled)
    if (showFVG) {
      fvgAreas.forEach((fvg, idx) => {
        // Top line of FVG zone
        seriesRef.current?.createPriceLine({
          price: fvg.top,
          color: fvg.type === 'bullish' ? '#3b82f680' : '#f9731680',
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: false,
          title: `FVG ${fvg.type === 'bullish' ? '↑' : '↓'}`,
        });

        // Bottom line of FVG zone
        seriesRef.current?.createPriceLine({
          price: fvg.bottom,
          color: fvg.type === 'bullish' ? '#3b82f680' : '#f9731680',
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: false,
          title: '',
        });
      });
    }

    // Add price lines for support/resistance
    const supportResistance = detectSupportResistance(data);
    console.log('[Chart] Support/Resistance levels:', supportResistance.length);
    supportResistance.forEach((level) => {
      seriesRef.current?.createPriceLine({
        price: level.price,
        color: level.type === 'support' ? '#22c55e' : '#ef4444',
        lineWidth: 1,
        lineStyle: 2, // Dashed
        axisLabelVisible: true,
        title: level.type === 'support' ? 'Support' : 'Resistance',
      });
    });
  };

  // Aggregate candles from smaller timeframe
  const aggregateCandles = (data: CandleData[], factor: number): CandleData[] => {
    const aggregated: CandleData[] = [];

    for (let i = 0; i < data.length; i += factor) {
      const chunk = data.slice(i, i + factor);
      if (chunk.length === 0) continue;

      const aggregatedCandle: CandleData = {
        time: chunk[0].time,
        open: chunk[0].open,
        high: Math.max(...chunk.map(c => c.high)),
        low: Math.min(...chunk.map(c => c.low)),
        close: chunk[chunk.length - 1].close,
      };

      aggregated.push(aggregatedCandle);
    }

    return aggregated;
  };

  // Pattern detection algorithms (more sensitive for better detection)
  const detectOrderBlocks = (data: CandleData[]) => {
    const blocks: any[] = [];
    for (let i = 3; i < data.length - 3; i++) {
      const candle = data[i];
      const prevCandles = data.slice(i - 3, i);
      const nextCandles = data.slice(i + 1, i + 4);

      // Bullish Order Block: Strong bearish candle followed by bullish movement
      const isBearish = candle.close < candle.open;
      const strongMove = Math.abs(candle.close - candle.open) > (candle.high - candle.low) * 0.5; // Less strict
      const bullishAfter = nextCandles.filter(c => c.close > c.open).length >= 2; // Less strict

      if (isBearish && strongMove && bullishAfter) {
        blocks.push({ time: candle.time, type: 'bullish', price: candle.low });
      }

      // Bearish Order Block: Strong bullish candle followed by bearish movement
      const isBullish = candle.close > candle.open;
      const bearishAfter = nextCandles.filter(c => c.close < c.open).length >= 2; // Less strict

      if (isBullish && strongMove && bearishAfter) {
        blocks.push({ time: candle.time, type: 'bearish', price: candle.high });
      }
    }
    return blocks.slice(-15); // Return last 15 order blocks (more patterns)
  };

  const detectFairValueGaps = (data: CandleData[]) => {
    const gaps: any[] = [];
    for (let i = 1; i < data.length - 1; i++) {
      const prev = data[i - 1];
      const curr = data[i];
      const next = data[i + 1];

      // Bullish FVG: Gap between prev high and next low
      if (prev.high < next.low) {
        gaps.push({
          time: curr.time,
          type: 'bullish',
          top: next.low,
          bottom: prev.high,
        });
      }

      // Bearish FVG: Gap between prev low and next high
      if (prev.low > next.high) {
        gaps.push({
          time: curr.time,
          type: 'bearish',
          top: prev.low,
          bottom: next.high,
        });
      }
    }
    return gaps.slice(-5); // Return last 5 FVGs
  };

  const detectLiquiditySweeps = (data: CandleData[]) => {
    const sweeps: any[] = [];
    for (let i = 10; i < data.length; i++) { // Less history needed
      const curr = data[i];
      const recent = data.slice(i - 10, i);
      const recentHigh = Math.max(...recent.map(d => d.high));
      const recentLow = Math.min(...recent.map(d => d.low));

      // Sweep high (liquidity grab above) - less strict
      if (curr.high >= recentHigh * 1.001) { // Just 0.1% above is enough
        sweeps.push({ time: curr.time, type: 'high', price: curr.high });
      }

      // Sweep low (liquidity grab below) - less strict
      if (curr.low <= recentLow * 0.999) { // Just 0.1% below is enough
        sweeps.push({ time: curr.time, type: 'low', price: curr.low });
      }
    }
    return sweeps.slice(-12); // Return last 12 sweeps (more patterns)
  };

  const detectSupportResistance = (data: CandleData[]) => {
    const levels: any[] = [];
    const prices = data.map(d => d.close);
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const range = high - low;

    // Add major support/resistance levels
    levels.push({ price: high, type: 'resistance' });
    levels.push({ price: low, type: 'support' });
    levels.push({ price: low + range * 0.5, type: 'support' });
    levels.push({ price: low + range * 0.618, type: 'resistance' }); // Fibonacci

    return levels;
  };

  // Calculate EMA (Exponential Moving Average)
  const calculateEMA = (data: CandleData[], period: number) => {
    const emaData: { time: number; value: number }[] = [];
    const k = 2 / (period + 1);

    // Start with SMA for the first value
    let ema = 0;
    for (let i = 0; i < Math.min(period, data.length); i++) {
      ema += data[i].close;
    }
    ema = ema / Math.min(period, data.length);

    for (let i = period - 1; i < data.length; i++) {
      if (i === period - 1) {
        emaData.push({ time: data[i].time, value: ema });
      } else {
        ema = data[i].close * k + ema * (1 - k);
        emaData.push({ time: data[i].time, value: ema });
      }
    }

    return emaData;
  };

  // Add EMA lines to chart
  const addEMALines = (data: CandleData[]) => {
    if (!chartRef.current || data.length < 200) return; // Need enough data for EMA 200

    console.log('[Chart] Adding EMA lines...');

    // Calculate EMAs
    const ema21 = calculateEMA(data, 21);
    const ema50 = calculateEMA(data, 50);
    const ema100 = calculateEMA(data, 100);
    const ema200 = calculateEMA(data, 200);

    // Add or update EMA 21 (Yellow)
    if (!emaSeriesRefs.current.ema21) {
      emaSeriesRefs.current.ema21 = chartRef.current.addLineSeries({
        color: '#eab308',
        lineWidth: 2,
        title: 'EMA 21',
      });
    }
    emaSeriesRefs.current.ema21.setData(ema21);

    // Add or update EMA 50 (Blue)
    if (!emaSeriesRefs.current.ema50) {
      emaSeriesRefs.current.ema50 = chartRef.current.addLineSeries({
        color: '#3b82f6',
        lineWidth: 2,
        title: 'EMA 50',
      });
    }
    emaSeriesRefs.current.ema50.setData(ema50);

    // Add or update EMA 100 (Purple)
    if (!emaSeriesRefs.current.ema100) {
      emaSeriesRefs.current.ema100 = chartRef.current.addLineSeries({
        color: '#a855f7',
        lineWidth: 2,
        title: 'EMA 100',
      });
    }
    emaSeriesRefs.current.ema100.setData(ema100);

    // Add or update EMA 200 (Red)
    if (!emaSeriesRefs.current.ema200) {
      emaSeriesRefs.current.ema200 = chartRef.current.addLineSeries({
        color: '#ef4444',
        lineWidth: 3,
        title: 'EMA 200',
      });
    }
    emaSeriesRefs.current.ema200.setData(ema200);

    console.log('[Chart] EMA lines added successfully');
  };

  const handleFitContent = () => {
    chartRef.current?.timeScale().fitContent();
  };

  const handleRefresh = () => {
    loadChartData();
  };

  const handleFullscreen = async () => {
    const chartCard = chartCardRef.current;
    if (!chartCard) return;

    try {
      if (!document.fullscreenElement) {
        await chartCard.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      console.error('Fullscreen error:', err);
    }
  };

  // Listen for fullscreen changes (e.g., user presses ESC)
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);

      // Resize chart when entering/exiting fullscreen
      if (chartRef.current) {
        setTimeout(() => {
          chartRef.current?.resize(
            chartContainerRef.current?.clientWidth || 800,
            document.fullscreenElement ? window.innerHeight - 100 : 500
          );
        }, 100);
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

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
            <div className="flex items-center gap-2 flex-wrap">
              <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
                <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" size="sm" onClick={handleFitContent}>
                <Maximize2 className="w-4 h-4 mr-2" />
                Fit Content
              </Button>
              <Button variant="outline" size="sm" onClick={handleFullscreen}>
                <Maximize2 className="w-4 h-4 mr-2" />
                {isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
              </Button>

              {/* Indicator Toggles */}
              <div className="flex items-center gap-1 ml-2 pl-2 border-l">
                <Button
                  variant={showEMA ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setShowEMA(!showEMA)}
                  title="Toggle EMA lines"
                >
                  EMA
                </Button>
                <Button
                  variant={showOrderBlocks ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setShowOrderBlocks(!showOrderBlocks)}
                  title="Toggle Order Blocks"
                >
                  OB
                </Button>
                <Button
                  variant={showFVG ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setShowFVG(!showFVG)}
                  title="Toggle Fair Value Gaps"
                >
                  FVG
                </Button>
                <Button
                  variant={showLiquiditySweeps ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setShowLiquiditySweeps(!showLiquiditySweeps)}
                  title="Toggle Liquidity Sweeps"
                >
                  LS
                </Button>
              </div>
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
      <div ref={chartCardRef}>
        <Card>
          <CardContent className="p-0">
            <div
              ref={chartContainerRef}
              className="w-full"
              style={{ minHeight: '500px' }} // Guaranteed min-height
            />
          </CardContent>
        </Card>
      </div>

      {/* Pattern Legend */}
      {(showEMA || showOrderBlocks || showFVG || showLiquiditySweeps) && (
        <Card>
          <CardHeader>
            <CardTitle>Smart Money Concepts & Patterns</CardTitle>
            <CardDescription>Active pattern detection and key price levels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Pattern Markers */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Pattern Markers</h4>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  <div className="flex items-start gap-3 p-2 rounded-lg bg-secondary/50">
                    <div className="w-4 h-4 rounded bg-green-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium">Order Blocks (OB)</div>
                      <div className="text-xs text-muted-foreground">Institutional supply/demand zones</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-2 rounded-lg bg-secondary/50">
                    <div className="w-4 h-4 rounded-full bg-blue-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium">Fair Value Gaps (FVG)</div>
                      <div className="text-xs text-muted-foreground">Price imbalance zones with horizontal lines</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 p-2 rounded-lg bg-secondary/50">
                    <div className="w-4 h-4 rounded-full bg-yellow-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-sm font-medium">Liquidity Sweeps (LS)</div>
                      <div className="text-xs text-muted-foreground">Stop hunts and liquidity grabs</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Price Levels */}
              <div>
                <h4 className="text-sm font-semibold mb-2">Key Price Levels</h4>
                <div className="grid gap-2 md:grid-cols-2">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 border-t-2 border-dashed border-green-500" />
                    <span className="text-sm">Support (Green dashed)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 border-t-2 border-dashed border-red-500" />
                    <span className="text-sm">Resistance (Red dashed)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 border-t-2 border-blue-400" />
                    <span className="text-sm">FVG Zone (Blue/Orange solid)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-0.5 border-t-2 border-purple-400" />
                    <span className="text-sm">Fibonacci Levels (Purple)</span>
                  </div>
                </div>
              </div>

              <div className="pt-2 border-t">
                <p className="text-xs text-muted-foreground">
                  ✓ <span className="font-semibold">Showing last 10 Order Blocks, 5 FVG zones, and 8 Liquidity Sweeps</span>
                  <br />
                  💡 Toggle patterns on/off using the "Patterns" button above. Hover over markers for details.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
