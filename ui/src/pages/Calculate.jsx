import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

export default function Calculate() {
  const [timestamp, setTimestamp] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("");
  const [symbol, setSymbol] = useState("");
  const [mode, setMode] = useState("Analyze");
  const [metrics, setMetrics] = useState(null);
  const [msg, setMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

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

  function parseApiError(err) {
    let status = err?.status ?? err?.response?.status ?? null;
    let data = err?.data ?? err?.response?.data ?? undefined;
    const coerce = (x) => {
      if (!x) return undefined;
      if (typeof x !== "string") return x;
      try {
        return JSON.parse(x);
      } catch {
        return { error: x };
      }
    };
    if (data === undefined && (typeof err === "string" || typeof err?.message === "string")) {
      const raw = String(typeof err === "string" ? err : err.message).trim();
      const m = raw.match(/^(\d{3})\s+(.+)$/);
      if (m) {
        status = Number(m[1]);
        data = coerce(m[2]);
      } else {
        data = coerce(raw);
      }
    } else {
      data = coerce(data);
    }
    return { status, data };
  }

  async function run(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});
    try {
      const payload = {
        timestamp,
        price: Number.parseFloat(price),
        quantity: Number.parseInt(quantity, 10),
        side,
        symbol,
        request: mode,
      };
      const r = await calcPost(payload);
      setMetrics(r?.metrics || null);
      setMsg("✅ calculated");
    } catch (err) {
      const { status, data } = parseApiError(err);
      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors(fe);
        setMsg("❌ The information you entered doesn’t meet the requirements. Please fix the highlighted fields.");
        const order = ["timestamp", "price", "quantity", "side", "symbol"];
        const first = order.find((k) => fe[k]);
        if (first) {
          requestAnimationFrame(() => {
            document.querySelector(`[name="${first}"]`)?.focus();
          });
        }
        return;
      }
      setMsg(`❌ ${data?.error || err?.message || "Something went wrong"}`);
    }
  }

  async function save() {
    if (!metrics) {
      setMsg("No metrics to save");
      return;
    }
    try {
      const payload = {
        timestamp,
        price: Number.parseFloat(price),
        quantity: Number.parseInt(quantity, 10),
        side,
        symbol,
        request: mode,
      };
      await apiPost("/v1/fills", payload);
      setMsg("✅ Your fills and metrics were saved!");
    } catch (err) {
      const { data } = parseApiError(err);
      setMsg(`❌ ${data?.error || err?.message || "Something went wrong"}`);
    }
  }

  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Calculate</h2>
        <form
          onSubmit={run}
          className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Timestamp (RFC3339)</label>
              <input
                className={inputCls}
                placeholder="e.g. 2025-10-17T12:00:00Z"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                required
                name="timestamp"
              />
              {fieldErrors.timestamp && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.timestamp}</p>
              )}
            </div>
            <div>
              <label className={labelCls}>Price</label>
              <input
                className={inputCls}
                placeholder="e.g. 100.50"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
                name="price"
              />
              {fieldErrors.price && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.price}</p>
              )}
            </div>
            <div>
              <label className={labelCls}>Quantity</label>
              <input
                className={inputCls}
                placeholder="e.g. 2"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                required
                name="quantity"
              />
              {fieldErrors.quantity && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.quantity}</p>
              )}
            </div>
            <div>
              <label className={labelCls}>Side (buy/sell)</label>
              <input
                className={inputCls}
                placeholder="buy or sell"
                value={side}
                onChange={(e) => setSide(e.target.value)}
                required
                name="side"
              />
              {fieldErrors.side && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.side}</p>
              )}
            </div>
            <div className="md:col-span-2">
              <label className={labelCls}>Symbol</label>
              <input
                className={inputCls}
                placeholder="e.g. BTCUSD"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                required
                name="symbol"
              />
              {fieldErrors.symbol && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.symbol}</p>
              )}
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
              <h3 className="text-lg font-medium text-gray-100 flex items-center gap-2">
                <span className="text-brand-accent">⚙️</span> Result Metrics
              </h3>
              <button onClick={save} className={btnPrimary}>
                Save to DB
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
              {Object.entries(metrics).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-center justify-between rounded-lg border border-brand-border bg-black/30 px-4 py-3 text-sm text-gray-200 shadow-sm"
                >
                  <span className="capitalize tracking-tight text-gray-300">
                    {key.replace(/_/g, " ")}
                  </span>
                  <span className="font-semibold text-emerald-400">{value}</span>
                </div>
              ))}
            </div>
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

