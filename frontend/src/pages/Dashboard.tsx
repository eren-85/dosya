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

  // Symbol, timeframe, and market type selection
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1H');
  const [marketType, setMarketType] = useState('futures'); // 'futures' or 'spot'

  // Market data (TODO: fetch from backend API)
  const [marketData, setMarketData] = useState({
    symbol: 'BTCUSDT',
    btc_price: 67234,
    change_24h: 2.34,
    sentiment: 'bullish',
    confidence: 0.72,
    volatility_regime: 'Normal',
    funding_rate: 0.0082,
    key_observation: 'Price consolidating above $67k support. Bullish momentum building.'
  });

  // Flow data (TODO: fetch from backend API)
  const [flowData, setFlowData] = useState({
    exchange_netflow: -3250000, // Negative = outflow (bullish)
    miner_reserve_change: 1200, // Positive = accumulation
    whale_transactions: 47,
    stablecoin_supply_ratio: 0.08,
    liquidations_24h: {
      longs: 12500000,
      shorts: 18700000
    }
  });

  const [scenarios, setScenarios] = useState([
    {
      name: 'Bull',
      type: 'bull',
      prob: 0.45,
      trigger: 'Break above $68,000',
      targets: [70000, 72000],
      invalidation: 'Drop below $65,500'
    },
    {
      name: 'Base',
      type: 'base',
      prob: 0.35,
      trigger: 'Range continuation',
      targets: [67500],
      invalidation: 'Break of range'
    },
    {
      name: 'Bear',
      type: 'bear',
      prob: 0.20,
      trigger: 'Break below $65,000',
      targets: [63000, 60000],
      invalidation: 'Recovery above $66,500'
    }
  ]);

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
