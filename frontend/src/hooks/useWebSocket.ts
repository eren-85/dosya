import { useEffect, useState } from 'react';
import io, { Socket } from 'socket.io-client';

interface MarketData {
  symbol: string;
  price: number;
  change_24h: number;
  sentiment: 'bullish' | 'neutral' | 'bearish';
  confidence: number;
  volatility_regime: string;
  funding_rate: number;
  key_observation: string;
}

export const useWebSocket = (url?: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // WebSocket disabled for now - backend doesn't have socket.io yet
    // TODO: Enable when backend implements WebSocket endpoints
    if (!url) {
      console.log('ℹ️ WebSocket disabled (backend not configured)');
      return;
    }

    const socketInstance = io(url, {
      transports: ['websocket'],
      reconnection: true,
      reconnectionAttempts: 3, // Limit reconnection attempts
    });

    socketInstance.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
      setIsConnected(false);
    });

    socketInstance.on('connect_error', (error) => {
      // Suppress error logs to avoid spam
      setIsConnected(false);
    });

    // Market data updates
    socketInstance.on('market_update', (data: MarketData) => {
      setMarketData(data);
    });

    // Alert notifications
    socketInstance.on('alert', (alert: any) => {
      setAlerts((prev) => [alert, ...prev].slice(0, 50));
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [url]);

  return { socket, marketData, alerts, isConnected };
};
