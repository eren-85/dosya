/**
 * Training Page
 *
 * Train ML models on downloaded data
 * - Ensemble models (XGBoost, LightGBM, CatBoost)
 * - Deep learning (LSTM, Transformer)
 * - Reinforcement learning (PPO)
 */

import React, { useState } from "react";

export default function Training() {
  const [symbols, setSymbols] = useState("BTCUSDT,ETHUSDT");
  const [timeframes, setTimeframes] = useState("1h,4h,1d");
  const [modelType, setModelType] = useState<"ensemble" | "lstm" | "transformer" | "ppo">(
    "ensemble"
  );
  const [epochs, setEpochs] = useState(100);
  const [useGPU, setUseGPU] = useState(true);

  const [log, setLog] = useState("");
  const [loading, setLoading] = useState(false);

  const appendLog = (msg: string) => {
    setLog((prev) => `${prev}${msg}\n`);
  };

  const clearLog = () => setLog("");

  /**
   * Train model
   */
  const handleTrain = async () => {
    clearLog();
    setLoading(true);
    appendLog("⏳ Starting model training...\n");

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
      // Call backend train endpoint
      const response = await fetch("/api/ops/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbols: symbolList,
          timeframes: timeframes,
          model_type: modelType,
          epochs: epochs,
          device: useGPU ? "cuda" : "cpu",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const result = await response.json();

      if (result.ok) {
        appendLog("✅ Training completed!");
        appendLog("\n--- Output ---");
        appendLog(result.stdout || "");
      } else {
        appendLog(`❌ Training failed (exit code: ${result.returncode})`);
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
      <h1>🧠 Train ML Models</h1>
      <p style={{ color: "#666" }}>
        Train machine learning models on your downloaded data
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

          {/* Timeframes */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Timeframes
            </label>
            <input
              type="text"
              value={timeframes}
              onChange={(e) => setTimeframes(e.target.value)}
              placeholder="1h,4h,1d"
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            />
          </div>

          {/* Model Type */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Model Type
            </label>
            <select
              value={modelType}
              onChange={(e) => setModelType(e.target.value as any)}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 4,
                border: "1px solid #ccc",
                fontSize: 14,
              }}
            >
              <option value="ensemble">Ensemble (XGBoost + LightGBM + CatBoost)</option>
              <option value="lstm">LSTM (Deep Learning)</option>
              <option value="transformer">Transformer (Deep Learning)</option>
              <option value="ppo">PPO (Reinforcement Learning)</option>
            </select>
          </div>

          {/* Epochs */}
          <div>
            <label style={{ fontWeight: 600, display: "block", marginBottom: 8 }}>
              Epochs
            </label>
            <input
              type="number"
              value={epochs}
              onChange={(e) => setEpochs(Number(e.target.value))}
              min={10}
              max={1000}
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

        {/* GPU Option */}
        <div style={{ marginTop: 16 }}>
          <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={useGPU}
              onChange={(e) => setUseGPU(e.target.checked)}
            />
            <span style={{ fontWeight: 600 }}>
              Use GPU (CUDA) - RTX 4060 {useGPU && "✅"}
            </span>
          </label>
        </div>

        {/* Buttons */}
        <div style={{ marginTop: 24, display: "flex", gap: 12 }}>
          <button
            onClick={handleTrain}
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
            {loading ? "Training..." : "🚀 Start Training"}
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
        <h3>Training Log</h3>
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
          {log || "No output yet. Click Start Training to begin."}
        </pre>
      </div>

      {/* Model Info */}
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
        <h4 style={{ marginTop: 0, color: "#000" }}>📊 Model Information:</h4>
        <ul style={{ marginBottom: 0, color: "#000" }}>
          <li>
            <strong>Ensemble:</strong> Combines XGBoost, LightGBM, CatBoost for robust predictions
          </li>
          <li>
            <strong>LSTM:</strong> Recurrent neural network for sequence prediction (GPU recommended)
          </li>
          <li>
            <strong>Transformer:</strong> Attention-based model for pattern recognition (GPU required)
          </li>
          <li>
            <strong>PPO:</strong> Reinforcement learning for decision optimization (GPU required)
          </li>
          <li>
            Trained models saved to: <code>data/models/</code>
          </li>
          <li>
            <strong>GPU:</strong> RTX 4060 8GB with BF16 + TF32 optimizations
          </li>
        </ul>
      </div>
    </div>
  );
}
