import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

export default function Calculate() {
  const [timestamp, setTimestamp] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("");
  const [symbol, setSymbol] = useState("");

  const [response, setResponse] = useState(null); // holds full analyzer response: { ok, request_id, fills, metrics }
  const [msg, setMsg] = useState("");

  async function run(e) {
    e.preventDefault();
    setMsg("");
    try {
      const r = await calcPost({
        timestamp,
        price,
        quantity,
        side,
        symbol,
        request: "Analyze", // later: switch to Estimate where needed
      });
      setResponse(r);
      setMsg(r?.ok ? "✅ calculated" : "❌ not ok");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  async function save() {
    if (!response?.metrics || !response?.fills) {
      setMsg("No calculation to save");
      return;
    }
    try {
      const payload = {
        fill: { ...response.fills, result: "SUCCESS" }, // adds result along with mode from analyzer
        metrics: response.metrics,
      };
      const r = await apiPost("/v1/fills", payload);
      setMsg(`✅ saved (fill_id: ${r.fill_id})`);
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  return (
    <div>
      <h2>Calculate</h2>
      <form onSubmit={run} className="form">
        <input placeholder="timestamp" value={timestamp} onChange={(e) => setTimestamp(e.target.value)} required />
        <input placeholder="price" value={price} onChange={(e) => setPrice(e.target.value)} required />
        <input placeholder="quantity" value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
        <input placeholder="side buy/sell" value={side} onChange={(e) => setSide(e.target.value)} required />
        <input placeholder="symbol" value={symbol} onChange={(e) => setSymbol(e.target.value)} required />
        <div style={{ display: "flex", gap: 8 }}>
          <button type="submit">Run</button>
        </div>
      </form>

      {response?.metrics && (
        <div style={{ marginTop: 12 }}>
          <pre>{JSON.stringify(response.metrics, null, 2)}</pre>
          <button onClick={save}>Save to DB</button>
        </div>
      )}
      <div className="banner">{msg}</div>
    </div>
  );
}
