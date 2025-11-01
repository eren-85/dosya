/**
 * AI Analysis Page
 * - Market scenarios with probabilities
 * - Market pulse & kill zones
 * - On-chain & derivatives data
 * - Alert system
 */

import React, { useState, useEffect } from 'react';
import { Activity, AlertCircle, TrendingUp, Clock, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api, ExtendedAnalysis } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';

export default function NewAnalysis() {
  const [analysis, setAnalysis] = useState<ExtendedAnalysis>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysis();
    const interval = setInterval(fetchAnalysis, 60000); // Update every 60s
    return () => clearInterval(interval);
  }, []);

  const fetchAnalysis = async () => {
    try {
      const data = await api.getExtendedAnalysis('BTCUSDT', '1h');
      setAnalysis(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96 w-full" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">AI Analysis</h1>
        <p className="text-muted-foreground">
          Advanced market intelligence and AI-generated scenarios
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="scenarios" className="w-full">
        <TabsList>
          <TabsTrigger value="scenarios">Scenarios</TabsTrigger>
          <TabsTrigger value="killzones">Kill Zones</TabsTrigger>
          <TabsTrigger value="pulse">Market Pulse</TabsTrigger>
        </TabsList>

        {/* Scenarios Tab */}
        <TabsContent value="scenarios" className="space-y-4 mt-6">
          {analysis.scenarios && analysis.scenarios.length > 0 ? (
            analysis.scenarios.map((scenario, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{scenario.name}</CardTitle>
                    <Badge variant={scenario.probability > 0.6 ? 'success' : 'default'}>
                      {(scenario.probability * 100).toFixed(0)}% probability
                    </Badge>
                  </div>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-3">
                    <div>
                      <div className="text-sm text-muted-foreground">Trigger Price</div>
                      <div className="text-lg font-semibold text-green-500">
                        ${scenario.trigger_price.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Invalidation</div>
                      <div className="text-lg font-semibold text-red-500">
                        ${scenario.invalidation_price.toLocaleString()}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm text-muted-foreground">Targets</div>
                      <div className="text-sm font-medium">
                        {scenario.targets.map((t, i) => (
                          <span key={i}>
                            ${t.toLocaleString()}{i < scenario.targets.length - 1 ? ', ' : ''}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Alert>
              <Activity className="h-4 w-4" />
              <AlertDescription>
                No scenarios available. Scenarios are generated based on current market conditions.
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>

        {/* Kill Zones Tab */}
        <TabsContent value="killzones" className="space-y-4 mt-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Asian Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.asian_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.asian_killzone.start} - {analysis.asian_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.asian_killzone.active ? 'success' : 'default'}>
                      {analysis.asian_killzone.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  London Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.london_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.london_killzone.start} - {analysis.london_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.london_killzone.active ? 'success' : 'default'}>
                      {analysis.london_killzone.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  New York Session
                </CardTitle>
              </CardHeader>
              <CardContent>
                {analysis.ny_killzone ? (
                  <>
                    <div className="text-sm text-muted-foreground mb-2">
                      {analysis.ny_killzone.start} - {analysis.ny_killzone.end} UTC
                    </div>
                    <Badge variant={analysis.ny_killzone.active ? 'success' : 'default'}>
                      {analysis.ny_killzone.active ? 'Active' : 'Inactive'}
                    </Badge>
                  </>
                ) : (
                  <div className="text-sm text-muted-foreground">No data</div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Market Pulse Tab */}
        <TabsContent value="pulse" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-5 h-5 text-primary" />
                Market Pulse
              </CardTitle>
              <CardDescription>AI-generated market sentiment analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {analysis.market_pulse ? (
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <p>{analysis.market_pulse}</p>
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Market pulse analysis is not available. This feature provides AI-generated
                  insights based on current market conditions.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alerts */}
      {analysis.alerts && analysis.alerts.length > 0 && (
        <div className="space-y-2">
          <h2 className="text-lg font-semibold">Active Alerts</h2>
          {analysis.alerts.map((alert) => (
            <Alert
              key={alert.id}
              variant={
                alert.type === 'critical' ? 'destructive' :
                alert.type === 'warning' ? 'warning' : 'default'
              }
            >
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>{alert.type.toUpperCase()}</AlertTitle>
              <AlertDescription>{alert.message}</AlertDescription>
            </Alert>
          ))}
        </div>
      )}
    </div>
  );
}
