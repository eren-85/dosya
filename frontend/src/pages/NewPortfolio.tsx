/**
 * Portfolio Page - Real Portfolio Tracker + Paper Trading
 * - Real Portfolio: Manual coin tracking with buy/sell history
 * - Paper Trading: AI recommendations and simulated trades
 * - Spot/Futures support
 * - P&L tracking, exposure breakdown
 */

import { useState, useEffect } from 'react';
import { Briefcase, TrendingUp, TrendingDown, Target, DollarSign, Plus, Trash2, Edit, X } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { MarketType, EXCHANGES } from '@/lib/constants';
import { cn } from '@/lib/utils';

interface HoldingTransaction {
  type: 'buy' | 'sell';
  price: number;
  amount: number;
  date: string;
  total: number;
}

interface Holding {
  id: string;
  symbol: string;
  exchange: string;
  totalAmount: number;
  avgBuyPrice: number;
  currentPrice: number;
  marketType: MarketType;
  transactions: HoldingTransaction[];
}

interface PaperPosition {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  confidence: number;
  aiRecommendation: string;
}

const STORAGE_KEY = 'dosya_portfolio_holdings';

// Default demo holdings (used only when localStorage is empty)
const DEFAULT_HOLDINGS: Holding[] = [
  {
    id: '1',
    symbol: 'BTC',
    exchange: 'binance',
    totalAmount: 0.5,
    avgBuyPrice: 65000,
    currentPrice: 67500,
    marketType: 'spot',
    transactions: [
      { type: 'buy', price: 64000, amount: 0.3, date: '2025-10-15', total: 19200 },
      { type: 'buy', price: 66500, amount: 0.2, date: '2025-10-20', total: 13300 },
    ],
  },
  {
    id: '2',
    symbol: 'ETH',
    exchange: 'binance',
    totalAmount: 8,
    avgBuyPrice: 3200,
    currentPrice: 3350,
    marketType: 'spot',
    transactions: [
      { type: 'buy', price: 3200, amount: 8, date: '2025-10-18', total: 25600 },
    ],
  },
];

