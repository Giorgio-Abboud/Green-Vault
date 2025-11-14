import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

function convertToEST(datetimeLocalValue) {
  if (!datetimeLocalValue) return null;
  const localDate = new Date(datetimeLocalValue);
  if (isNaN(localDate)) return null;
  const estString = localDate.toLocaleString("en-US", {
    timeZone: "America/New_York",
  });
  return new Date(estString).toISOString();
}

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
  const [isSaving, setIsSaving] = useState(false);
  const [hasSaved, setHasSaved] = useState(false);

  const baseInput =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const errorInput =
    "w-full rounded-lg border-2 border-red-500 bg-brand-card/60 px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/60 transition";
  const inputClass = (field) => (fieldErrors[field] ? errorInput : baseInput);

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
    setFieldErrors({});
    setHasSaved(false);

    const localErrors = {};
    const nPrice = parseFloat(price);
    const nQty = parseFloat(quantity);

    if (!timestamp) localErrors.timestamp = "Required";
    if (!Number.isFinite(nPrice)) localErrors.price = "Must be a number";
    if (!Number.isFinite(nQty)) localErrors.quantity = "Must be a number";
    if (!side) localErrors.side = "Required";
    if (!symbol) localErrors.symbol = "Required";

    if (Object.keys(localErrors).length > 0) {
      setFieldErrors(localErrors);
      setMetrics(null);
      setMsg("❌ Please fix the highlighted fields.");
      return;
    }

    try {
      const estISO = convertToEST(timestamp);
      if (!estISO) throw new Error("Invalid date");
      const payload = {
        timestamp: estISO,
        price: nPrice,
        quantity: nQty,
        side,
        symbol: symbol.toUpperCase(),
        request: mode,
      };
      const res = await calcPost(payload);
      setMetrics(res?.metrics || null);
      setMsg("✅ Calculated");
    } catch {
      setMetrics(null);
      setMsg("❌ Something went wrong");
    }
  }

  async function save() {
    if (!metrics) {
      setMsg("No metrics to save");
      return;
    }

    setIsSaving(true);
    setMsg("");
    setFieldErrors({});

    try {
      const estISO = convertToEST(timestamp);
      if (!estISO) {
        setFieldErrors({ timestamp: "Invalid EST time" });
        setIsSaving(false);
        return;
      }

      const parsedMetrics = {};
      for (const [k, v] of Object.entries(metrics)) {
        const m = typeof v === "string" ? v.match(/-?\d+(\.\d+)?/) : null;
        parsedMetrics[k] = m ? parseFloat(m[0]) : Number(v) || 0;
      }

      const payload = {
        fill: {
          timestamp: estISO,
          price: parseFloat(price),
          quantity: parseFloat(quantity),
          side,
          symbol: symbol.trim().toUpperCase(),
          mode: mode.toLowerCase(),
        },
        metrics: parsedMetrics,
      };

      await apiPost("/v1/fills", payload);
      setMsg("✅ Your fills and metrics were saved!");
      setHasSaved(true);
    } catch {
      setMsg("❌ Failed to save");
    } finally {
      setIsSaving(false);
    }
  }

  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <style>{`
        input[type="datetime-local"]::-webkit-calendar-picker-indicator {
          filter: invert(1);
          cursor: pointer;
        }
      `}</style>

      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Calculate</h2>

        <form onSubmit={run} className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            <div>
              <label className={labelCls}>Date & time (converted to EST)</label>
              <input
                className={inputClass("timestamp")}
                type="datetime-local"
                value={timestamp}
                onChange={(e) => setTimestamp(e.target.value)}
                name="timestamp"
              />
              {fieldErrors.timestamp && <p className="text-xs text-red-400 mt-1">{fieldErrors.timestamp}</p>}
            </div>

            <div>
              <label className={labelCls}>Price</label>
              <input
                className={inputClass("price")}
                placeholder="e.g. 100.50"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                name="price"
              />
              {fieldErrors.price && <p className="text-xs text-red-400 mt-1">{fieldErrors.price}</p>}
            </div>

            <div>
              <label className={labelCls}>Quantity</label>
              <input
                className={inputClass("quantity")}
                placeholder="e.g. 10"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                name="quantity"
              />
              {fieldErrors.quantity && <p className="text-xs text-red-400 mt-1">{fieldErrors.quantity}</p>}
            </div>

            <div>
              <label className={labelCls}>Side</label>
              <select
                className={inputClass("side")}
                value={side}
                onChange={(e) => setSide(e.target.value)}
                name="side"
              >
                <option value="">Select side</option>
                <option value="buy">buy</option>
                <option value="sell">sell</option>
              </select>
              {fieldErrors.side && <p className="text-xs text-red-400 mt-1">{fieldErrors.side}</p>}
            </div>

            <div className="md:col-span-2">
              <label className={labelCls + " flex items-center gap-2"}>
                Symbol
                <div className="group relative cursor-pointer">
                  <div className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-brand-border text-[10px] text-gray-300">
                    ?
                  </div>
                  <div className="absolute left-6 top-0 z-10 hidden w-44 rounded-lg border border-brand-border bg-brand-card/95 p-3 text-xs text-gray-200 shadow-lg group-hover:block">
                    Stock ticker symbol. Example: AAPL, TSLA, NVDA
                  </div>
                </div>
              </label>
              <input
                className={inputClass("symbol")}
                placeholder="e.g. AAPL"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                name="symbol"
              />
              {fieldErrors.symbol && <p className="text-xs text-red-400 mt-1">{fieldErrors.symbol}</p>}

              <div className="mt-1">
                <a
                  href="https://www.nasdaq.com/market-activity/stocks/screener"
                  target="_blank"
                  className="text-brand-accent underline text-sm hover:brightness-110"
                >
                  Supported symbols
                </a>
              </div>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode("Analyze")}
                className={mode === "Analyze" ? btnPrimary : btnGhost}
              >
                Analyze
              </button>
              <button
                type="button"
                onClick={() => setMode("Estimate")}
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
              <h3 className="text-lg font-medium flex items-center gap-2">
                <span className="text-brand-accent">⚙️</span> Result Metrics
              </h3>

              {!isSaving && !hasSaved && (
                <button onClick={save} className={btnPrimary}>
                  Save Fills And Metric
                </button>
              )}
              {isSaving && <span className="text-sm text-gray-300">Saving…</span>}
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
              {Object.entries(metrics).map(([k, v]) => (
                <div
                  key={k}
                  className="flex items-center justify-between rounded-lg border border-brand-border bg-black/30 px-4 py-3 text-sm text-gray-200"
                >
                  <span className="capitalize">{k.replace(/_/g, " ")}</span>
                  <span className="font-semibold text-emerald-400">{v}</span>
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
