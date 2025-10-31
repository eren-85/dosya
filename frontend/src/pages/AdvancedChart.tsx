import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Switch,
  FormControlLabel,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import { createChart, IChartApi, ISeriesApi, LineStyle } from 'lightweight-charts';
import axios from 'axios';

interface ChartOverlay {
  killZones: boolean;
  orderBlocks: boolean;
  fvg: boolean;
  harmonicPatterns: boolean;
  divergences: boolean;
  supportResistance: boolean;
  trendLines: boolean;
  fibonacci: boolean;
  swingPoints: boolean;
}

const AdvancedChart: React.FC = () => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candlestickSeriesRef = useRef<ISeriesApi<'Candlestick'> | null>(null);

  const [overlays, setOverlays] = useState<ChartOverlay>({
    killZones: true,
    orderBlocks: true,
    fvg: true,
    harmonicPatterns: true,
    divergences: true,
    supportResistance: true,
    trendLines: true,
    fibonacci: true,
    swingPoints: true,
  });

  const [analysisData, setAnalysisData] = useState<any>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1H');

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 700,
      layout: {
        background: { color: '#ffffff' },
        textColor: '#000000',
      },
      grid: {
        vertLines: { color: '#e0e0e0' },
        horzLines: { color: '#e0e0e0' },
      },
      crosshair: {
        mode: 1,
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
        borderColor: '#2B2B43',
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00BFA6',
      downColor: '#FF6B6B',
      borderVisible: false,
      wickUpColor: '#00BFA6',
      wickDownColor: '#FF6B6B',
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;

    // Load data
    loadChartData();

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [selectedSymbol, selectedTimeframe]);

  useEffect(() => {
    if (chartRef.current && analysisData) {
      // Redraw overlays when toggle changes
      drawAllOverlays();
    }
  }, [overlays, analysisData]);

  const loadChartData = async () => {
    try {
      const BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

      // Fetch OHLCV data
      const response = await axios.get(`${BASE}/api/data/ohlcv`, {
        params: {
          symbol: selectedSymbol,
          timeframe: selectedTimeframe,
          limit: 500,
        },
      });

      // Backend returns {status: 'success', data: [...]}
      if (response.data.status === 'success' && response.data.data) {
        const candles = response.data.data.map((c: any) => ({
          time: c.time, // Backend returns 'time', not 'timestamp'
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));

        candlestickSeriesRef.current?.setData(candles);
      }

      // TODO: Fetch advanced analysis from backend
      // For now, use mock analysis data
      loadMockAnalysis();
    } catch (error) {
      console.error('Error loading chart data:', error);
      // Use mock data for development
      loadMockData();
    }
  };

  const loadMockData = () => {
    // Deterministic mock candle data (seed-based for consistency)
    // Use symbol + timeframe as seed to ensure same data on refresh
    const seedStr = `${selectedSymbol}_${selectedTimeframe}`;
    let seed = 0;
    for (let i = 0; i < seedStr.length; i++) {
      seed = seed * 31 + seedStr.charCodeAt(i);
    }

    // Simple seeded random function
    const seededRandom = () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };

    const basePrice = selectedSymbol === 'BTCUSDT' ? 67000 :
                      selectedSymbol === 'ETHUSDT' ? 3500 :
                      selectedSymbol === 'BNBUSDT' ? 600 : 1000;

    const mockCandles = [];
    let price = basePrice;

    for (let i = 0; i < 500; i++) {
      const open = price;
      const changePercent = (seededRandom() - 0.5) * 0.04; // ±2%
      price = price * (1 + changePercent);

      const high = open * (1 + seededRandom() * 0.01); // up to +1%
      const low = open * (1 - seededRandom() * 0.01);  // up to -1%
      const close = low + seededRandom() * (high - low);

      mockCandles.push({
        time: Math.floor(Date.now() / 1000) - (500 - i) * 3600,
        open: Math.round(open * 100) / 100,
        high: Math.round(high * 100) / 100,
        low: Math.round(low * 100) / 100,
        close: Math.round(close * 100) / 100,
      });

      price = close;
    }

    candlestickSeriesRef.current?.setData(mockCandles);
    loadMockAnalysis();
  };

  const loadMockAnalysis = () => {
    // Mock analysis data
    setAnalysisData({
      swing_highs: [
        { index: 50, price: 68500, timestamp: Math.floor(Date.now() / 1000) - 150 * 3600 },
        { index: 120, price: 69200, timestamp: Math.floor(Date.now() / 1000) - 80 * 3600 },
      ],
      swing_lows: [
        { index: 30, price: 65500, timestamp: Math.floor(Date.now() / 1000) - 170 * 3600 },
        { index: 100, price: 66200, timestamp: Math.floor(Date.now() / 1000) - 100 * 3600 },
      ],
      fibonacci: {
        swing_high: 69200,
        swing_low: 65500,
        level_618: 67500,
        level_382: 66800,
        golden_zone_low: 67500,
        golden_zone_high: 67650,
        ote_high: 67800,
        ote_low: 66500,
      },
      support_resistance: [
        { level: 67000, type: 'support', strength: 3 },
        { level: 68500, type: 'resistance', strength: 4 },
      ],
      harmonic_patterns: [
        {
          name: 'Gartley',
          type: 'bullish',
          points: { X: 65000, A: 68000, B: 66500, C: 67500, D: 66000 },
        },
      ],
      order_blocks: [
        { price: 66800, type: 'bullish', timestamp: Math.floor(Date.now() / 1000) - 50 * 3600 },
      ],
      fvg: [
        { start: 67200, end: 67600, type: 'bullish', timestamp: Math.floor(Date.now() / 1000) - 30 * 3600 },
      ],
    });
  };

  const drawAllOverlays = () => {
    if (!chartRef.current || !analysisData) return;

    // Clear previous markers
    // Note: LightweightCharts doesn't have a built-in clear method
    // We would need to track and remove individual markers

    // Draw Kill Zones
    if (overlays.killZones) {
      drawKillZones();
    }

    // Draw Fibonacci
    if (overlays.fibonacci && analysisData.fibonacci) {
      drawFibonacci();
    }

    // Draw Support/Resistance
    if (overlays.supportResistance && analysisData.support_resistance) {
      drawSupportResistance();
    }

    // Draw Swing Points
    if (overlays.swingPoints) {
      drawSwingPoints();
    }

    // Draw Order Blocks
    if (overlays.orderBlocks && analysisData.order_blocks) {
      drawOrderBlocks();
    }

    // Draw FVG
    if (overlays.fvg && analysisData.fvg) {
      drawFVG();
    }
  };

  const drawKillZones = () => {
    if (!chartRef.current) return;

    // London Kill Zone: 02:00-05:00 UTC (background shading)
    // New York Kill Zone: 13:00-16:00 UTC
    // Asia Kill Zone: 20:00-02:00 UTC

    // Note: LightweightCharts doesn't support time-based backgrounds directly
    // This would require custom rendering or using price series with null values
    console.log('Kill Zones would be drawn here');
  };

  const drawFibonacci = () => {
    if (!chartRef.current || !analysisData.fibonacci) return;

    const fib = analysisData.fibonacci;

    // Draw Fibonacci levels as horizontal lines
    const levels = [
      { price: fib.level_0, label: '0.0%', color: '#888' },
      { price: fib.level_236, label: '23.6%', color: '#888' },
      { price: fib.level_382, label: '38.2%', color: '#FFA726' },
      { price: fib.golden_zone_382_low, label: 'GZ 382 Low', color: '#FFD700' },
      { price: fib.golden_zone_382_high, label: 'GZ 382 High', color: '#FFD700' },
      { price: fib.ote_low, label: 'OTE Low (0.295)', color: '#00E676' },
      { price: fib.level_500, label: '50.0%', color: '#888' },
      { price: fib.level_618, label: '61.8%', color: '#FFA726' },
      { price: fib.golden_zone_low, label: 'GZ 618 Low', color: '#FFD700' },
      { price: fib.golden_zone_high, label: 'GZ 618 High', color: '#FFD700' },
      { price: fib.ote_high, label: 'OTE High (0.705)', color: '#00E676' },
      { price: fib.level_786, label: '78.6%', color: '#888' },
      { price: fib.level_1000, label: '100.0%', color: '#888' },
    ];

    levels.forEach((level) => {
      const lineSeries = chartRef.current!.addLineSeries({
        color: level.color,
        lineWidth: level.label.includes('GZ') ? 2 : (level.label.includes('OTE') ? 2 : 1),
        lineStyle: level.label.includes('GZ') || level.label.includes('OTE') ? LineStyle.Solid : LineStyle.Dashed,
        priceLineVisible: false,
      });

      lineSeries.setData([
        { time: Date.now() / 1000 - 200 * 3600, value: level.price },
        { time: Date.now() / 1000, value: level.price },
      ]);
    });
  };

  const drawSupportResistance = () => {
    if (!chartRef.current || !analysisData.support_resistance) return;

    analysisData.support_resistance.forEach((sr: any) => {
      const lineSeries = chartRef.current!.addLineSeries({
        color: sr.type === 'support' ? '#00BFA6' : '#FF6B6B',
        lineWidth: Math.min(sr.strength, 3),
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
      });

      lineSeries.setData([
        { time: Date.now() / 1000 - 200 * 3600, value: sr.level },
        { time: Date.now() / 1000, value: sr.level },
      ]);
    });
  };

  const drawSwingPoints = () => {
    if (!chartRef.current || !analysisData.swing_highs || !analysisData.swing_lows) return;

    const markers: any[] = [];

    // Swing Highs
    analysisData.swing_highs.forEach((sh: any) => {
      markers.push({
        time: sh.timestamp,
        position: 'aboveBar',
        color: '#FF6B6B',
        shape: 'arrowDown',
        text: 'SH',
      });
    });

    // Swing Lows
    analysisData.swing_lows.forEach((sl: any) => {
      markers.push({
        time: sl.timestamp,
        position: 'belowBar',
        color: '#00BFA6',
        shape: 'arrowUp',
        text: 'SL',
      });
    });

    // Sort markers by time (REQUIRED by lightweight-charts)
    markers.sort((a, b) => a.time - b.time);

    candlestickSeriesRef.current?.setMarkers(markers);
  };

  const drawOrderBlocks = () => {
    console.log('Order Blocks would be drawn as rectangles');
    // LightweightCharts doesn't support rectangles natively
    // Would require custom drawing or using background series
  };

  const drawFVG = () => {
    console.log('Fair Value Gaps would be drawn as shaded zones');
    // Similar to order blocks, would need custom rendering
  };

  const toggleOverlay = (key: keyof ChartOverlay) => {
    setOverlays((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Chart Controls */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h5" gutterBottom>
                Advanced Technical Analysis Chart
              </Typography>

              <Typography variant="body2" color="text.secondary" gutterBottom>
                This chart shows all detected patterns, levels, and zones. Toggle overlays below.
              </Typography>

              {/* Symbol and Timeframe Selectors */}
              <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Symbol</InputLabel>
                  <Select
                    value={selectedSymbol}
                    label="Symbol"
                    onChange={(e: SelectChangeEvent) => setSelectedSymbol(e.target.value)}
                  >
                    <MenuItem value="BTCUSDT">BTC/USDT</MenuItem>
                    <MenuItem value="ETHUSDT">ETH/USDT</MenuItem>
                    <MenuItem value="BNBUSDT">BNB/USDT</MenuItem>
                    <MenuItem value="SOLUSDT">SOL/USDT</MenuItem>
                    <MenuItem value="XRPUSDT">XRP/USDT</MenuItem>
                  </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Timeframe</InputLabel>
                  <Select
                    value={selectedTimeframe}
                    label="Timeframe"
                    onChange={(e: SelectChangeEvent) => setSelectedTimeframe(e.target.value)}
                  >
                    <MenuItem value="5m">5 Minutes</MenuItem>
                    <MenuItem value="15m">15 Minutes</MenuItem>
                    <MenuItem value="30m">30 Minutes</MenuItem>
                    <MenuItem value="1H">1 Hour</MenuItem>
                    <MenuItem value="4H">4 Hours</MenuItem>
                    <MenuItem value="1D">1 Day</MenuItem>
                  </Select>
                </FormControl>

                <Button variant="outlined" onClick={loadChartData}>
                  Refresh Data
                </Button>
              </Box>

              {/* Overlay Toggles */}
              <Box sx={{ mt: 2, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Typography variant="body2" sx={{ width: '100%', mb: 1, fontWeight: 500 }}>
                  Overlays:
                </Typography>
                {Object.entries(overlays).map(([key, value]) => (
                  <Chip
                    key={key}
                    label={key.replace(/([A-Z])/g, ' $1').trim()}
                    color={value ? 'primary' : 'default'}
                    onClick={() => toggleOverlay(key as keyof ChartOverlay)}
                    sx={{ textTransform: 'capitalize' }}
                  />
                ))}
              </Box>

              <Box sx={{ mt: 2 }}>
                <Button variant="outlined" onClick={() => alert('Manual annotation mode (coming soon)')}>
                  Manual Annotation Mode
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Chart */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box ref={chartContainerRef} sx={{ width: '100%', height: 700 }} />
            </CardContent>
          </Card>
        </Grid>

        {/* Legend */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Legend
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Fibonacci Levels:</Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">
                      🟡 <strong>Golden Zone 618:</strong> 0.618 - 0.66 (High probability reversal)
                    </Typography>
                    <Typography variant="body2">
                      🟡 <strong>Golden Zone 382:</strong> 0.34 - 0.382
                    </Typography>
                    <Typography variant="body2">
                      🟢 <strong>OTE High:</strong> 0.705 (Optimal Trade Entry)
                    </Typography>
                    <Typography variant="body2">
                      🟢 <strong>OTE Low:</strong> 0.295
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Kill Zones (UTC):</Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🟦 London: 02:00 - 05:00</Typography>
                    <Typography variant="body2">🟦 New York: 13:00 - 16:00</Typography>
                    <Typography variant="body2">🟦 Asia: 20:00 - 02:00</Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Patterns:</Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">📐 Harmonic Patterns (Gartley, Bat, Butterfly, Crab)</Typography>
                    <Typography variant="body2">📊 Divergences (RSI, MACD, Volume)</Typography>
                    <Typography variant="body2">🔺 Swing Highs/Lows</Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2">Smart Money Concepts:</Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🟩 Bullish Order Blocks</Typography>
                    <Typography variant="body2">🟥 Bearish Order Blocks</Typography>
                    <Typography variant="body2">⬜ Fair Value Gaps (FVG)</Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdvancedChart;
