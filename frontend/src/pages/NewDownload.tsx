/**
 * Download Data Page
 * - Symbol/exchange/interval selection
 * - "All-time" option
 * - Progress tracking with logs
 * - Toast notifications
 */

import React, { useState } from 'react';
import { Download, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { api } from '@/lib/api';

export default function NewDownload() {
  const [symbols, setSymbols] = useState('BTCUSDT,ETHUSDT');
  const [exchange, setExchange] = useState('binance');
  const [intervals, setIntervals] = useState('1h,4h,1d');
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
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const appendLog = (msg: string) => {
    setLog(prev => prev + msg + '\n');
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
            Select symbols, exchange, and timeframes to download
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Symbols */}
          <div>
            <label htmlFor="symbols" className="text-sm font-medium mb-2 block">
              Symbols
            </label>
            <input
              id="symbols"
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="BTCUSDT,ETHUSDT,SOLUSDT"
              className="w-full px-3 py-2 rounded-lg border bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Comma-separated list of trading pairs
            </p>
          </div>

          {/* Exchange */}
          <div>
            <label htmlFor="exchange" className="text-sm font-medium mb-2 block">
              Exchange
            </label>
            <select
              id="exchange"
              value={exchange}
              onChange={(e) => setExchange(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={loading}
            >
              <option value="binance">Binance</option>
              <option value="bybit">Bybit</option>
              <option value="okx">OKX</option>
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
              className="w-full px-3 py-2 rounded-lg border bg-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              disabled={loading}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Comma-separated intervals (e.g., 1m, 5m, 15m, 1h, 4h, 1d)
            </p>
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
              Download all available historical data
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
            Data download completed successfully! You can now train models.
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
