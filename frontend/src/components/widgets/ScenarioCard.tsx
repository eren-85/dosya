import React from 'react';
import { Card, CardContent, Typography, Box, LinearProgress, Chip } from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import RemoveIcon from '@mui/icons-material/Remove';

interface Scenario {
  name: string;
  type: 'bull' | 'base' | 'bear';
  prob: number;
  trigger: string;
  targets: number[];
  invalidation: string;
}

interface Props {
  scenario: Scenario;
}

const ScenarioCard: React.FC<Props> = ({ scenario }) => {
  const getColor = () => {
    switch (scenario.type) {
      case 'bull':
        return '#00BFA6';
      case 'bear':
        return '#FF6B6B';
      default:
        return '#FFC107';
    }
  };

  const getIcon = () => {
    switch (scenario.type) {
      case 'bull':
        return <ArrowUpwardIcon />;
      case 'bear':
        return <ArrowDownwardIcon />;
      default:
        return <RemoveIcon />;
    }
  };

  return (
    <Card sx={{ borderLeft: `4px solid ${getColor()}` }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            {getIcon()}
            <Typography variant="h6">{scenario.name}</Typography>
          </Box>
          <Chip
            label={`${(scenario.prob * 100).toFixed(0)}%`}
            size="small"
            sx={{ bgcolor: getColor(), fontWeight: 'bold' }}
          />
        </Box>

        <LinearProgress
          variant="determinate"
          value={scenario.prob * 100}
          sx={{
            mb: 2,
            height: 8,
            borderRadius: 4,
            bgcolor: 'rgba(255,255,255,0.1)',
            '& .MuiLinearProgress-bar': {
              bgcolor: getColor(),
            },
          }}
        />

        <Box mb={1}>
          <Typography variant="caption" color="text.secondary">
            Trigger
          </Typography>
          <Typography variant="body2">{scenario.trigger}</Typography>
        </Box>

        <Box mb={1}>
          <Typography variant="caption" color="text.secondary">
            Targets
          </Typography>
          <Typography variant="body2">
            {scenario.targets.map((t) => `$${t.toLocaleString()}`).join(', ')}
          </Typography>
        </Box>

        <Box>
          <Typography variant="caption" color="text.secondary">
            Invalidation
          </Typography>
          <Typography variant="body2" color="error">
            {scenario.invalidation}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ScenarioCard;
