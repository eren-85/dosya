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
import { TIMEFRAMES, MarketType, COMMON_SYMBOLS } from '@/lib/constants';
import { api } from '@/lib/api';

export default function NewDownload() {
  const [symbols, setSymbols] = useState('BTCUSDT,ETHUSDT');
  const [intervals, setIntervals] = useState('1h,4h,1d');
  const [marketType, setMarketType] = useState<MarketType>('spot');
  const [allTime, setAllTime] = useState(false);
  const [loading, setLoading] = useState(false);
  const [log, setLog] = useState('');
  const [status, setStatus] = useState<'idle' | 'running' | 'success' | 'error'>('idle');

  // Progress tracking
  const [progress, setProgress] = useState(0);
  const [currentInterval, setCurrentInterval] = useState('');
  const [completedCount, setCompletedCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  const handleDownload = async () => {
    setLoading(true);
    setStatus('running');
    setLog('');
    setProgress(0);
    setCompletedCount(0);
    appendLog('⏳ Starting data download...\n');

    const symbolList = symbols.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    const intervalList = intervals.split(',').map(i => i.trim()).filter(i => i);

    if (symbolList.length === 0) {
      appendLog('❌ Error: No symbols provided');
      setStatus('error');
      setLoading(false);
      return;
    }

    if (intervalList.length === 0) {
      appendLog('❌ Error: No intervals provided');
      setStatus('error');
      setLoading(false);
      return;
    }

    setTotalCount(intervalList.length);

    appendLog(`📊 Market Type: ${marketType.toUpperCase()}\n`);
    appendLog(`🏦 Exchange: Binance\n`);
    appendLog(`💱 Symbols: ${symbolList.join(', ')}\n`);
    appendLog(`⏱️  Intervals: ${intervalList.join(', ')}\n`);
    appendLog(`📅 All-time: ${allTime ? 'Yes' : 'No'}\n\n`);

    let allSuccess = true;
    let totalDownloads = 0;
    let failedDownloads = 0;

    try {
      // Download data for each interval separately (backend expects single interval)
      for (let i = 0; i < intervalList.length; i++) {
        const interval = intervalList[i];
        setCurrentInterval(interval);
        appendLog(`\n📥 Downloading ${interval} data...\n`);

        try {
          const result = await api.downloadData({
            symbols: symbolList,
            interval: interval,
            market: marketType,
            all_time: allTime,
          });

          if (result.ok) {
            appendLog(`✅ ${interval} download completed successfully!\n`);
            if (result.stdout) {
              appendLog(`${result.stdout}\n`);
            }
            totalDownloads++;
          } else {
            appendLog(`❌ ${interval} download failed (code: ${result.returncode})\n`);
            if (result.stderr) {
              appendLog(`${result.stderr}\n`);
            }
            allSuccess = false;
            failedDownloads++;
          }
        } catch (intervalError: any) {
          appendLog(`❌ ${interval} error: ${intervalError.message}\n`);
          allSuccess = false;
          failedDownloads++;
        }

        // Update progress
        const completed = i + 1;
        setCompletedCount(completed);
        setProgress((completed / intervalList.length) * 100);

        // Small delay between requests
        if (i < intervalList.length - 1) {
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      }

      appendLog(`\n${'='.repeat(50)}\n`);
      appendLog(`✅ Completed: ${totalDownloads}/${intervalList.length} intervals\n`);
      if (failedDownloads > 0) {
        appendLog(`❌ Failed: ${failedDownloads} intervals\n`);
      }
      setStatus(allSuccess ? 'success' : 'error');
    } catch (error: any) {
      appendLog(`\n❌ Critical error: ${error.message}\n`);
      setStatus('error');
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

      {/* Progress Bar */}
      {loading && totalCount > 0 && (
        <Card className="border-primary/50">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Download Progress</span>
              <Badge variant="secondary" className="text-base">
                {completedCount}/{totalCount}
              </Badge>
            </CardTitle>
            <CardDescription>
              {currentInterval ? (
                <>Downloading <span className="font-semibold">{currentInterval}</span> data from Binance...</>
              ) : (
                'Initializing download...'
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground font-medium">Overall Progress</span>
                <span className="text-lg font-bold text-primary">{Math.round(progress)}%</span>
              </div>
              <div className="w-full h-4 bg-secondary rounded-full overflow-hidden border border-primary/20">
                <div
                  className="h-full bg-gradient-to-r from-primary to-pink-500 transition-all duration-500 ease-out relative"
                  style={{ width: `${progress}%` }}
                >
                  {/* Animated shimmer effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse" />
                </div>
              </div>
              {/* Progress details */}
              <div className="flex items-center justify-between text-xs text-muted-foreground pt-1">
                <span>
                  {completedCount > 0 ? `✅ ${completedCount} completed` : 'Starting...'}
                </span>
                <span>
                  {totalCount - completedCount > 0 ? `⏳ ${totalCount - completedCount} remaining` : 'Almost done!'}
                </span>
              </div>
            </div>

            {/* Current Status */}
            <div className="flex items-center gap-3 p-3 bg-primary/5 rounded-lg border border-primary/10">
              <Loader2 className="w-5 h-5 animate-spin text-primary flex-shrink-0" />
              <span className="text-sm">
                {currentInterval ? (
                  <>
                    Processing <span className="font-bold text-primary">{currentInterval}</span> interval...
                    {completedCount > 0 && (
                      <span className="text-muted-foreground ml-2">
                        ({completedCount} of {totalCount} intervals done)
                      </span>
                    )}
                  </>
                ) : (
                  'Preparing download...'
                )}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

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
