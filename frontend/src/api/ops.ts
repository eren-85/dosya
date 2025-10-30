// D:\3\frontend\src\api\ops.ts
// Simple client for backend /api/ops endpoints

export type Market = "spot" | "futures";
export type Interval = "5m" | "15m" | "30m" | "1h" | "4h" | "1d" | "1w" | "1m";

export interface DownloadReq {
  symbols: string[];      // ["BTCUSDT", "ETHUSDT"]
  interval: Interval;     // "1h"
  market: Market;         // "futures" | "spot"
  all_time?: boolean;     // true → ALL-TIME indir
  parquet?: boolean;      // true → parquet de kaydet
}

export interface SyncReq {
  symbols: string[];      // ["BTCUSDT", "ETHUSDT"]
  interval: Interval;     // "4h"
  market: Market;         // "spot" | "futures"
  parquet?: boolean;      // true → parquet de güncelle
}

// .env veya .env.local içinde VITE_API_BASE=http://localhost:8000 olmalı
const BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

async function api<T = any>(
  path: string,
  init?: RequestInit & { parseText?: boolean }
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
  }
  if ((init as any)?.parseText) {
    // @ts-ignore
    return (await res.text()) as T;
  }
  return (await res.json()) as T;
}

export async function ping() {
  // GET /api/ops/ping → {"status":"ok","service":"ops"}
  return api<{ status: string; service: string }>("/api/ops/ping");
}

export async function download(body: DownloadReq) {
  // POST /api/ops/download → CLI çıktısını döndürüyor
  return api<{ ok: boolean; returncode: number; args: string[]; stdout: string; stderr?: string }>(
    "/api/ops/download",
    { method: "POST", body: JSON.stringify(body) }
  );
}

export async function sync(body: SyncReq) {
  // POST /api/ops/sync → CLI çıktısını döndürüyor
  return api<{ ok: boolean; returncode: number; args: string[]; stdout: string; stderr?: string }>(
    "/api/ops/sync",
    { method: "POST", body: JSON.stringify(body) }
  );
}
