import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Divider,
} from '@mui/material';
import NotificationsIcon from '@mui/icons-material/Notifications';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';
import ErrorIcon from '@mui/icons-material/Error';
import DeleteIcon from '@mui/icons-material/Delete';

interface Alert {
  type: string;
  title: string;
  message: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
}

interface Props {
  alerts: Alert[];
  onClearAlert?: (index: number) => void;
}

const AlertsList: React.FC<Props> = ({ alerts, onClearAlert }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return '#FF1744';
      case 'high':
        return '#FF6B6B';
      case 'medium':
        return '#FFC107';
      case 'low':
        return '#00BFA6';
      default:
        return '#888';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <ErrorIcon sx={{ color: getPriorityColor(priority) }} />;
      case 'high':
        return <WarningIcon sx={{ color: getPriorityColor(priority) }} />;
      case 'medium':
        return <InfoIcon sx={{ color: getPriorityColor(priority) }} />;
      default:
        return <NotificationsIcon sx={{ color: getPriorityColor(priority) }} />;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
      return `${Math.floor(diffMins / 1440)}d ago`;
    } catch {
      return timestamp;
    }
  };

  if (alerts.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Recent Alerts
          </Typography>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              py: 4,
            }}
          >
            <NotificationsIcon sx={{ fontSize: 48, color: '#888', mb: 2 }} />
            <Typography variant="body2" color="text.secondary">
              No alerts yet
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Recent Alerts</Typography>
          <Chip label={`${alerts.length} active`} size="small" color="primary" />
        </Box>

        <List sx={{ maxHeight: 400, overflow: 'auto' }}>
          {alerts.map((alert, index) => (
            <React.Fragment key={index}>
              <ListItem
                sx={{
                  borderLeft: `4px solid ${getPriorityColor(alert.priority)}`,
                  mb: 1,
                  bgcolor: 'rgba(255,255,255,0.02)',
                  borderRadius: 1,
                }}
                secondaryAction={
                  onClearAlert && (
                    <IconButton
                      edge="end"
                      aria-label="delete"
                      onClick={() => onClearAlert(index)}
                      size="small"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  )
                }
              >
                <Box sx={{ mr: 2 }}>{getPriorityIcon(alert.priority)}</Box>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle2">{alert.title}</Typography>
                      <Chip
                        label={alert.type}
                        size="small"
                        sx={{ fontSize: '0.7rem', height: 20 }}
                      />
                    </Box>
                  }
                  secondary={
                    <>
                      <Typography variant="body2" component="span" sx={{ display: 'block', mt: 0.5 }}>
                        {alert.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                        {formatTimestamp(alert.timestamp)}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
              {index < alerts.length - 1 && <Divider sx={{ my: 1 }} />}
            </React.Fragment>
          ))}
        </List>
      </CardContent>
    </Card>
  );
};

export default AlertsList;
