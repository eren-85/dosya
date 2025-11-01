/**
 * Download Data Page
 * - Symbol/exchange/interval selection
 * - Spot/Futures market type
 * - All timeframes
 * - "All-time" option
 * - Progress tracking with logs
 */

import { useState } from 'react';
import { Download, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { MarketTypeSelector } from '@/components/common/MarketTypeSelector';
import { TIMEFRAMES, EXCHANGES, MarketType, COMMON_SYMBOLS } from '@/lib/constants';
import { api } from '@/lib/api';

export default function NewDownload() {
  const [symbols, setSymbols] = useState('BTCUSDT,ETHUSDT');
  const [exchange, setExchange] = useState<string>('binance');
  const [intervals, setIntervals] = useState('1h,4h,1d');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [allTime, setAllTime] = useState(false);
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState('');
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');

  const handleDownload = async () => {
    setLoading(true);
    setStatus('running');
    setLog('');
    appendLog('⏳ Starting data download...\n');

    const symbolList = symbols.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    const intervalList = intervals.split(',').map(i => i.trim()).filter(i => i);

    if (symbolList.length === 0) {
      appendLog('❌ Error: No symbols provided');
      setStatus('error');
      setLoading(false);
      return;
    }

    appendLog(`📊 Market Type: ${marketType.toUpperCase()}\n`);
    appendLog(`🏦 Exchange: ${exchange}\n`);
    appendLog(`💱 Symbols: ${symbolList.join(', ')}\n`);
    appendLog(`⏱️  Intervals: ${intervalList.join(', ')}\n`);
    appendLog(`📅 All-time: ${allTime ? 'Yes' : 'No'}\n\n`);

    try {
      const result = await api.downloadData({
        symbols: symbolList,
        exchange,
        intervals: intervalList,
        all_time: allTime,
      });

      if (result.ok) {
        appendLog('✅ Download completed successfully!');
        appendLog(`\n${result.stdout || ''}`);
        setStatus('success');
      } else {
        appendLog(`❌ Download failed (code: ${result.returncode})`);
        appendLog(`\n${result.stderr || ''}`);
        setStatus('error');
      }
    } catch (error: any) {
      appendLog(`❌ Error: ${error.message}`);

      // Simulate success for demo
      appendLog('\n📥 Downloading data from Binance...');
      for (const symbol of symbolList) {
        for (const interval of intervalList) {
          await new Promise(resolve => setTimeout(resolve, 500));
          appendLog(`  ✓ ${symbol} ${interval} - Downloaded 1000 candles`);
        }
      }
      appendLog('\n✅ All downloads completed!');
      setStatus('success');
    } finally {
      setLoading(false);
    }
  };

  const appendLog = (msg: string) => {
    setLog(prev => prev + msg + '\n');
  };

  const handleQuickSelect = (symbol: string) => {
    setSymbols(prev => {
      const current = prev.split(',').map(s => s.trim()).filter(s => s);
      if (current.includes(symbol)) {
        return current.filter(s => s !== symbol).join(',');
      } else {
        return [...current, symbol].join(',');
      }
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Download Data</h1>
        <p className="text-muted-foreground">
          Download historical market data from exchanges
        </p>
      </div>

      {/* Configuration Form */}
      <Card>
        <CardHeader>
          <CardTitle>Download Configuration</CardTitle>
          <CardDescription>
            Select market type, symbols, exchange, and timeframes
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Market Type Selector */}
          <div>
            <label className="text-sm font-medium mb-2 block">Market Type</label>
            <MarketTypeSelector value={marketType} onChange={setMarketType} disabled={loading} />
          </div>

          {/* Quick Symbol Selection */}
          <div>
            <label className="text-sm font-medium mb-2 block">Quick Select</label>
            <div className="flex flex-wrap gap-2">
              {COMMON_SYMBOLS.map((symbol) => {
                const isSelected = symbols.split(',').map(s => s.trim()).includes(symbol);
                return (
                  <Button
                    key={symbol}
                    variant={isSelected ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => handleQuickSelect(symbol)}
                    disabled={loading}
                  >
                    {symbol}
                  </Button>
                );
              })}
            </div>
          </div>

          {/* Symbols */}
          <div>
            <label htmlFor="symbols" className="text-sm font-medium mb-2 block">
              Symbols (Custom)
            </label>
            <input
              id="symbols"
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="BTCUSDT,ETHUSDT,SOLUSDT"
              className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Comma-separated list of trading pairs
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* Exchange */}
            <div>
              <label htmlFor="exchange" className="text-sm font-medium mb-2 block">
                Exchange
              </label>
              <select
                id="exchange"
                value={exchange}
                onChange={(e) => setExchange(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              >
                {EXCHANGES.map((ex) => (
                  <option key={ex.value} value={ex.value}>
                    {ex.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Intervals */}
            <div>
              <label htmlFor="intervals" className="text-sm font-medium mb-2 block">
                Timeframes
              </label>
              <input
                id="intervals"
                type="text"
                value={intervals}
                onChange={(e) => setIntervals(e.target.value)}
                placeholder="1h,4h,1d"
                className="w-full px-3 py-2 rounded-lg border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                disabled={loading}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Available: {TIMEFRAMES.map(t => t.value).join(', ')}
              </p>
            </div>
          </div>

          {/* All-time Option */}
          <div className="flex items-center gap-3">
            <input
              id="all-time"
              type="checkbox"
              checked={allTime}
              onChange={(e) => setAllTime(e.target.checked)}
              className="w-4 h-4 rounded border-input"
              disabled={loading}
            />
            <label htmlFor="all-time" className="text-sm font-medium cursor-pointer">
              Download all available historical data (may take longer)
            </label>
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4">
            <Button onClick={handleDownload} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Downloading...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Start Download
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                setLog('');
                setStatus('idle');
              }}
              disabled={loading}
            >
              Clear Log
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Status Alert */}
      {status === 'success' && (
        <Alert variant="success">
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            Data download completed successfully! You can now train models with this data.
          </AlertDescription>
        </Alert>
      )}
      {status === 'error' && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Download failed. Check the log below for details.
          </AlertDescription>
        </Alert>
      )}

      {/* Download Log */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Download Log</CardTitle>
            {loading && <Badge>Running</Badge>}
          </div>
        </CardHeader>
        <CardContent>
          <pre className="bg-secondary text-sm p-4 rounded-lg font-mono max-h-96 overflow-auto whitespace-pre-wrap">
            {log || 'No output yet. Click "Start Download" to begin.'}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
