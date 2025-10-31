import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi } from 'lightweight-charts';
import { Box } from '@mui/material';

interface Props {
  symbol: string;
  interval: string;
  marketType?: string; // 'futures' or 'spot'
}

const TradingViewChart: React.FC<Props> = ({ symbol, interval, marketType = 'futures' }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
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
      },
    });

    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#00BFA6',
      downColor: '#FF6B6B',
      borderVisible: false,
      wickUpColor: '#00BFA6',
      wickDownColor: '#FF6B6B',
    });

    // Fetch and set data
    fetchChartData(symbol, interval, marketType).then((data) => {
      candlestickSeries.setData(data);
    });

    chartRef.current = chart;

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [symbol, interval, marketType]);

  return <Box ref={chartContainerRef} sx={{ width: '100%', height: 500 }} />;
};

// Fetch real chart data from backend API
async function fetchChartData(symbol: string, interval: string, marketType: string = 'futures') {
  try {
    const BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";
    const response = await fetch(
      `${BASE}/api/data/ohlcv?symbol=${symbol}&timeframe=${interval}&market_type=${marketType}&limit=0`
    );

    if (!response.ok) {
      console.error('Failed to fetch chart data:', response.statusText);
      return [];
    }

    const result = await response.json();

    if (result.status === 'success' && result.data) {
      // Backend returns {time, open, high, low, close, volume}
      // lightweight-charts needs the same format
      return result.data;
    }

    return [];
  } catch (error) {
    console.error('Error fetching chart data:', error);
    return [];
  }
}

export default TradingViewChart;
