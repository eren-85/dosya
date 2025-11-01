/**
 * Portfolio Page
 * - Current positions
 * - Exposure breakdown
 * - Risk table with filters
 * - P&L tracking
 */

import React, { useState } from 'react';
import { Briefcase, TrendingUp, TrendingDown, Target, DollarSign } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
}

export default function NewPortfolio() {
  // Mock data
  const [positions] = useState<Position[]>([
    {
      symbol: 'BTCUSDT',
      side: 'LONG',
      size: 0.5,
      entryPrice: 65000,
      currentPrice: 67500,
      pnl: 1250,
      pnlPercent: 3.85,
    },
    {
      symbol: 'ETHUSDT',
      side: 'LONG',
      size: 8,
      entryPrice: 3200,
      currentPrice: 3350,
      pnl: 1200,
      pnlPercent: 4.69,
    },
    {
      symbol: 'SOLUSDT',
      side: 'SHORT',
      size: 100,
      entryPrice: 145,
      currentPrice: 142,
      pnl: 300,
      pnlPercent: 2.07,
    },
  ]);

  const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalValue = positions.reduce((sum, pos) => sum + (pos.size * pos.currentPrice), 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Portfolio</h1>
        <p className="text-muted-foreground">
          Track your positions and performance
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Value</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">${totalValue.toLocaleString()}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className={cn("text-2xl font-bold", totalPnL > 0 ? "text-green-500" : "text-red-500")}>
              ${totalPnL.toLocaleString()}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
            <Briefcase className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{positions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-500">75%</div>
          </CardContent>
        </Card>
      </div>

      {/* Positions Table */}
      <Card>
        <CardHeader>
          <CardTitle>Open Positions</CardTitle>
          <CardDescription>Your current trading positions</CardDescription>
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
                  <th className="pb-3 font-medium text-right">P&L</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((pos, idx) => (
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
                    <td className={cn(
                      "py-4 text-right font-medium",
                      pos.pnl > 0 ? "text-green-500" : "text-red-500"
                    )}>
                      <div className="flex items-center justify-end gap-2">
                        {pos.pnl > 0 ? (
                          <TrendingUp className="w-4 h-4" />
                        ) : (
                          <TrendingDown className="w-4 h-4" />
                        )}
                        <div>
                          ${Math.abs(pos.pnl).toLocaleString()}
                          <span className="text-xs ml-1">
                            ({pos.pnl > 0 ? '+' : ''}{pos.pnlPercent.toFixed(2)}%)
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

      {/* Exposure Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Exposure Breakdown</CardTitle>
          <CardDescription>Asset allocation across your portfolio</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {positions.map((pos, idx) => {
              const exposure = ((pos.size * pos.currentPrice) / totalValue) * 100;
              return (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{pos.symbol}</span>
                    <span className="text-sm text-muted-foreground">{exposure.toFixed(1)}%</span>
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
    </div>
  );
}
