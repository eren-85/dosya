import React, { useEffect, useRef } from 'react';
import { createChart, IChartApi } from 'lightweight-charts';
import { Box } from '@mui/material';

interface Props {
  symbol: string;
  interval: string;
}

const TradingViewChart: React.FC<Props> = ({ symbol, interval }) => {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { color: '#151B3D' },
        textColor: '#DDD',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
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

    // Fetch and set data (placeholder)
    fetchChartData(symbol, interval).then((data) => {
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
  }, [symbol, interval]);

  return <Box ref={chartContainerRef} sx={{ width: '100%', height: 500 }} />;
};

// Placeholder data fetch
async function fetchChartData(symbol: string, interval: string) {
  // In production, fetch from backend API
  // For now, return dummy data
  return [
    { time: '2024-01-01', open: 65000, high: 67000, low: 64000, close: 66500 },
    { time: '2024-01-02', open: 66500, high: 68000, low: 66000, close: 67200 },
    // ... more data
  ];
}

export default TradingViewChart;
