import React from 'react';
import { Card, CardContent, Typography, Box, Chip, Grid } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import RemoveIcon from '@mui/icons-material/Remove';

interface Props {
  data: any;
}

const MarketPulse: React.FC<Props> = ({ data }) => {
  const sentiment = data?.sentiment || 'neutral';
  const confidence = (data?.confidence || 0.5) * 100;

  const getSentimentIcon = () => {
    switch (sentiment) {
      case 'bullish':
        return <TrendingUpIcon sx={{ color: '#00BFA6' }} />;
      case 'bearish':
        return <TrendingDownIcon sx={{ color: '#FF6B6B' }} />;
      default:
        return <RemoveIcon sx={{ color: '#FFC107' }} />;
    }
  };

  const getSentimentColor = () => {
    switch (sentiment) {
      case 'bullish':
        return '#00BFA6';
      case 'bearish':
        return '#FF6B6B';
      default:
        return '#FFC107';
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Market Pulse
        </Typography>

        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <Box display="flex" alignItems="center" gap={1}>
              {getSentimentIcon()}
              <Typography variant="h4" sx={{ color: getSentimentColor(), textTransform: 'capitalize' }}>
                {sentiment}
              </Typography>
            </Box>
            <Typography variant="caption" color="text.secondary">
              Confidence: {confidence.toFixed(1)}%
            </Typography>
          </Grid>

          <Grid item xs={12} md={8}>
            <Box display="flex" flexWrap="wrap" gap={1}>
              <Chip
                label={`BTC: $${data?.btc_price?.toLocaleString() || '---'}`}
                color="primary"
                variant="outlined"
              />
              <Chip
                label={`24h: ${data?.change_24h >= 0 ? '+' : ''}${data?.change_24h?.toFixed(2) || '0'}%`}
                color={data?.change_24h >= 0 ? 'success' : 'error'}
              />
              <Chip
                label={`Vol: ${data?.volatility_regime || 'Normal'}`}
                variant="outlined"
              />
              <Chip
                label={`Funding: ${data?.funding_rate ? (data.funding_rate * 100).toFixed(3) : '---'}%`}
                variant="outlined"
              />
            </Box>
          </Grid>
        </Grid>

        <Box mt={2}>
          <Typography variant="body2" color="text.secondary">
            {data?.key_observation || 'Analyzing market conditions...'}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default MarketPulse;
