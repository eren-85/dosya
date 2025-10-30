// src/ControlPanel.tsx
import React, { useState } from "react";
import { postJSON, getJSON } from "./api";

export default function ControlPanel() {
  const [symbols, setSymbols] = useState("BTCUSDT,ETHUSDT");
  const [interval, setInterval] = useState("1h");
  const [market, setMarket] = useState<"spot" | "futures">("futures");
  const [timeframes, setTimeframes] = useState("1h,4h,1d");
  const [parquet, setParquet] = useState(true);
  const [allTime, setAllTime] = useState(true);
  const [log, setLog] = useState("");

  const appendLog = (s: string) =>
    setLog((prev) => (prev ? prev + "\n" + s : s));

  async function runDownload() {
    setLog("");
    appendLog("➡️ /download starting...");
    try {
      const data = await postJSON("/download", {
        symbols, interval, market, parquet, all_time: allTime,
      });
      appendLog(data.stdout || JSON.stringify(data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  async function runSync() {
    setLog("");
    appendLog("➡️ /sync starting...");
    try {
      const data = await postJSON("/sync", {
        symbols, interval, market, parquet,
      });
      appendLog(data.stdout || JSON.stringify(data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  async function runTrain() {
    setLog("");
    appendLog("➡️ /train starting...");
    try {
      const data = await postJSON("/train", { symbols, timeframes });
      appendLog(data.stdout || JSON.stringify(data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  async function runAnalyze() {
    setLog("");
    appendLog("➡️ /analyze starting...");
    try {
      const data = await postJSON("/analyze", { symbols, timeframes });
      appendLog("IDs / result:");
      appendLog(JSON.stringify(data.result || data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  async function runLs() {
    setLog("");
    try {
      const data = await getJSON("/ls?limit=10");
      appendLog(data.stdout || JSON.stringify(data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  async function runWatch() {
    setLog("");
    appendLog("➡️ /watch starting...");
    const ids = prompt("Comma-separated task IDs:");
    if (!ids) return;
    try {
      const data = await postJSON("/watch", { ids, print_result: true });
      appendLog(data.stdout || JSON.stringify(data, null, 2));
    } catch (e:any) {
      appendLog("❌ " + e.message);
    }
  }

  return (
    <div style={{ padding: 16, display: "grid", gap: 16 }}>
      <h2>Sigma Control Panel</h2>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))" }}>
        <label>
          <div>Symbols (comma separated)</div>
          <input value={symbols} onChange={e=>setSymbols(e.target.value)} />
        </label>
        <label>
          <div>Interval (for download/sync)</div>
          <select value={interval} onChange={e=>setInterval(e.target.value)}>
            {["5m","15m","30m","1h","4h","1d","1w","1M"].map(t=>(
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
        <label>
          <div>Market</div>
          <select value={market} onChange={e=>setMarket(e.target.value as any)}>
            <option value="spot">spot</option>
            <option value="futures">futures</option>
          </select>
        </label>
        <label>
          <div>Timeframes (for train/analyze)</div>
          <input value={timeframes} onChange={e=>setTimeframes(e.target.value)} />
        </label>
        <label>
          <input type="checkbox" checked={parquet} onChange={e=>setParquet(e.target.checked)} /> save Parquet
        </label>
        <label>
          <input type="checkbox" checked={allTime} onChange={e=>setAllTime(e.target.checked)} /> ALL-TIME (download)
        </label>
      </div>

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
        <button onClick={runDownload}>Download</button>
        <button onClick={runSync}>Sync</button>
        <button onClick={runTrain}>Train</button>
        <button onClick={runAnalyze}>Analyze</button>
        <button onClick={runLs}>List IDs</button>
        <button onClick={runWatch}>Watch</button>
      </div>

      <textarea readOnly value={log} rows={18} style={{ width: "100%", fontFamily: "monospace" }} />
    </div>
  );
}
