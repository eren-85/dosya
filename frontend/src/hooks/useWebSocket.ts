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

export const useWebSocket = (url: string) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [marketData, setMarketData] = useState<MarketData | null>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(url, {
      transports: ['websocket'],
      reconnection: true,
    });

    socketInstance.on('connect', () => {
      console.log('✅ WebSocket connected');
      setIsConnected(true);
    });

    socketInstance.on('disconnect', () => {
      console.log('❌ WebSocket disconnected');
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
