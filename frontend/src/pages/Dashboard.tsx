import React, { useEffect, useState } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import TradingViewChart from '../components/charts/TradingViewChart';
import MarketPulse from '../components/widgets/MarketPulse';
import ScenarioCard from '../components/widgets/ScenarioCard';
import FlowWidget from '../components/widgets/FlowWidget';
import AlertsList from '../components/widgets/AlertsList';
import { useWebSocket } from '../hooks/useWebSocket';

const Dashboard: React.FC = () => {
  // WebSocket disabled for now - use REST API endpoints instead
  const { alerts, isConnected } = useWebSocket(); // No URL = disabled

  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1H');
  const [marketType, setMarketType] = useState('futures'); // 'futures' or 'spot'

  // Market data - fetch from backend
  const [marketData, setMarketData] = useState<any>({
    symbol: 'BTCUSDT',
    btc_price: 0,
    change_24h: 0,
    sentiment: 'neutral',
    confidence: 0.5,
    volatility_regime: 'Loading...',
    funding_rate: 0,
    key_observation: 'Loading market data...'
  });

  // Flow data - fetch from backend
  const [flowData, setFlowData] = useState<any>({
    exchange_netflow: 0,
    miner_reserve_change: 0,
    whale_transactions: 0,
    stablecoin_supply_ratio: 0,
    liquidations_24h: { longs: 0, shorts: 0 }
  });

  const [scenarios, setScenarios] = useState<any[]>([]);

  // Fetch live market data
  useEffect(() => {
    fetchMarketData();
    const interval = setInterval(fetchMarketData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [symbol, marketType]);

  const fetchMarketData = async () => {
    try {
      const BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

      // Fetch current price from Binance
      const binanceUrl = marketType === 'futures'
        ? 'https://fapi.binance.com/fapi/v1/ticker/24hr'
        : 'https://api.binance.com/api/v3/ticker/24hr';

      const response = await fetch(`${binanceUrl}?symbol=${symbol}`);
      const data = await response.json();

      const currentPrice = parseFloat(data.lastPrice);
      const change24h = parseFloat(data.priceChangePercent);
      const volume = parseFloat(data.volume);

      // Simple sentiment based on price change
      const sentiment = change24h > 2 ? 'bullish' : change24h < -2 ? 'bearish' : 'neutral';
      const confidence = Math.min(Math.abs(change24h) / 5, 1);

      // Get funding rate for futures
      let fundingRate = 0;
      if (marketType === 'futures') {
        try {
          const fundingResp = await fetch(`https://fapi.binance.com/fapi/v1/fundingRate?symbol=${symbol}&limit=1`);
          const fundingData = await fundingResp.json();
          if (fundingData.length > 0) {
            fundingRate = parseFloat(fundingData[0].fundingRate);
          }
        } catch (e) {
          console.error('Failed to fetch funding rate:', e);
        }
      }

      setMarketData({
        symbol,
        btc_price: currentPrice,
        change_24h: change24h,
        sentiment,
        confidence,
        volatility_regime: Math.abs(change24h) > 5 ? 'High' : Math.abs(change24h) > 2 ? 'Normal' : 'Low',
        funding_rate: fundingRate,
        key_observation: `${symbol} ${change24h > 0 ? 'up' : 'down'} ${Math.abs(change24h).toFixed(2)}% in 24h. ${sentiment.charAt(0).toUpperCase() + sentiment.slice(1)} momentum.`
      });

      // Generate dynamic scenarios based on current price
      generateScenarios(currentPrice, change24h);

      // Mock flow data (TODO: fetch real on-chain data)
      setFlowData({
        exchange_netflow: change24h < 0 ? -3250000 : -1500000,
        miner_reserve_change: change24h > 0 ? 1200 : -800,
        whale_transactions: Math.floor(30 + Math.random() * 30),
        stablecoin_supply_ratio: 0.08,
        liquidations_24h: {
          longs: change24h < 0 ? 25000000 : 12500000,
          shorts: change24h > 0 ? 30000000 : 18700000
        }
      });

    } catch (error) {
      console.error('Failed to fetch market data:', error);
    }
  };

  const generateScenarios = (currentPrice: number, change24h: number) => {
    // Calculate dynamic price targets based on current price
    const resistance1 = currentPrice * 1.03; // +3%
    const resistance2 = currentPrice * 1.06; // +6%
    const support1 = currentPrice * 0.97; // -3%
    const support2 = currentPrice * 0.94; // -6%

    // Probabilities based on recent momentum
    let bullProb = 0.35;
    let baseProb = 0.35;
    let bearProb = 0.30;

    if (change24h > 3) {
      bullProb = 0.50;
      baseProb = 0.30;
      bearProb = 0.20;
    } else if (change24h < -3) {
      bullProb = 0.20;
      baseProb = 0.30;
      bearProb = 0.50;
    }

    setScenarios([
      {
        name: 'Bull',
        type: 'bull',
        prob: bullProb,
        trigger: `Break above $${(currentPrice * 1.02).toLocaleString('en-US', {maximumFractionDigits: 0})}`,
        targets: [
          Math.round(resistance1),
          Math.round(resistance2)
        ],
        invalidation: `Drop below $${support1.toLocaleString('en-US', {maximumFractionDigits: 0})}`
      },
      {
        name: 'Base',
        type: 'base',
        prob: baseProb,
        trigger: 'Range continuation',
        targets: [Math.round(currentPrice)],
        invalidation: 'Break of range'
      },
      {
        name: 'Bear',
        type: 'bear',
        prob: bearProb,
        trigger: `Break below $${support1.toLocaleString('en-US', {maximumFractionDigits: 0})}`,
        targets: [
          Math.round(support1),
          Math.round(support2)
        ],
        invalidation: `Recovery above $${(currentPrice * 1.01).toLocaleString('en-US', {maximumFractionDigits: 0})}`
      }
    ]);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Grid container spacing={3}>
        {/* Top Row: Market Pulse & Key Metrics */}
        <Grid item xs={12} md={8}>
          <MarketPulse data={marketData} />
        </Grid>
        <Grid item xs={12} md={4}>
          <FlowWidget data={flowData} />
        </Grid>

        {/* Main Chart with Controls */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 650 }}>
            <CardContent>
              {/* Chart Controls */}
              <Box sx={{ display: 'flex', gap: 2, mb: 2, flexWrap: 'wrap' }}>
                <FormControl size="small" sx={{ minWidth: 150 }}>
                  <InputLabel>Symbol</InputLabel>
                  <Select
                    value={symbol}
                    label="Symbol"
                    onChange={(e: SelectChangeEvent) => setSymbol(e.target.value)}
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
                    value={timeframe}
                    label="Timeframe"
                    onChange={(e: SelectChangeEvent) => setTimeframe(e.target.value)}
                  >
                    <MenuItem value="1m">1 Minute</MenuItem>
                    <MenuItem value="5m">5 Minutes</MenuItem>
                    <MenuItem value="15m">15 Minutes</MenuItem>
                    <MenuItem value="30m">30 Minutes</MenuItem>
                    <MenuItem value="1H">1 Hour</MenuItem>
                    <MenuItem value="4H">4 Hours</MenuItem>
                    <MenuItem value="1D">1 Day</MenuItem>
                    <MenuItem value="1w">1 Week</MenuItem>
                    <MenuItem value="1M">1 Month</MenuItem>
                  </Select>
                </FormControl>
              </Box>

              {/* Chart */}
              <TradingViewChart symbol={symbol} interval={timeframe} marketType={marketType} />
            </CardContent>
          </Card>
        </Grid>

        {/* Scenarios */}
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            {scenarios.map((scenario) => (
              <Grid item xs={12} key={scenario.name}>
                <ScenarioCard scenario={scenario} />
              </Grid>
            ))}
          </Grid>
        </Grid>

        {/* Alerts */}
        <Grid item xs={12}>
          <AlertsList alerts={alerts} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;
