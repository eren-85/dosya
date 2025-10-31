import React, { useEffect, useRef, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  Chip,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import { createChart, IChartApi, ISeriesApi, LineStyle, Time } from 'lightweight-charts';
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

  // Store overlay series for cleanup
  const overlaySeriesRef = useRef<ISeriesApi<any>[]>([]);

  const [overlays, setOverlays] = useState<ChartOverlay>({
    killZones: true,
    orderBlocks: true,
    fvg: true,
    harmonicPatterns: false,
    divergences: false,
    supportResistance: true,
    trendLines: false,
    fibonacci: true,
    swingPoints: true,
  });

  const [analysisData, setAnalysisData] = useState<any>(null);
  const [candleData, setCandleData] = useState<any[]>([]);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1H');
  const [marketType, setMarketType] = useState('futures');

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
        borderColor: '#cccccc',
      },
      rightPriceScale: {
        borderColor: '#cccccc',
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
  }, [selectedSymbol, selectedTimeframe, marketType]);

  useEffect(() => {
    if (chartRef.current && analysisData && candleData.length > 0) {
      // Clear previous overlays
      clearOverlays();
      // Redraw overlays when toggle changes
      drawAllOverlays();
    }
  }, [overlays, analysisData, candleData]);

  const clearOverlays = () => {
    // Remove all overlay series
    overlaySeriesRef.current.forEach(series => {
      try {
        chartRef.current?.removeSeries(series);
      } catch (e) {
        // Series already removed
      }
    });
    overlaySeriesRef.current = [];

    // Clear markers
    if (candlestickSeriesRef.current) {
      candlestickSeriesRef.current.setMarkers([]);
    }
  };

  const loadChartData = async () => {
    try {
      const BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

      // Fetch OHLCV data (limit=0 for ALL TIME data)
      const response = await axios.get(`${BASE}/api/data/ohlcv`, {
        params: {
          symbol: selectedSymbol,
          timeframe: selectedTimeframe,
          market_type: marketType,
          limit: 0, // 0 = all available candles
        },
      });

      // Backend returns {status: 'success', data: [...]}
      if (response.data.status === 'success' && response.data.data) {
        const candles = response.data.data.map((c: any) => ({
          time: c.time,
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));

        candlestickSeriesRef.current?.setData(candles);
        setCandleData(candles);

        // Generate analysis from candle data
        generateAnalysis(candles);
      }
    } catch (error) {
      console.error('Error loading chart data:', error);
    }
  };

  // RSI calculation helper
  const calculateRSI = (prices: number[], period: number = 14): number[] => {
    const rsi: number[] = [];
    if (prices.length < period + 1) return rsi;

    for (let i = 0; i < period; i++) {
      rsi.push(50); // Default neutral RSI for first period
    }

    let gains = 0;
    let losses = 0;

    // Calculate initial average gain/loss
    for (let i = 1; i <= period; i++) {
      const change = prices[i] - prices[i - 1];
      if (change > 0) gains += change;
      else losses += Math.abs(change);
    }

    let avgGain = gains / period;
    let avgLoss = losses / period;
    rsi.push(avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss)));

    // Calculate RSI for rest of data
    for (let i = period + 1; i < prices.length; i++) {
      const change = prices[i] - prices[i - 1];
      const gain = change > 0 ? change : 0;
      const loss = change < 0 ? Math.abs(change) : 0;

      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;

      rsi.push(avgLoss === 0 ? 100 : 100 - (100 / (1 + avgGain / avgLoss)));
    }

    return rsi;
  };

  const generateAnalysis = (candles: any[]) => {
    try {
      if (candles.length < 50) {
        setAnalysisData(null);
        return;
      }

      // For ALL TIME data, use only recent candles for analysis (last 2000)
      // This prevents performance issues and stack overflow
      const recentCandles = candles.length > 2000 ? candles.slice(-2000) : candles;

      // Calculate analysis from real candle data
      const prices = recentCandles.map(c => c.close);
      const highs = recentCandles.map(c => c.high);
      const lows = recentCandles.map(c => c.low);

      // Use reduce instead of spread operator to avoid stack overflow
      const maxPrice = prices.reduce((max, p) => Math.max(max, p), -Infinity);
      const minPrice = prices.reduce((min, p) => Math.min(min, p), Infinity);
      const priceRange = maxPrice - minPrice;

      // Find swing highs and lows (local maxima/minima)
      const swingHighs: any[] = [];
      const swingLows: any[] = [];
      const lookback = 10;

      for (let i = lookback; i < recentCandles.length - lookback; i++) {
        const isSwingHigh = highs.slice(i - lookback, i).every(h => h <= highs[i]) &&
                            highs.slice(i + 1, i + lookback + 1).every(h => h < highs[i]);

        const isSwingLow = lows.slice(i - lookback, i).every(l => l >= lows[i]) &&
                           lows.slice(i + 1, i + lookback + 1).every(l => l > lows[i]);

        if (isSwingHigh) {
          swingHighs.push({ index: i, price: highs[i], timestamp: recentCandles[i].time });
        }
        if (isSwingLow) {
          swingLows.push({ index: i, price: lows[i], timestamp: recentCandles[i].time });
        }
      }

      // Calculate Fibonacci levels from recent swing high/low
      const recentSwingHigh = swingHighs.length > 0 ? swingHighs[swingHighs.length - 1] : { price: maxPrice };
      const recentSwingLow = swingLows.length > 0 ? swingLows[swingLows.length - 1] : { price: minPrice };

      const fibHigh = Math.max(recentSwingHigh.price, recentSwingLow.price);
      const fibLow = Math.min(recentSwingHigh.price, recentSwingLow.price);
      const fibRange = fibHigh - fibLow;

      // Calculate support/resistance levels (price levels with multiple touches)
      const supportResistance: any[] = [];
      const priceRounded = prices.map(p => Math.round(p / (priceRange * 0.01)) * (priceRange * 0.01));
      const priceCounts: { [key: number]: number } = {};

      priceRounded.forEach(p => {
        priceCounts[p] = (priceCounts[p] || 0) + 1;
      });

      Object.entries(priceCounts)
        .filter(([_, count]) => count >= 5)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 5)
        .forEach(([price, count]) => {
          const currentPrice = prices[prices.length - 1];
          supportResistance.push({
            level: parseFloat(price),
            type: parseFloat(price) < currentPrice ? 'support' : 'resistance',
            strength: Math.min(count / 5, 5)
          });
        });

      // Detect order blocks (strong bullish/bearish candles)
      const orderBlocks: any[] = [];
      for (let i = 1; i < recentCandles.length; i++) {
        const candle = recentCandles[i];
        const prevCandle = recentCandles[i - 1];
        const bodySize = Math.abs(candle.close - candle.open);
        const prevBodySize = Math.abs(prevCandle.close - prevCandle.open);

        // Strong bullish candle after bearish
        if (bodySize > prevBodySize * 2 && candle.close > candle.open && prevCandle.close < prevCandle.open) {
          orderBlocks.push({
            high: candle.high,
            low: candle.low,
            type: 'bullish',
            timestamp: candle.time
          });
        }

        // Strong bearish candle after bullish
        if (bodySize > prevBodySize * 2 && candle.close < candle.open && prevCandle.close > prevCandle.open) {
          orderBlocks.push({
            high: candle.high,
            low: candle.low,
            type: 'bearish',
            timestamp: candle.time
          });
        }
      }

      // Detect Fair Value Gaps (FVG) - 3-candle pattern with gap
      // FVG occurs when middle candle's wick doesn't overlap with candle 1 and 3
      const fvg: any[] = [];
      for (let i = 2; i < recentCandles.length; i++) {
        const candle1 = recentCandles[i - 2];
        const candle2 = recentCandles[i - 1];
        const candle3 = recentCandles[i];

      // Bullish FVG: gap above (candle1 high < candle3 low)
      // Strong buying pressure, price jumped up leaving a gap
      if (candle1.high < candle3.low && candle2.low < candle3.low) {
        const gapStart = candle1.high;
        const gapEnd = candle3.low;
        if ((gapEnd - gapStart) / gapStart > 0.001) { // At least 0.1% gap
          fvg.push({
            start: gapStart,
            end: gapEnd,
            type: 'bullish',
            timestamp: candle2.time,
            endTime: candle3.time
          });
        }
      }

      // Bearish FVG: gap below (candle1 low > candle3 high)
      // Strong selling pressure, price dropped leaving a gap
      if (candle1.low > candle3.high && candle2.high > candle3.high) {
        const gapStart = candle3.high;
        const gapEnd = candle1.low;
        if ((gapEnd - gapStart) / gapStart > 0.001) {
          fvg.push({
            start: gapStart,
            end: gapEnd,
            type: 'bearish',
            timestamp: candle2.time,
            endTime: candle3.time
          });
        }
      }
      }

      // Detect Trend Lines (connect swing highs and lows)
      const trendLines: any[] = [];
      if (swingHighs.length >= 2) {
        // Downtrend line from recent 2 swing highs
        const sh1 = swingHighs[swingHighs.length - 2];
        const sh2 = swingHighs[swingHighs.length - 1];
        trendLines.push({
          type: 'resistance',
          point1: { time: sh1.timestamp, price: sh1.price },
          point2: { time: sh2.timestamp, price: sh2.price }
        });
      }
      if (swingLows.length >= 2) {
        // Uptrend line from recent 2 swing lows
        const sl1 = swingLows[swingLows.length - 2];
        const sl2 = swingLows[swingLows.length - 1];
        trendLines.push({
          type: 'support',
          point1: { time: sl1.timestamp, price: sl1.price },
          point2: { time: sl2.timestamp, price: sl2.price }
        });
      }

      // Calculate RSI for divergence detection
      const rsi = calculateRSI(prices, 14);

      // Detect RSI Divergences
      const divergences: any[] = [];
      // Bullish divergence: Price makes lower low, RSI makes higher low
      for (let i = 1; i < swingLows.length; i++) {
        const prevLow = swingLows[i - 1];
        const currLow = swingLows[i];
        const prevRSI = rsi[prevLow.index];
        const currRSI = rsi[currLow.index];

        if (currLow.price < prevLow.price && currRSI > prevRSI) {
          divergences.push({
            type: 'bullish',
            point1: { time: prevLow.timestamp, price: prevLow.price },
            point2: { time: currLow.timestamp, price: currLow.price },
            rsi1: prevRSI,
            rsi2: currRSI
          });
        }
      }

      // Bearish divergence: Price makes higher high, RSI makes lower high
      for (let i = 1; i < swingHighs.length; i++) {
        const prevHigh = swingHighs[i - 1];
        const currHigh = swingHighs[i];
        const prevRSI = rsi[prevHigh.index];
        const currRSI = rsi[currHigh.index];

        if (currHigh.price > prevHigh.price && currRSI < prevRSI) {
          divergences.push({
            type: 'bearish',
            point1: { time: prevHigh.timestamp, price: prevHigh.price },
            point2: { time: currHigh.timestamp, price: currHigh.price },
            rsi1: prevRSI,
            rsi2: currRSI
          });
        }
      }

      // Detect Harmonic Patterns (simplified Gartley, Bat, Butterfly)
      // Limit to last 20 swing points for performance
      const harmonicPatterns: any[] = [];
      const recentSwingHighs = swingHighs.slice(-20);
      const recentSwingLows = swingLows.slice(-20);

      if (recentSwingHighs.length >= 2 && recentSwingLows.length >= 2) {
        // Find XABCD pattern - only check last few swing points
        for (let i = 0; i < Math.min(recentSwingLows.length - 1, 10); i++) {
          const X = recentSwingLows[i];
          for (let j = i + 1; j < Math.min(recentSwingHighs.length, i + 10); j++) {
            const A = recentSwingHighs[j];
            if (A.index <= X.index) continue;

            for (let k = j + 1; k < Math.min(recentSwingLows.length, j + 10); k++) {
              const B = recentSwingLows[k];
              if (B.index <= A.index) continue;

              for (let l = k + 1; l < Math.min(recentSwingHighs.length, k + 10); l++) {
                const C = recentSwingHighs[l];
                if (C.index <= B.index) continue;

                for (let m = l + 1; m < Math.min(recentSwingLows.length, l + 10); m++) {
                  const D = recentSwingLows[m];
                  if (D.index <= C.index) continue;

                // Calculate Fibonacci ratios
                const XA = A.price - X.price;
                const AB = A.price - B.price;
                const BC = C.price - B.price;
                const CD = C.price - D.price;
                const XD = D.price - X.price;

                const AB_XA = AB / XA;
                const BC_AB = BC / AB;
                const CD_BC = CD / BC;
                const XD_XA = XD / XA;

                // Gartley: AB=0.618 XA, BC=0.382-0.886 AB, CD=1.272-1.618 BC, XD=0.786 XA
                if (Math.abs(AB_XA - 0.618) < 0.1 && BC_AB >= 0.382 && BC_AB <= 0.886 &&
                    CD_BC >= 1.272 && CD_BC <= 1.618 && Math.abs(XD_XA - 0.786) < 0.1) {
                  harmonicPatterns.push({
                    type: 'Gartley',
                    points: { X, A, B, C, D },
                    bullish: D.price < X.price
                  });
                }

                // Bat: AB=0.382-0.5 XA, BC=0.382-0.886 AB, CD=1.618-2.618 BC, XD=0.886 XA
                if (AB_XA >= 0.382 && AB_XA <= 0.5 && BC_AB >= 0.382 && BC_AB <= 0.886 &&
                    CD_BC >= 1.618 && CD_BC <= 2.618 && Math.abs(XD_XA - 0.886) < 0.1) {
                  harmonicPatterns.push({
                    type: 'Bat',
                    points: { X, A, B, C, D },
                    bullish: D.price < X.price
                  });
                }

                // Butterfly: AB=0.786 XA, BC=0.382-0.886 AB, CD=1.618-2.24 BC, XD=1.272-1.618 XA
                if (Math.abs(AB_XA - 0.786) < 0.1 && BC_AB >= 0.382 && BC_AB <= 0.886 &&
                    CD_BC >= 1.618 && CD_BC <= 2.24 && XD_XA >= 1.272 && XD_XA <= 1.618) {
                  harmonicPatterns.push({
                    type: 'Butterfly',
                    points: { X, A, B, C, D },
                    bullish: D.price < X.price
                  });
                }

                // Only check first few patterns to avoid performance issues
                if (harmonicPatterns.length >= 3) break;
              }
              if (harmonicPatterns.length >= 3) break;
            }
            if (harmonicPatterns.length >= 3) break;
          }
          if (harmonicPatterns.length >= 3) break;
        }
        if (harmonicPatterns.length >= 3) break;
      }
    }

      setAnalysisData({
        swing_highs: swingHighs,
        swing_lows: swingLows,
        fibonacci: {
          swing_high: fibHigh,
          swing_low: fibLow,
          level_236: fibLow + fibRange * 0.236,
          level_382: fibLow + fibRange * 0.382,
          level_500: fibLow + fibRange * 0.500,
          level_618: fibLow + fibRange * 0.618,
          level_786: fibLow + fibRange * 0.786,
          golden_zone_low: fibLow + fibRange * 0.618,
          golden_zone_high: fibLow + fibRange * 0.66,
          ote_low: fibLow + fibRange * 0.295,
          ote_high: fibLow + fibRange * 0.705,
        },
        support_resistance: supportResistance,
        order_blocks: orderBlocks.slice(-10), // Last 10
        fvg: fvg.slice(-10), // Last 10
        trend_lines: trendLines,
        divergences: divergences.slice(-5), // Last 5
        harmonic_patterns: harmonicPatterns.slice(0, 3), // First 3
      });
    } catch (error) {
      console.error('Error generating analysis:', error);
      setAnalysisData(null);
    }
  };

  const drawAllOverlays = () => {
    if (!chartRef.current || !analysisData || candleData.length === 0) return;

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

    // Draw Trend Lines
    if (overlays.trendLines && analysisData.trend_lines) {
      drawTrendLines();
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

    // Draw Divergences
    if (overlays.divergences && analysisData.divergences) {
      drawDivergences();
    }

    // Draw Harmonic Patterns
    if (overlays.harmonicPatterns && analysisData.harmonic_patterns) {
      drawHarmonicPatterns();
    }
  };

  const drawKillZones = () => {
    if (!chartRef.current || candleData.length === 0) return;

    // Kill Zones: Mark session starts with vertical markers
    // London: 02:00-05:00 UTC, NY: 13:00-16:00 UTC, Asia: 20:00-02:00 UTC
    const markers: any[] = [];

    // Only mark if overlays.killZones is on AND overlays.swingPoints is off
    // (to avoid marker conflicts)
    if (!overlays.swingPoints) {
      candleData.forEach((candle, idx) => {
        const date = new Date(candle.time * 1000);
        const hour = date.getUTCHours();

        // Mark start of each session
        if (hour === 2) { // London open
          markers.push({
            time: candle.time,
            position: 'aboveBar',
            color: '#2196F3',
            shape: 'square',
            text: '🇬🇧 LON',
            size: 1
          });
        } else if (hour === 13) { // NY open
          markers.push({
            time: candle.time,
            position: 'aboveBar',
            color: '#4CAF50',
            shape: 'square',
            text: '🇺🇸 NY',
            size: 1
          });
        } else if (hour === 20) { // Asia open
          markers.push({
            time: candle.time,
            position: 'aboveBar',
            color: '#FF9800',
            shape: 'square',
            text: '🌏 ASIA',
            size: 1
          });
        }
      });

      if (markers.length > 0 && candlestickSeriesRef.current) {
        candlestickSeriesRef.current.setMarkers(markers);
      }
    }
  };

  const drawTrendLines = () => {
    if (!chartRef.current || !analysisData.trend_lines || candleData.length === 0) return;

    analysisData.trend_lines.forEach((tl: any) => {
      // Calculate slope to extend line
      const time1 = tl.point1.time;
      const time2 = tl.point2.time;
      const price1 = tl.point1.price;
      const price2 = tl.point2.price;

      const slope = (price2 - price1) / (time2 - time1);

      // Extend line forward
      const lastTime = candleData[candleData.length - 1].time;
      const extendedPrice = price2 + slope * (lastTime - time2);

      const lineSeries = chartRef.current!.addLineSeries({
        color: tl.type === 'support' ? '#00BFA6' : '#FF6B6B',
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      lineSeries.setData([
        { time: time1 as Time, value: price1 },
        { time: time2 as Time, value: price2 },
        { time: lastTime as Time, value: extendedPrice },
      ]);

      overlaySeriesRef.current.push(lineSeries);
    });
  };

  const drawFibonacci = () => {
    if (!chartRef.current || !analysisData.fibonacci || candleData.length === 0) return;

    const fib = analysisData.fibonacci;
    const firstTime = candleData[0].time;
    const lastTime = candleData[candleData.length - 1].time;

    const levels = [
      { price: fib.swing_high, label: '1.0 (100%)', color: '#E91E63', width: 3 }, // 0 line (swing high)
      { price: fib.level_786, label: '0.786 (78.6%)', color: '#9C27B0', width: 1 },
      { price: fib.ote_high, label: '0.705 OTE High', color: '#4CAF50', width: 2 },
      { price: fib.golden_zone_high, label: '0.66 GZ High', color: '#FFC107', width: 2 },
      { price: fib.level_618, label: '0.618 (61.8%)', color: '#FF9800', width: 2 },
      { price: fib.golden_zone_low, label: '0.618 GZ Low', color: '#FFC107', width: 2 },
      { price: fib.level_500, label: '0.5 (50%)', color: '#2196F3', width: 3 }, // Equilibrium
      { price: fib.level_382, label: '0.382 (38.2%)', color: '#FF9800', width: 2 },
      { price: fib.ote_low, label: '0.295 OTE Low', color: '#4CAF50', width: 2 },
      { price: fib.level_236, label: '0.236 (23.6%)', color: '#9C27B0', width: 1 },
      { price: fib.swing_low, label: '0.0 (0%)', color: '#E91E63', width: 3 }, // 1 line (swing low)
    ];

    levels.forEach((level) => {
      if (level.price && level.price > 0) {
        const lineSeries = chartRef.current!.addLineSeries({
          color: level.color,
          lineWidth: level.width,
          lineStyle: level.width === 3 ? LineStyle.Solid : level.width === 2 ? LineStyle.Solid : LineStyle.Dashed,
          priceLineVisible: true,
          lastValueVisible: true,
          title: level.label, // Show label on price scale
        });

        lineSeries.setData([
          { time: firstTime as Time, value: level.price },
          { time: lastTime as Time, value: level.price },
        ]);

        overlaySeriesRef.current.push(lineSeries);
      }
    });
  };

  const drawSupportResistance = () => {
    if (!chartRef.current || !analysisData.support_resistance || candleData.length === 0) return;

    const firstTime = candleData[0].time;
    const lastTime = candleData[candleData.length - 1].time;

    analysisData.support_resistance.forEach((sr: any) => {
      const lineSeries = chartRef.current!.addLineSeries({
        color: sr.type === 'support' ? '#00BFA6' : '#FF6B6B',
        lineWidth: Math.min(sr.strength, 3),
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      lineSeries.setData([
        { time: firstTime as Time, value: sr.level },
        { time: lastTime as Time, value: sr.level },
      ]);

      overlaySeriesRef.current.push(lineSeries);
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

    // Sort markers by time
    markers.sort((a, b) => a.time - b.time);

    if (candlestickSeriesRef.current && markers.length > 0 && !overlays.killZones) {
      candlestickSeriesRef.current.setMarkers(markers);
    }
  };

  const drawOrderBlocks = () => {
    if (!chartRef.current || !analysisData.order_blocks || candleData.length === 0) return;

    // Draw order blocks as filled areas (approximated with line series)
    analysisData.order_blocks.forEach((ob: any) => {
      // Find candle at this timestamp
      const startIdx = candleData.findIndex(c => c.time >= ob.timestamp);
      if (startIdx === -1) return;

      const endIdx = Math.min(startIdx + 10, candleData.length - 1);

      // Draw top line
      const topLine = chartRef.current!.addLineSeries({
        color: ob.type === 'bullish' ? 'rgba(0, 191, 166, 0.6)' : 'rgba(255, 107, 107, 0.6)',
        lineWidth: 3,
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      topLine.setData([
        { time: candleData[startIdx].time as Time, value: ob.high },
        { time: candleData[endIdx].time as Time, value: ob.high },
      ]);

      // Draw bottom line
      const bottomLine = chartRef.current!.addLineSeries({
        color: ob.type === 'bullish' ? 'rgba(0, 191, 166, 0.6)' : 'rgba(255, 107, 107, 0.6)',
        lineWidth: 3,
        lineStyle: LineStyle.Solid,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      bottomLine.setData([
        { time: candleData[startIdx].time as Time, value: ob.low },
        { time: candleData[endIdx].time as Time, value: ob.low },
      ]);

      overlaySeriesRef.current.push(topLine, bottomLine);
    });
  };

  const drawFVG = () => {
    if (!chartRef.current || !analysisData.fvg || candleData.length === 0) return;

    // Draw FVG as shaded zones (approximated with line series)
    analysisData.fvg.forEach((gap: any) => {
      const startIdx = candleData.findIndex(c => c.time >= gap.timestamp);
      if (startIdx === -1) return;

      const endIdx = Math.min(startIdx + 10, candleData.length - 1);

      // Draw gap boundaries
      const topLine = chartRef.current!.addLineSeries({
        color: gap.type === 'bullish' ? 'rgba(76, 175, 80, 0.4)' : 'rgba(244, 67, 54, 0.4)',
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      topLine.setData([
        { time: candleData[startIdx].time as Time, value: gap.end },
        { time: candleData[endIdx].time as Time, value: gap.end },
      ]);

      const bottomLine = chartRef.current!.addLineSeries({
        color: gap.type === 'bullish' ? 'rgba(76, 175, 80, 0.4)' : 'rgba(244, 67, 54, 0.4)',
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      bottomLine.setData([
        { time: candleData[startIdx].time as Time, value: gap.start },
        { time: candleData[endIdx].time as Time, value: gap.start },
      ]);

      overlaySeriesRef.current.push(topLine, bottomLine);
    });
  };

  const drawDivergences = () => {
    if (!chartRef.current || !analysisData.divergences || candleData.length === 0) return;

    analysisData.divergences.forEach((div: any) => {
      const lineSeries = chartRef.current!.addLineSeries({
        color: div.type === 'bullish' ? '#4CAF50' : '#F44336',
        lineWidth: 2,
        lineStyle: LineStyle.Dashed,
        priceLineVisible: false,
        lastValueVisible: false,
      });

      lineSeries.setData([
        { time: div.point1.time as Time, value: div.point1.price },
        { time: div.point2.time as Time, value: div.point2.price },
      ]);

      overlaySeriesRef.current.push(lineSeries);
    });
  };

  const drawHarmonicPatterns = () => {
    if (!chartRef.current || !analysisData.harmonic_patterns || candleData.length === 0) return;

    analysisData.harmonic_patterns.forEach((pattern: any) => {
      const { X, A, B, C, D } = pattern.points;
      const color = pattern.bullish ? '#4CAF50' : '#F44336';

      // Draw XABCD lines
      const lines = [
        [X, A],
        [A, B],
        [B, C],
        [C, D]
      ];

      lines.forEach(([p1, p2]) => {
        const lineSeries = chartRef.current!.addLineSeries({
          color,
          lineWidth: 2,
          lineStyle: LineStyle.Solid,
          priceLineVisible: false,
          lastValueVisible: false,
        });

        lineSeries.setData([
          { time: p1.timestamp as Time, value: p1.price },
          { time: p2.timestamp as Time, value: p2.price },
        ]);

        overlaySeriesRef.current.push(lineSeries);
      });

      // Add markers for pattern points
      const markers = [
        { time: X.timestamp, position: 'belowBar' as const, color, shape: 'circle' as const, text: `${pattern.type} X` },
        { time: A.timestamp, position: 'aboveBar' as const, color, shape: 'circle' as const, text: 'A' },
        { time: B.timestamp, position: 'belowBar' as const, color, shape: 'circle' as const, text: 'B' },
        { time: C.timestamp, position: 'aboveBar' as const, color, shape: 'circle' as const, text: 'C' },
        { time: D.timestamp, position: 'belowBar' as const, color, shape: 'circle' as const, text: 'D' },
      ];

      if (candlestickSeriesRef.current) {
        candlestickSeriesRef.current.setMarkers(markers);
      }
    });
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
                Real-time pattern detection with Smart Money Concepts. Toggle overlays below.
              </Typography>

              {/* Symbol and Timeframe Selectors */}
              <Box sx={{ mt: 2, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
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
                  <InputLabel>Market</InputLabel>
                  <Select
                    value={marketType}
                    label="Market"
                    onChange={(e: SelectChangeEvent) => setMarketType(e.target.value)}
                  >
                    <MenuItem value="futures">Futures</MenuItem>
                    <MenuItem value="spot">Spot</MenuItem>
                  </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 130 }}>
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
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    Fibonacci Levels:
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🟡 <strong>Golden Zone:</strong> 0.618 - 0.66 (High probability reversal)</Typography>
                    <Typography variant="body2">🟢 <strong>OTE:</strong> 0.295 - 0.705 (Optimal Trade Entry)</Typography>
                    <Typography variant="body2">🔵 <strong>50% Level:</strong> Equilibrium (blue, thick line)</Typography>
                    <Typography variant="body2">⚪ <strong>Other Levels:</strong> 23.6%, 38.2%, 61.8%, 78.6%</Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    Kill Zones (UTC):
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🟦 <strong>London:</strong> 02:00 - 05:00</Typography>
                    <Typography variant="body2">🟦 <strong>New York:</strong> 13:00 - 16:00</Typography>
                    <Typography variant="body2">🟦 <strong>Asia:</strong> 20:00 - 02:00</Typography>
                    <Typography variant="caption" color="text.secondary">High liquidity periods</Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    Smart Money Concepts:
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🟩 <strong>Bullish Order Blocks:</strong> Strong buying zones</Typography>
                    <Typography variant="body2">🟥 <strong>Bearish Order Blocks:</strong> Strong selling zones</Typography>
                    <Typography variant="body2">📦 <strong>Fair Value Gaps (FVG):</strong> Imbalance areas likely to fill</Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    Patterns:
                  </Typography>
                  <Box sx={{ pl: 2 }}>
                    <Typography variant="body2">🔻 <strong>Swing Highs (SH):</strong> Local price peaks</Typography>
                    <Typography variant="body2">🔺 <strong>Swing Lows (SL):</strong> Local price troughs</Typography>
                    <Typography variant="body2">➖ <strong>Support/Resistance:</strong> Key price levels</Typography>
                  </Box>
                </Grid>
              </Grid>

              <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  💡 <strong>Tip:</strong> Click overlay chips to toggle them on/off. Analysis is generated from real candle data.
                  All patterns are detected automatically using technical analysis algorithms.
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdvancedChart;
