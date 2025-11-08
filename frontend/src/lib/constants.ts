/**
 * Common constants used across the application
 */

// Timeframes for all trading operations
export const TIMEFRAMES = [
  { value: '1m', label: '1 Minute' },
  { value: '3m', label: '3 Minutes' },
  { value: '5m', label: '5 Minutes' },
  { value: '15m', label: '15 Minutes' },
  { value: '30m', label: '30 Minutes' },
  { value: '1h', label: '1 Hour' },
  { value: '2h', label: '2 Hours' },
  { value: '4h', label: '4 Hours' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '3d', label: '3 Days' },
  { value: '1w', label: '1 Week' },
  { value: '1M', label: '1 Month' },
] as const;

export type TimeframeValue = typeof TIMEFRAMES[number]['value'];

// Market types
export const MARKET_TYPES = [
  { value: 'spot', label: 'Spot' },
  { value: 'futures', label: 'Futures' },
] as const;

export type MarketType = typeof MARKET_TYPES[number]['value'];

// Exchanges
export const EXCHANGES = [
  { value: 'binance', label: 'Binance' },
  { value: 'bybit', label: 'Bybit' },
  { value: 'okx', label: 'OKX' },
  { value: 'mexc', label: 'MEXC' },
] as const;

export type ExchangeValue = typeof EXCHANGES[number]['value'];

// Common symbols
export const COMMON_SYMBOLS = [
  'BTCUSDT',
  'ETHUSDT',
  'BNBUSDT',
  'SOLUSDT',
  'XRPUSDT',
  'ADAUSDT',
  'DOGEUSDT',
  'AVAXUSDT',
  'DOTUSDT',
  'MATICUSDT',
] as const;
