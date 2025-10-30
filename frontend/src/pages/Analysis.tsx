// D:\3\frontend\src\pages\Analysis.tsx
import React, { useState } from "react";
import { ping, download, sync } from "../api/ops";

export default function Analysis() {
  const [out, setOut] = useState<string>("");

  return (
    <div style={{ padding: 16 }}>
      <h2>Analysis (Ops Test)</h2>
      <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
        <button
          onClick={async () => {
            try {
              const r = await ping();
              setOut(JSON.stringify(r, null, 2));
            } catch (e: any) {
              setOut(e.message);
            }
          }}
        >
          Ping
        </button>
        <button
          onClick={async () => {
            try {
              const r = await download({
                symbols: ["BTCUSDT"],
                interval: "1h",
                market: "futures",
                all_time: true,
                parquet: true,
              });
              setOut(r.stdout || JSON.stringify(r, null, 2));
            } catch (e: any) {
              setOut(e.message);
            }
          }}
        >
          Download (BTCUSDT 1h futures)
        </button>
        <button
          onClick={async () => {
            try {
              const r = await sync({
                symbols: ["BTCUSDT", "ETHUSDT"],
                interval: "4h",
                market: "spot",
                parquet: true,
              });
              setOut(r.stdout || JSON.stringify(r, null, 2));
            } catch (e: any) {
              setOut(e.message);
            }
          }}
        >
          Sync (BTC,ETH 4h spot)
        </button>
      </div>
      <pre style={{ background: "#111", color: "#0f0", padding: 12, borderRadius: 8, maxHeight: 400, overflow: "auto" }}>
        {out}
      </pre>
    </div>
  );
}
