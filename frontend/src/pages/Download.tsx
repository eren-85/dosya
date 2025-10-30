/**
 * Download/Sync Page
 *
 * Download historical OHLCV data from Binance
 * Supports:
 * - Spot & Futures markets
 * - Multiple symbols
 * - Multiple timeframes
 * - All-time or date range
 * - CSV + Parquet formats
 * - Sync (resume from last candle)
 */

import React, { useState } from "react";
import { download, sync } from "../api/ops";

// Allowed timeframes
const INTERVALS = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "3d", "1w", "1M"];

export default function Download() {
  // Form state
  const [symbols, setSymbols] = useState("BTCUSDT,ETHUSDT");
  const [interval, setInterval] = useState<string>("1h");
  const [market, setMarket] = useState<"spot" | "futures">("futures");
  const [allTime, setAllTime] = useState(true);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [parquet, setParquet] = useState(true);

  // Output state
  const [log, setLog] = useState("");
  const [loading, setLoading] = useState(false);

  const appendLog = (msg: string) => {
    setLog((prev) => `${prev}${msg}\n`);
  };

  const clearLog = () => setLog("");

  /**
   * Download historical data
   */
  const handleDownload = async () => {
    clearLog();
    setLoading(true);
    appendLog("⏳ Starting download...\n");

    const symbolList = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    if (symbolList.length === 0) {
      appendLog("❌ Error: No symbols provided");
      setLoading(false);
      return;
    }

    try {
      const result = await download({
        symbols: symbolList,
        interval,
        market,
        all_time: allTime,
        start_date: !allTime && startDate ? startDate : undefined,
        end_date: !allTime && endDate ? endDate : undefined,
        parquet,
      });

      if (result.ok) {
        appendLog("✅ Download completed!");
        appendLog("\n--- Output ---");
        appendLog(result.stdout || "");
      } else {
        appendLog(`❌ Download failed (exit code: ${result.returncode})`);
        appendLog(result.stderr || "");
      }
    } catch (error: any) {
      appendLog(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Sync (resume) existing data
   */
  const handleSync = async () => {
    clearLog();
    setLoading(true);
    appendLog("⏳ Starting sync (resume)...\n");

    const symbolList = symbols
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter((s) => s.length > 0);

    if (symbolList.length === 0) {
      appendLog("❌ Error: No symbols provided");
      setLoading(false);
      return;
    }

    try {
      const result = await sync({
        symbols: symbolList,
        interval,
        market,
        parquet,
      });

      if (result.ok) {
        appendLog("✅ Sync completed!");
        appendLog("\n--- Output ---");
        appendLog(result.stdout || "");
      } else {
        appendLog(`❌ Sync failed (exit code: ${result.returncode})`);
        appendLog(result.stderr || "");
      }
    } catch (error: any) {
      appendLog(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: "0 auto" }}>
      <h1>📥 Download Historical Data</h1>
      <p style={{ color: "#666" }}>
        Download or sync OHLCV data from Binance (Spot/Futures)
      </p>

      {/* Form */}
      <div
        style={{
          background: "#f5f5f5",
          padding: 24,
          borderRadius: 8,
          marginTop: 24,
        }}
      >
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
              placeholder="BTCUSDT,ETHUSDT"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>

          {/* Interval */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Interval
            </label>
            <select
              value={interval}
              onChange={(e) => setInterval(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            >
              {INTERVALS.map((int) => (
                <option key={int} value={int}>
                  {int}
                </option>
              ))}
            </select>
          </div>

          {/* Market */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Market Type
            </label>
            <select
              value={market}
              onChange={(e) => setMarket(e.target.value as "spot" | "futures")}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            >
              <option value="spot">Spot</option>
              <option value="futures">Futures</option>
            </select>
          </div>
        </div>

        {/* Date Range */}
        <div style={{ marginTop: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={allTime}
              onChange={(e) => setAllTime(e.target.checked)}
            />
            <span style={{ fontWeight: 600 }}>Download All-Time</span>
          </label>

          {!allTime && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 16,
                marginTop: 12,
              }}
            >
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 13 }}>
                  Start Date
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: 4,
                    border: "1px solid #ccc",
                  }}
                />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 13 }}>
                  End Date
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    borderRadius: 4,
                    border: "1px solid #ccc",
                  }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Parquet Option */}
        <div style={{ marginTop: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={parquet}
              onChange={(e) => setParquet(e.target.checked)}
            />
            <span style={{ fontWeight: 600 }}>
              Save as Parquet (recommended for faster loading)
            </span>
          </label>
        </div>

        {/* Buttons */}
        <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
          <button
            onClick={handleDownload}
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
            {loading ? "Downloading..." : "📥 Download"}
          </button>

          <button
            onClick={handleSync}
            disabled={loading}
            style={{
              padding: "12px 32px",
              background: loading ? "#ccc" : "#00aa00",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "Syncing..." : "🔄 Sync (Resume)"}
          </button>

          <button
            onClick={clearLog}
            disabled={loading}
            style={{
              padding: "12px 32px",
              background: "#666",
              color: "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Clear Log
          </button>
        </div>
      </div>

      {/* Output Log */}
      <div style={{ marginTop: 24 }}>
        <h3>Output Log</h3>
        <pre
          style={{
            background: "#1e1e1e",
            color: "#00ff00",
            padding: 16,
            borderRadius: 8,
            fontSize: 13,
            fontFamily: "monospace",
            maxHeight: 500,
            overflow: "auto",
            whiteSpace: "pre-wrap",
            wordWrap: "break-word",
          }}
        >
          {log || "No output yet. Click Download or Sync to start."}
        </pre>
      </div>

      {/* Help Text */}
      <div
        style={{
          marginTop: 24,
          padding: 16,
          background: "#fff3cd",
          borderRadius: 8,
          fontSize: 14,
          color: "#000",
        }}
      >
        <h4 style={{ marginTop: 0, color: "#000" }}>💡 Tips:</h4>
        <ul style={{ marginBottom: 0, color: "#000" }}>
          <li>
            <strong>Download:</strong> Full historical data from start to end
          </li>
          <li>
            <strong>Sync:</strong> Resume from last downloaded candle (faster for updates)
          </li>
          <li>
            <strong>Parquet:</strong> Binary format, 5-10x faster to load than CSV
          </li>
          <li>
            <strong>All-Time:</strong> Downloads complete history (may take time for 1m/5m)
          </li>
          <li>
            Downloaded files saved to: <code>data/historical/</code>
          </li>
        </ul>
      </div>
    </div>
  );
}
