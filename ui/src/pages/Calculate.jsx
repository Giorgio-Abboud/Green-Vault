import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

export default function Calculate() {
  const [timestamp, setTimestamp] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("");
  const [symbol, setSymbol] = useState("");
  const [mode, setMode] = useState("Analyze"); // Analyze | Estimate

  const [metrics, setMetrics] = useState(null);
  const [msg, setMsg] = useState("");

  // --- UI helpers (purely visual) ---
  const inputCls =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const labelCls = "text-sm text-gray-300";
  const btnBase =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed";
  const btnPrimary =
    `${btnBase} bg-brand-accent text-black hover:brightness-110 shadow-soft`;
  const btnGhost =
    `${btnBase} bg-brand-card/60 text-gray-200 border border-brand-border hover:border-brand-accent/50`;
  const badgeMode =
    "inline-flex items-center gap-2 rounded-md border border-brand-border bg-brand-card/80 px-2.5 py-1 text-xs text-gray-300";

  async function run(e) {
    e.preventDefault();
    setMsg("");
    try {
      const r = await calcPost({ timestamp, price, quantity, side, symbol, request: mode });
      // FastAPI returns { ok, request_id, fills, metrics }
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
        fill: { timestamp, price, quantity, side, symbol, mode, result: "SUCCESS" },
        metrics,
        client_request_id: metrics.request_id || "",
      };
      await apiPost("/v1/fills", payload); // returns { fill_id, metric_id } as data
      setMsg("✅ Your fills and metrics were saved!");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Calculate</h2>

        <form onSubmit={run} className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Timestamp (RFC3339)</label>
              <input
                className={inputCls}
                placeholder="e.g. 2025-10-17T12:00:00Z"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                required
              />
            </div>
            <div>
              <label className={labelCls}>Price</label>
              <input
                className={inputCls}
                placeholder="e.g. 100.50"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
              />
            </div>
            <div>
              <label className={labelCls}>Quantity</label>
              <input
                className={inputCls}
                placeholder="e.g. 2"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
              />
            </div>
            <div>
              <label className={labelCls}>Side (buy/sell)</label>
              <input
                className={inputCls}
                placeholder="buy or sell"
                value={side}
                onChange={(e) => setSide(e.target.value)}
                required
              />
            </div>
            <div className="md:col-span-2">
              <label className={labelCls}>Symbol</label>
              <input
                className={inputCls}
                placeholder="e.g. BTCUSD"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode("Analyze")}
                disabled={mode === "Analyze"}
                className={mode === "Analyze" ? btnPrimary : btnGhost}
              >
                Analyze
              </button>
              <button
                type="button"
                onClick={() => setMode("Estimate")}
                disabled={mode === "Estimate"}
                className={mode === "Estimate" ? btnPrimary : btnGhost}
              >
                Estimate
              </button>
            </div>
            <div className={badgeMode}>
              Mode: <strong className="text-white">{mode}</strong>
            </div>
            <div className="ml-auto">
              <button type="submit" className={btnPrimary}>
                Run
              </button>
            </div>
          </div>
        </form>

        {metrics && (
          <div className="mt-6 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-lg font-medium">Result</h3>
              <button onClick={save} className={btnPrimary}>
                Save to DB
              </button>
            </div>
            <pre className="max-h-[420px] overflow-auto rounded-lg bg-black/50 p-4 text-sm">
              {JSON.stringify(metrics, null, 2)}
            </pre>
          </div>
        )}

        {msg && (
          <div
            className={[
              "mt-6 rounded-lg border px-4 py-3 text-sm",
              isOk
                ? "border-emerald-600/40 bg-emerald-500/10 text-emerald-300"
                : isErr
                ? "border-red-600/40 bg-red-500/10 text-red-300"
                : "border-brand-border bg-brand-card/80 text-gray-300",
            ].join(" ")}
          >
            {msg}
          </div>
        )}
      </div>
    </div>
  );
}
