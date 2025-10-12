import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

export default function Calculate() {
  const [timestamp, setTimestamp] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("buy");
  const [symbol, setSymbol] = useState("");
  const [mode, setMode] = useState("Analyze"); // Analyze | Estimate

  const [metrics, setMetrics] = useState(null);
  const [msg, setMsg] = useState("");

  // convert to RFC3339 if possible
  function toRFC3339(ts) {
    try {
      const date = new Date(ts);
      return date.toISOString();
    } catch {
      return ts; // fallback
    }
  }

  async function run(e) {
    e.preventDefault();
    setMsg("");
    try {
      const payload = {
        timestamp: toRFC3339(timestamp),
        price: parseFloat(price),
        quantity: parseInt(quantity),
        side,
        symbol: symbol.toUpperCase(),
        request: mode,
      };
      const r = await calcPost(payload);
      setMetrics(r?.metrics || null);
      setMsg("✅ calculated");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  async function save() {
    if (!metrics) {
      setMsg("No metrics to save");
      return;
    }
    try {
      const payload = {
        fill: {
          timestamp: toRFC3339(timestamp),
          price: parseFloat(price),
          quantity: parseInt(quantity),
          side,
          symbol: symbol.toUpperCase(),
          mode,
          result: "SUCCESS",
        },
        metrics,
        client_request_id: metrics.request_id || "",
      };
      await apiPost("/v1/fills", payload);
      setMsg("✅ Your fills and metrics were saved!");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  return (
    <div>
      <h2>Calculate</h2>
      <form onSubmit={run} className="form">
        <input
          type="datetime-local"
          placeholder="timestamp (RFC3339)"
          value={timestamp}
          onChange={(e) => setTimestamp(e.target.value)}
          required
        />
        <input
          type="number"
          placeholder="price"
          step="any"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          required
        />
        <input
          type="number"
          placeholder="quantity"
          step="1"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          required
        />
        <select value={side} onChange={(e) => setSide(e.target.value)}>
          <option value="buy">buy</option>
          <option value="sell">sell</option>
        </select>
        <input
          placeholder="symbol"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          required
        />

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button
            type="button"
            onClick={() => setMode("Analyze")}
            disabled={mode === "Analyze"}
          >
            Analyze
          </button>
          <button
            type="button"
            onClick={() => setMode("Estimate")}
            disabled={mode === "Estimate"}
          >
            Estimate
          </button>
          <button type="submit">Run</button>
        </div>
        <div style={{ marginTop: 4, opacity: 0.8 }}>
          Mode: <strong>{mode}</strong>
        </div>
      </form>

      {metrics && (
        <div style={{ marginTop: 12 }}>
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
          <button onClick={save}>Save to DB</button>
        </div>
      )}
      {msg && (
        <div className="banner" style={{ marginTop: 12 }}>
          {msg}
        </div>
      )}
    </div>
  );
}