export default function NewPortfolio() {
  const [activeTab, setActiveTab] = useState('real');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingHolding, setEditingHolding] = useState<Holding | null>(null);

  // Real Portfolio State - Load from localStorage on mount
  const [holdings, setHoldings] = useState<Holding[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (error) {
      console.error('Failed to load portfolio from localStorage:', error);
    }
    return DEFAULT_HOLDINGS;
  });

  // Save holdings to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(holdings));
    } catch (error) {
      console.error('Failed to save portfolio to localStorage:', error);
    }
  }, [holdings]);

  // CRUD Handlers
  const handleAddHolding = (newHolding: Omit<Holding, 'id' | 'currentPrice'>) => {
    const id = Date.now().toString();
    const currentPrice = newHolding.avgBuyPrice; // Initially set to avg buy price
    setHoldings(prev => [...prev, { ...newHolding, id, currentPrice }]);
    setShowAddModal(false);
  };

  const handleEditHolding = (updatedHolding: Holding) => {
    setHoldings(prev => prev.map(h => h.id === updatedHolding.id ? updatedHolding : h));
    setEditingHolding(null);
  };

  const handleDeleteHolding = (id: string) => {
    if (confirm('Are you sure you want to delete this holding?')) {
      setHoldings(prev => prev.filter(h => h.id !== id));
    }
  };

  // Paper Trading State
  const [paperPositions] = useState<PaperPosition[]>([
    {
      symbol: 'BTCUSDT',
      side: 'LONG',
      size: 0.5,
      entryPrice: 65000,
      currentPrice: 67500,
      pnl: 1250,
      pnlPercent: 3.85,
      confidence: 78,
      aiRecommendation: 'PPO Agent suggests LONG with high confidence',
    },
    {
      symbol: 'ETHUSDT',
      side: 'LONG',
      size: 8,
      entryPrice: 3200,
      currentPrice: 3350,
      pnl: 1200,
      pnlPercent: 4.69,
      confidence: 72,
      aiRecommendation: 'LSTM predicts uptrend continuation',
    },
  ]);

  // Calculate Real Portfolio Stats
  const totalRealValue = holdings.reduce(
    (sum, h) => sum + h.totalAmount * h.currentPrice,
    0
  );
  const totalRealCost = holdings.reduce(
    (sum, h) => sum + h.totalAmount * h.avgBuyPrice,
    0
  );
  const realPnL = totalRealValue - totalRealCost;
  const realPnLPercent = totalRealCost > 0 ? (realPnL / totalRealCost) * 100 : 0;

  // Calculate Paper Portfolio Stats
  const paperPnL = paperPositions.reduce((sum, pos) => sum + pos.pnl, 0);
  const paperValue = paperPositions.reduce(
    (sum, pos) => sum + pos.size * pos.currentPrice,
    0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
          <p className="text-muted-foreground">
            Track your real holdings and AI-powered paper trading
          </p>
        </div>
        <MarketTypeSelector value={marketType} onChange={setMarketType} />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full md:w-[400px] grid-cols-2">
          <TabsTrigger value="real">Real Portfolio</TabsTrigger>
          <TabsTrigger value="paper">Paper Trading</TabsTrigger>
        </TabsList>

        {/* REAL PORTFOLIO TAB */}
        <TabsContent value="real" className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Value</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${totalRealValue.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">
                  ${totalRealCost.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div
                  className={cn(
                    'text-2xl font-bold',
                    realPnL > 0 ? 'text-green-500' : 'text-red-500'
                  )}
                >
                  {realPnL > 0 ? '+' : ''}${realPnL.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">P&L %</CardTitle>
                <Briefcase className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div
                  className={cn(
                    'text-2xl font-bold',
                    realPnLPercent > 0 ? 'text-green-500' : 'text-red-500'
                  )}
                >
                  {realPnLPercent > 0 ? '+' : ''}{realPnLPercent.toFixed(2)}%
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Add Coin Button */}
          <div className="flex justify-end">
            <Button onClick={() => setShowAddModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Coin
            </Button>
          </div>

          {/* Holdings Table */}
          <Card>
            <CardHeader>
              <CardTitle>My Holdings</CardTitle>
              <CardDescription>Manually track your cryptocurrency positions</CardDescription>
            </CardHeader>
            <CardContent>
              {holdings.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No holdings yet. Click "Add Coin" to start tracking.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b text-left text-sm text-muted-foreground">
                        <th className="pb-3 font-medium">Coin</th>
                        <th className="pb-3 font-medium">Amount</th>
                        <th className="pb-3 font-medium">Avg Buy</th>
                        <th className="pb-3 font-medium">Current</th>
                        <th className="pb-3 font-medium">Value</th>
                        <th className="pb-3 font-medium text-right">P&L</th>
                        <th className="pb-3 font-medium text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {holdings.map((holding) => {
                        const value = holding.totalAmount * holding.currentPrice;
                        const cost = holding.totalAmount * holding.avgBuyPrice;
                        const pnl = value - cost;
                        const pnlPercent = cost > 0 ? (pnl / cost) * 100 : 0;

                        return (
                          <tr key={holding.id} className="border-b last:border-0">
                            <td className="py-4 font-medium">{holding.symbol}</td>
                            <td className="py-4 text-sm">{holding.totalAmount}</td>
                            <td className="py-4 text-sm">
                              ${holding.avgBuyPrice.toLocaleString()}
                            </td>
                            <td className="py-4 text-sm">
                              ${holding.currentPrice.toLocaleString()}
                            </td>
                            <td className="py-4 text-sm">
                              ${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                            </td>
                            <td
                              className={cn(
                                'py-4 text-right font-medium',
                                pnl > 0 ? 'text-green-500' : 'text-red-500'
                              )}
                            >
                              <div className="flex items-center justify-end gap-2">
                                {pnl > 0 ? (
                                  <TrendingUp className="w-4 h-4" />
                                ) : (
                                  <TrendingDown className="w-4 h-4" />
                                )}
                                <div>
                                  {pnl > 0 ? '+' : ''}$
                                  {Math.abs(pnl).toLocaleString(undefined, {
                                    maximumFractionDigits: 2,
                                  })}
                                  <span className="text-xs ml-1">
                                    ({pnl > 0 ? '+' : ''}
                                    {pnlPercent.toFixed(2)}%)
                                  </span>
                                </div>
                              </div>
                            </td>
                            <td className="py-4 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => setEditingHolding(holding)}
                                  title="Edit holding"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeleteHolding(holding.id)}
                                  title="Delete holding"
                                >
                                  <Trash2 className="w-4 h-4 text-destructive" />
                                </Button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Exposure Breakdown */}
          {holdings.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Exposure Breakdown</CardTitle>
                <CardDescription>Asset allocation in your portfolio</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {holdings.map((holding) => {
                    const value = holding.totalAmount * holding.currentPrice;
                    const exposure = (value / totalRealValue) * 100;
                    return (
                      <div key={holding.id}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-sm font-medium">{holding.symbol}</span>
                          <span className="text-sm text-muted-foreground">
                            {exposure.toFixed(1)}%
                          </span>
                        </div>
                        <div className="w-full bg-secondary rounded-full h-2">
                          <div
                            className="bg-primary h-2 rounded-full"
                            style={{ width: `${exposure}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* PAPER TRADING TAB */}
        <TabsContent value="paper" className="space-y-6">
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Portfolio Value</CardTitle>
                <DollarSign className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">${paperValue.toLocaleString()}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className={cn('text-2xl font-bold', paperPnL > 0 ? 'text-green-500' : 'text-red-500')}>
                  ${paperPnL.toLocaleString()}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
                <Briefcase className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{paperPositions.length}</div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">
                  {(
                    paperPositions.reduce((sum, pos) => sum + pos.confidence, 0) /
                    paperPositions.length
                  ).toFixed(0)}
                  %
                </div>
              </CardContent>
            </Card>
          </div>

          {/* AI Positions Table */}
          <Card>
            <CardHeader>
              <CardTitle>AI-Recommended Positions</CardTitle>
              <CardDescription>Simulated trades based on model predictions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b text-left text-sm text-muted-foreground">
                      <th className="pb-3 font-medium">Symbol</th>
                      <th className="pb-3 font-medium">Side</th>
                      <th className="pb-3 font-medium">Size</th>
                      <th className="pb-3 font-medium">Entry</th>
                      <th className="pb-3 font-medium">Current</th>
                      <th className="pb-3 font-medium">AI Model</th>
                      <th className="pb-3 font-medium text-right">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paperPositions.map((pos, idx) => (
                      <tr key={idx} className="border-b last:border-0">
                        <td className="py-4 font-medium">{pos.symbol}</td>
                        <td className="py-4">
                          <Badge variant={pos.side === 'LONG' ? 'success' : 'warning'}>
                            {pos.side}
                          </Badge>
                        </td>
                        <td className="py-4 text-sm">{pos.size}</td>
                        <td className="py-4 text-sm">${pos.entryPrice.toLocaleString()}</td>
                        <td className="py-4 text-sm">${pos.currentPrice.toLocaleString()}</td>
                        <td className="py-4">
                          <div className="text-sm">
                            <div className="font-medium">{pos.aiRecommendation.split(' ')[0]}</div>
                            <div className="text-xs text-muted-foreground">
                              {pos.confidence}% confidence
                            </div>
                          </div>
                        </td>
                        <td
                          className={cn(
                            'py-4 text-right font-medium',
                            pos.pnl > 0 ? 'text-green-500' : 'text-red-500'
                          )}
                        >
                          <div className="flex items-center justify-end gap-2">
                            {pos.pnl > 0 ? (
                              <TrendingUp className="w-4 h-4" />
                            ) : (
                              <TrendingDown className="w-4 h-4" />
                            )}
                            <div>
                              ${Math.abs(pos.pnl).toLocaleString()}
                              <span className="text-xs ml-1">
                                ({pos.pnl > 0 ? '+' : ''}
                                {pos.pnlPercent.toFixed(2)}%)
                              </span>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add/Edit Modal */}
      {(showAddModal || editingHolding) && (
        <HoldingModal
          holding={editingHolding}
          onSave={editingHolding ? handleEditHolding : handleAddHolding}
          onClose={() => {
            setShowAddModal(false);
            setEditingHolding(null);
          }}
        />
      )}
    </div>
  );
}

// Holding Modal Component
interface HoldingModalProps {
  holding: Holding | null;
  onSave: (holding: any) => void;
  onClose: () => void;
}

function HoldingModal({ holding, onSave, onClose }: HoldingModalProps) {
  const [formData, setFormData] = useState({
    symbol: holding?.symbol || '',
    exchange: holding?.exchange || 'binance',
    totalAmount: holding?.totalAmount || 0,
    avgBuyPrice: holding?.avgBuyPrice || 0,
    marketType: holding?.marketType || 'spot' as MarketType,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (holding) {
      // Edit existing
      onSave({
        ...holding,
        ...formData,
      });
    } else {
      // Add new
      onSave({
        ...formData,
        transactions: [],
      });
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>{holding ? 'Edit' : 'Add'} Holding</CardTitle>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <CardDescription>
            {holding ? 'Update your holding details' : 'Add a new coin to your portfolio'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="symbol" className="text-sm font-medium mb-2 block">
                Symbol
              </label>
              <input
                id="symbol"
                type="text"
                value={formData.symbol}
                onChange={(e) => setFormData({ ...formData, symbol: e.target.value.toUpperCase() })}
                placeholder="BTC, ETH, etc."
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                required
              />
            </div>

            <div>
              <label htmlFor="exchange" className="text-sm font-medium mb-2 block">
                Exchange
              </label>
              <select
                id="exchange"
                value={formData.exchange}
                onChange={(e) => setFormData({ ...formData, exchange: e.target.value })}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                required
              >
                {EXCHANGES.map((ex) => (
                  <option key={ex.value} value={ex.value}>
                    {ex.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="marketType" className="text-sm font-medium mb-2 block">
                Market Type
              </label>
              <select
                id="marketType"
                value={formData.marketType}
                onChange={(e) => setFormData({ ...formData, marketType: e.target.value as MarketType })}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                required
              >
                <option value="spot">Spot</option>
                <option value="futures">Futures</option>
              </select>
            </div>

            <div>
              <label htmlFor="amount" className="text-sm font-medium mb-2 block">
                Amount
              </label>
              <input
                id="amount"
                type="number"
                step="0.00000001"
                value={formData.totalAmount}
                onChange={(e) => setFormData({ ...formData, totalAmount: Number(e.target.value) })}
                placeholder="0.5"
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                required
              />
            </div>

            <div>
              <label htmlFor="price" className="text-sm font-medium mb-2 block">
                Average Buy Price ($)
              </label>
              <input
                id="price"
                type="number"
                step="0.01"
                value={formData.avgBuyPrice}
                onChange={(e) => setFormData({ ...formData, avgBuyPrice: Number(e.target.value) })}
                placeholder="65000"
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                required
              />
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" className="flex-1">
                {holding ? 'Update' : 'Add'} Holding
              </Button>
              <Button type="button" variant="outline" onClick={onClose}>
                Cancel
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
