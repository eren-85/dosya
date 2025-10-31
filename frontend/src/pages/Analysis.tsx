/**
 * Analysis Page
 *
 * AI-powered market analysis with OpenAI
 * - Real-time market analysis
 * - Technical indicators + On-chain data
 * - Trading signals (LONG/SHORT/WAIT)
 * - Risk assessment
 * - Quick analysis chat
 */

import React, { useState } from "react";

// Analysis result structure (from OpenAI)
interface AnalysisResult {
  symbol: string;
  timeframe: string;
  status: string;
  analysis?: {
    market_bias?: string;
    confidence?: number;
    summary?: string;
    technical_analysis?: any;
    smart_money?: any;
    on_chain_insights?: any;
    trading_signal?: {
      action: string;
      entry_price?: number;
      stop_loss?: number;
      take_profit_1?: number;
      take_profit_2?: number;
      risk_reward_ratio?: number;
    };
    risk_assessment?: any;
    conclusion?: string;
  };
  error?: string;
  timestamp: string;
}

export default function Analysis() {
  // Form state
  const [symbols, setSymbols] = useState("BTCUSDT,ETHUSDT");
  const [timeframes, setTimeframes] = useState("1H,4H,1D");
  const [mode, setMode] = useState<"oneshot" | "continuous">("oneshot");
  const [useOpenAI, setUseOpenAI] = useState(true);

  // Quick analysis state
  const [quickSymbol, setQuickSymbol] = useState("BTCUSDT");
  const [quickQuestion, setQuickQuestion] = useState("");
  const [quickResult, setQuickResult] = useState("");

  // Results state
  const [results, setResults] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [quickLoading, setQuickLoading] = useState(false);

  /**
   * Full market analysis
   */
  const handleAnalyze = async () => {
    setLoading(true);
    setResults([]);

    const symbolList = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    const timeframeList = timeframes
      .split(",")
      .map((t) => t.trim().toUpperCase())
      .filter((t) => t.length > 0);

    if (symbolList.length === 0 || timeframeList.length === 0) {
      alert("Please provide symbols and timeframes");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: symbolList,
          timeframes: timeframeList,
          mode,
          use_openai: useOpenAI,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setResults(data.results || []);
    } catch (error: any) {
      alert(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Quick analysis
   */
  const handleQuickAnalysis = async () => {
    if (!quickSymbol.trim()) {
      alert("Please provide a symbol");
      return;
    }

    setQuickLoading(true);
    setQuickResult("");

    try {
      const response = await fetch("/api/analysis/quick", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: quickSymbol.trim().toUpperCase(),
          question: quickQuestion.trim() || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setQuickResult(data.analysis || "No analysis available");
    } catch (error: any) {
      setQuickResult(`Error: ${error.message}`);
    } finally {
      setQuickLoading(false);
    }
  };

  /**
   * Get color for market bias
   */
  const getBiasColor = (bias?: string) => {
    if (!bias) return "#666";
    if (bias.toLowerCase().includes("bullish")) return "#00aa00";
    if (bias.toLowerCase().includes("bearish")) return "#ff4444";
    return "#ff9800";
  };

  /**
   * Get color for trading action
   */
  const getActionColor = (action?: string) => {
    if (!action) return "#666";
    if (action === "LONG") return "#00aa00";
    if (action === "SHORT") return "#ff4444";
    return "#ff9800";
  };

  return (
    <div style={{ padding: 24, maxWidth: 1400, margin: "0 auto" }}>
      <h1>🤖 AI Market Analysis</h1>
      <p style={{ color: "#666" }}>
        Real-time market analysis powered by OpenAI GPT-4
      </p>

      {/* ============================================ */}
      {/* Full Analysis Form */}
      {/* ============================================ */}
      <div
        style={{
          background: "#f5f5f5",
          padding: 24,
          borderRadius: 8,
          marginTop: 24,
        }}
      >
        <h3 style={{ marginTop: 0 }}>Full Market Analysis</h3>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: 16,
          }}
        >
          {/* Symbols */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Symbols (comma-separated)
            </label>
            <input
              type="text"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="BTCUSDT,ETHUSDT,SOLUSDT"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>

          {/* Timeframes */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Timeframes (comma-separated)
            </label>
            <input
              type="text"
              value={timeframes}
              onChange={(e) => setTimeframes(e.target.value)}
              placeholder="1H,4H,1D"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>

          {/* Mode */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Analysis Mode
            </label>
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value as "oneshot" | "continuous")}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            >
              <option value="oneshot">One-shot (Single analysis)</option>
              <option value="continuous">Continuous (Real-time updates)</option>
            </select>
          </div>
        </div>

        {/* OpenAI Toggle */}
        <div style={{ marginTop: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={useOpenAI}
              onChange={(e) => setUseOpenAI(e.target.checked)}
            />
            <span style={{ fontWeight: 600 }}>
              Use OpenAI GPT-4 for AI-powered insights {useOpenAI && "✅"}
            </span>
          </label>
        </div>

        {/* Analyze Button */}
        <div style={{ marginTop: 24 }}>
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              padding: "12px 32px",
              background: loading ? "#ccc" : "#0066ff",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Analyzing..." : "🚀 Analyze Markets"}
          </button>
        </div>
      </div>

      {/* ============================================ */}
      {/* Analysis Results */}
      {/* ============================================ */}
      {results.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>Analysis Results ({results.length})</h3>

          {results.map((result, idx) => (
            <div
              key={idx}
              style={{
                background: "#fff",
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: 20,
                marginBottom: 16,
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 16,
                  paddingBottom: 12,
                  borderBottom: "2px solid #eee",
                }}
              >
                <div>
                  <h3 style={{ margin: 0 }}>
                    {result.symbol} ({result.timeframe})
                  </h3>
                  <span style={{ fontSize: 12, color: "#666" }}>
                    {new Date(result.timestamp).toLocaleString()}
                  </span>
                </div>
                <div
                  style={{
                    padding: "6px 16px",
                    borderRadius: 20,
                    background:
                      result.status === "success" ? "#e7f8e7" : "#ffe7e7",
                    color: result.status === "success" ? "#00aa00" : "#ff4444",
                    fontWeight: 600,
                    fontSize: 14,
                  }}
                >
                  {result.status.toUpperCase()}
                </div>
              </div>

              {/* Error */}
              {result.error && (
                <div
                  style={{
                    background: "#ffe7e7",
                    color: "#cc0000",
                    padding: 16,
                    borderRadius: 6,
                    fontSize: 14,
                    lineHeight: 1.6,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  ❌ <strong>Error:</strong>
                  <div style={{ marginTop: 8 }}>
                    {result.error}
                  </div>
                </div>
              )}

              {/* No Analysis Data Warning */}
              {!result.error && !result.analysis && (
                <div
                  style={{
                    background: "#fff3cd",
                    color: "#856404",
                    padding: 16,
                    borderRadius: 6,
                    fontSize: 14,
                    lineHeight: 1.6,
                  }}
                >
                  ⚠️ <strong>No analysis data available</strong>
                  <div style={{ marginTop: 8 }}>
                    The analysis completed but returned no data. This might indicate:
                    <ul style={{ marginTop: 8, marginBottom: 0 }}>
                      <li>OpenAI API key is not configured</li>
                      <li>The model returned an unexpected response format</li>
                      <li>Network connectivity issues</li>
                    </ul>
                    Please check your .env file and backend logs for more details.
                  </div>
                </div>
              )}

              {/* Analysis */}
              {result.analysis && (
                <>
                  {/* Market Bias & Confidence */}
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns: "1fr 1fr",
                      gap: 16,
                      marginBottom: 20,
                    }}
                  >
                    <div
                      style={{
                        background: "#f8f8f8",
                        padding: 16,
                        borderRadius: 8,
                      }}
                    >
                      <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>
                        Market Bias
                      </div>
                      <div
                        style={{
                          fontSize: 24,
                          fontWeight: 700,
                          color: getBiasColor(result.analysis.market_bias),
                          textTransform: "uppercase",
                        }}
                      >
                        {result.analysis.market_bias || "N/A"}
                      </div>
                    </div>

                    <div
                      style={{
                        background: "#f8f8f8",
                        padding: 16,
                        borderRadius: 8,
                      }}
                    >
                      <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>
                        Confidence
                      </div>
                      <div style={{ fontSize: 24, fontWeight: 700, color: "#0066ff" }}>
                        {result.analysis.confidence !== undefined
                          ? `${result.analysis.confidence}%`
                          : "N/A"}
                      </div>
                    </div>
                  </div>

                  {/* Summary */}
                  {result.analysis.summary && (
                    <div style={{ marginBottom: 20 }}>
                      <h4 style={{ marginBottom: 8 }}>📊 Summary</h4>
                      <div
                        style={{
                          background: "#e7f3ff",
                          padding: 12,
                          borderRadius: 6,
                          fontSize: 14,
                          lineHeight: 1.6,
                        }}
                      >
                        {result.analysis.summary}
                      </div>
                    </div>
                  )}

                  {/* Trading Signal */}
                  {result.analysis.trading_signal && (
                    <div style={{ marginBottom: 20 }}>
                      <h4 style={{ marginBottom: 8 }}>🎯 Trading Signal</h4>
                      <div
                        style={{
                          background: "#f8f8f8",
                          padding: 16,
                          borderRadius: 8,
                        }}
                      >
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                            gap: 12,
                          }}
                        >
                          <div>
                            <div style={{ fontSize: 12, color: "#666" }}>Action</div>
                            <div
                              style={{
                                fontSize: 18,
                                fontWeight: 700,
                                color: getActionColor(
                                  result.analysis.trading_signal.action
                                ),
                              }}
                            >
                              {result.analysis.trading_signal.action}
                            </div>
                          </div>

                          {result.analysis.trading_signal.entry_price && (
                            <div>
                              <div style={{ fontSize: 12, color: "#666" }}>Entry</div>
                              <div style={{ fontSize: 16, fontWeight: 600 }}>
                                ${result.analysis.trading_signal.entry_price.toFixed(2)}
                              </div>
                            </div>
                          )}

                          {result.analysis.trading_signal.stop_loss && (
                            <div>
                              <div style={{ fontSize: 12, color: "#666" }}>Stop Loss</div>
                              <div style={{ fontSize: 16, fontWeight: 600, color: "#ff4444" }}>
                                ${result.analysis.trading_signal.stop_loss.toFixed(2)}
                              </div>
                            </div>
                          )}

                          {result.analysis.trading_signal.take_profit_1 && (
                            <div>
                              <div style={{ fontSize: 12, color: "#666" }}>TP1</div>
                              <div style={{ fontSize: 16, fontWeight: 600, color: "#00aa00" }}>
                                ${result.analysis.trading_signal.take_profit_1.toFixed(2)}
                              </div>
                            </div>
                          )}

                          {result.analysis.trading_signal.take_profit_2 && (
                            <div>
                              <div style={{ fontSize: 12, color: "#666" }}>TP2</div>
                              <div style={{ fontSize: 16, fontWeight: 600, color: "#00aa00" }}>
                                ${result.analysis.trading_signal.take_profit_2.toFixed(2)}
                              </div>
                            </div>
                          )}

                          {result.analysis.trading_signal.risk_reward_ratio && (
                            <div>
                              <div style={{ fontSize: 12, color: "#666" }}>Risk/Reward</div>
                              <div style={{ fontSize: 16, fontWeight: 600, color: "#0066ff" }}>
                                1:{result.analysis.trading_signal.risk_reward_ratio.toFixed(2)}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Conclusion */}
                  {result.analysis.conclusion && (
                    <div style={{ marginBottom: 20 }}>
                      <h4 style={{ marginBottom: 8 }}>💡 Conclusion</h4>
                      <div
                        style={{
                          background: "#fff3cd",
                          padding: 12,
                          borderRadius: 6,
                          fontSize: 14,
                          lineHeight: 1.6,
                        }}
                      >
                        {result.analysis.conclusion}
                      </div>
                    </div>
                  )}

                  {/* Raw Data (Collapsible) */}
                  <details style={{ marginTop: 16 }}>
                    <summary
                      style={{
                        cursor: "pointer",
                        fontWeight: 600,
                        fontSize: 14,
                        color: "#0066ff",
                      }}
                    >
                      View Raw Analysis Data
                    </summary>
                    <pre
                      style={{
                        background: "#1e1e1e",
                        color: "#00ff00",
                        padding: 12,
                        borderRadius: 6,
                        fontSize: 12,
                        overflow: "auto",
                        maxHeight: 400,
                        marginTop: 8,
                      }}
                    >
                      {JSON.stringify(result.analysis, null, 2)}
                    </pre>
                  </details>
                </>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ============================================ */}
      {/* Quick Analysis */}
      {/* ============================================ */}
      <div
        style={{
          background: "#f5f5f5",
          padding: 24,
          borderRadius: 8,
          marginTop: 32,
        }}
      >
        <h3 style={{ marginTop: 0 }}>⚡ Quick Analysis</h3>
        <p style={{ color: "#666", fontSize: 14 }}>
          Get a fast AI-powered text analysis for any symbol
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "2fr 3fr",
            gap: 12,
            marginTop: 16,
          }}
        >
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Symbol
            </label>
            <input
              type="text"
              value={quickSymbol}
              onChange={(e) => setQuickSymbol(e.target.value)}
              placeholder="BTCUSDT"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>

          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Question (Optional)
            </label>
            <input
              type="text"
              value={quickQuestion}
              onChange={(e) => setQuickQuestion(e.target.value)}
              placeholder="Is this a good entry point?"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>
        </div>

        <div style={{ marginTop: 16 }}>
          <button
            onClick={handleQuickAnalysis}
            disabled={quickLoading}
            style={{
              padding: "12px 32px",
              background: quickLoading ? "#ccc" : "#00aa00",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: quickLoading ? "not-allowed" : "pointer",
            }}
          >
            {quickLoading ? "Analyzing..." : "⚡ Quick Analyze"}
          </button>
        </div>

        {quickResult && (
          <div
            style={{
              marginTop: 16,
              background: "#fff",
              padding: 16,
              borderRadius: 8,
              border: "1px solid #ddd",
              fontSize: 14,
              lineHeight: 1.8,
              whiteSpace: "pre-wrap",
            }}
          >
            {quickResult}
          </div>
        )}
      </div>

      {/* ============================================ */}
      {/* Info Panel */}
      {/* ============================================ */}
      <div
        style={{
          marginTop: 24,
          padding: 16,
          background: "#e7f3ff",
          borderRadius: 8,
          fontSize: 14,
          color: "#000",
        }}
      >
        <h4 style={{ marginTop: 0, color: "#000" }}>🤖 AI Analysis Features:</h4>
        <ul style={{ marginBottom: 0, color: "#000" }}>
          <li>
            <strong>Market Bias:</strong> Bullish, Bearish, or Neutral sentiment
          </li>
          <li>
            <strong>Confidence Score:</strong> AI confidence level (0-100%)
          </li>
          <li>
            <strong>Trading Signals:</strong> Entry, Stop Loss, Take Profit levels
          </li>
          <li>
            <strong>Technical Analysis:</strong> RSI, MACD, Moving Averages, Bollinger Bands
          </li>
          <li>
            <strong>On-Chain Data:</strong> Exchange netflow, whale activity (BTC only)
          </li>
          <li>
            <strong>Risk Assessment:</strong> Risk level and position sizing recommendations
          </li>
          <li>
            <strong>Quick Analysis:</strong> Fast text-based insights and answers to your questions
          </li>
        </ul>
      </div>
    </div>
  );
}
