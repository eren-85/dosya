import React, { useEffect, useState } from 'react';
import { Grid, Card, CardContent, Typography, Box } from '@mui/material';
import TradingViewChart from '../components/charts/TradingViewChart';
import MarketPulse from '../components/widgets/MarketPulse';
import ScenarioCard from '../components/widgets/ScenarioCard';
import FlowWidget from '../components/widgets/FlowWidget';
import AlertsList from '../components/widgets/AlertsList';
import { useWebSocket } from '../hooks/useWebSocket';

const Dashboard: React.FC = () => {
  const { marketData, alerts, isConnected } = useWebSocket('ws://localhost:8000/ws');

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
          <FlowWidget />
        </Grid>

        {/* Main Chart */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 600 }}>
            <CardContent>
              <TradingViewChart symbol="BTCUSDT" interval="1H" />
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
