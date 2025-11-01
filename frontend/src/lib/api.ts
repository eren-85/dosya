/**
 * Type-safe API client with retry logic for 429 errors
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface ApiOptions {
  retries?: number;
  retryDelay?: number;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: any
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  apiOptions: ApiOptions = {}
): Promise<Response> {
  const { retries = 3, retryDelay = 1000 } = apiOptions;
  let lastError: Error;

  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);

      // Retry on 429 (rate limit)
      if (response.status === 429 && i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, i)));
        continue;
      }

      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new ApiError(response.status, response.statusText, data);
      }

      return response;
    } catch (error) {
      lastError = error as Error;
      if (error instanceof ApiError) {
        throw error;
      }
      // Network error - retry
      if (i < retries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay * Math.pow(2, i)));
        continue;
      }
    }
  }

  throw lastError!;
}

// Market Data Types
export interface TickerData {
  symbol: string;
  price: number;
  change24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
}

export interface CandleData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

// Analysis Types
export interface MarketHealth {
  vix?: number;
  fear_greed?: number;
  realized_cap_ratio?: number;
  mvrv?: number;
  nupl?: number;
}

export interface LiquidityMetrics {
  orderbook_imbalance?: number;
  effective_spread?: number;
  slippage_1pct?: number;
  bid_ask_spread?: number;
}

export interface Scenario {
  name: string;
  probability: number;
  trigger_price: number;
  invalidation_price: number;
  targets: number[];
  description: string;
}

export interface Alert {
  id: string;
  type: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: number;
}

export interface ExtendedAnalysis {
  market_health?: MarketHealth;
  liquidity_metrics?: LiquidityMetrics;
  on_chain_flows?: any;
  derivatives_data?: any;
  scenarios?: Scenario[];
  alerts?: Alert[];
  market_pulse?: string;
  asian_killzone?: { start: string; end: string; active: boolean };
  london_killzone?: { start: string; end: string; active: boolean };
  ny_killzone?: { start: string; end: string; active: boolean };
}

// API Methods
export const api = {
  // Market data
  async getTicker(symbol: string): Promise<TickerData> {
    const response = await fetchWithRetry(`${API_BASE_URL}/api/market/ticker/${symbol}`);
    return response.json();
  },

  async getCandles(
    symbol: string,
    interval: string,
    limit: number = 500
  ): Promise<CandleData[]> {
    const response = await fetchWithRetry(
      `${API_BASE_URL}/api/market/candles/${symbol}?interval=${interval}&limit=${limit}`
    );
    return response.json();
  },

  // Extended analysis
  async getExtendedAnalysis(
    symbol: string = 'BTCUSDT',
    interval: string = '1h'
  ): Promise<ExtendedAnalysis> {
    try {
      const response = await fetchWithRetry(
        `${API_BASE_URL}/api/analysis/extended?symbol=${symbol}&interval=${interval}`
      );
      return response.json();
    } catch (error) {
      console.error('Extended analysis error:', error);
      return {}; // Return empty object for graceful degradation
    }
  },

  // Training
  async startTraining(params: {
    symbols: string[];
    timeframes: string;
    model_type: string;
    epochs: number;
    device: string;
  }): Promise<any> {
    const response = await fetchWithRetry(`${API_BASE_URL}/api/ops/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
    return response.json();
  },

  // Download data
  async downloadData(params: {
    symbols: string[];
    interval: string;
    market: 'spot' | 'futures';
    all_time: boolean;
    start_date?: string;
    end_date?: string;
  }): Promise<any> {
    const response = await fetchWithRetry(`${API_BASE_URL}/api/ops/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbols: params.symbols,
        interval: params.interval,
        market: params.market,
        all_time: params.all_time,
        start_date: params.start_date,
        end_date: params.end_date,
        parquet: true,
      }),
    });
    return response.json();
  },

  // Backtest
  async runBacktest(params: {
    symbols: string[];
    timeframe: string;
    strategy: string;
    start_date: string;
    end_date: string;
    initial_capital: number;
    position_size_pct?: number;
    commission_pct?: number;
  }): Promise<any> {
    const response = await fetchWithRetry(`${API_BASE_URL}/api/ops/backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbols: params.symbols,
        timeframe: params.timeframe,
        strategy: params.strategy,
        start_date: params.start_date,
        end_date: params.end_date,
        initial_capital: params.initial_capital,
        position_size_pct: params.position_size_pct || 10.0,
        commission_pct: params.commission_pct || 0.1,
      }),
    });
    return response.json();
  },

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: number }> {
    const response = await fetchWithRetry(`${API_BASE_URL}/api/health`);
    return response.json();
  },
};
