import React from 'react';
import { Card, CardContent, Typography, Box, Grid, Chip } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';

interface FlowData {
  exchange_netflow: number;
  miner_reserve_change: number;
  whale_transactions: number;
  stablecoin_supply_ratio: number;
  liquidations_24h: {
    longs: number;
    shorts: number;
  };
}

interface Props {
  data: FlowData | null;
}

const FlowWidget: React.FC<Props> = ({ data }) => {
  if (!data) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Money Flow & On-Chain
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Loading flow data...
          </Typography>
        </CardContent>
      </Card>
    );
  }

  const formatNumber = (num: number) => {
    if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B`;
    if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M`;
    if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const getFlowColor = (value: number) => {
    return value > 0 ? '#00BFA6' : '#FF6B6B';
  };

  const getFlowIcon = (value: number) => {
    return value > 0 ? <TrendingUpIcon /> : <TrendingDownIcon />;
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Money Flow & On-Chain
        </Typography>

        <Grid container spacing={2} sx={{ mt: 1 }}>
          {/* Exchange Netflow */}
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Exchange Netflow
              </Typography>
              <Box display="flex" alignItems="center" gap={0.5}>
                {getFlowIcon(data.exchange_netflow)}
                <Typography
                  variant="h6"
                  sx={{ color: getFlowColor(data.exchange_netflow) }}
                >
                  {formatNumber(data.exchange_netflow)}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                {data.exchange_netflow > 0 ? 'Inflow (Bearish)' : 'Outflow (Bullish)'}
              </Typography>
            </Box>
          </Grid>

          {/* Miner Reserve Change */}
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Miner Reserve Change
              </Typography>
              <Box display="flex" alignItems="center" gap={0.5}>
                {getFlowIcon(data.miner_reserve_change)}
                <Typography
                  variant="h6"
                  sx={{ color: getFlowColor(data.miner_reserve_change) }}
                >
                  {formatNumber(data.miner_reserve_change)}
                </Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                {data.miner_reserve_change > 0 ? 'Accumulating' : 'Selling'}
              </Typography>
            </Box>
          </Grid>

          {/* Whale Transactions */}
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Whale Transactions (24h)
              </Typography>
              <Typography variant="h6">{data.whale_transactions}</Typography>
              <Typography variant="caption" color="text.secondary">
                Txs &gt; $1M
              </Typography>
            </Box>
          </Grid>

          {/* Stablecoin Supply Ratio */}
          <Grid item xs={6}>
            <Box>
              <Typography variant="caption" color="text.secondary">
                Stablecoin Supply Ratio
              </Typography>
              <Typography variant="h6">
                {(data.stablecoin_supply_ratio * 100).toFixed(2)}%
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Buying Power
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Liquidations */}
        <Box sx={{ mt: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Liquidations (24h)
          </Typography>
          <Box display="flex" gap={1}>
            <Chip
              label={`Longs: $${formatNumber(data.liquidations_24h.longs)}`}
              size="small"
              sx={{ bgcolor: '#FF6B6B' }}
            />
            <Chip
              label={`Shorts: $${formatNumber(data.liquidations_24h.shorts)}`}
              size="small"
              sx={{ bgcolor: '#00BFA6' }}
            />
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            {data.liquidations_24h.longs > data.liquidations_24h.shorts
              ? 'More long liquidations (bearish)'
              : 'More short liquidations (bullish)'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default FlowWidget;
