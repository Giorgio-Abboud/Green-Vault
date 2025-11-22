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
  const [review, setReview] = useState(null);
  const [msg, setMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

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

  const EST_OFFSET = "-04:00";

  function buildEstIsoFromLocal(value) {
    if (!value) throw new Error("Timestamp required");
    const trimmed = value.trim();
    const [datePart, rawTime] = trimmed.split("T");
    if (!datePart || !rawTime) throw new Error("Invalid datetime");

    let timePart = rawTime.replace(/(Z|[+-].*)$/, "");
    if (timePart.includes(".")) {
      timePart = timePart.split(".")[0];
    }

    const segments = timePart.split(":");
    if (segments.length < 2) throw new Error("Invalid time");
    while (segments.length < 3) {
      segments.push("00");
    }
    const normalizedTime = segments
      .slice(0, 3)
      .map((seg) => seg.padStart(2, "0"))
      .join(":");
    return `${datePart}T${normalizedTime}${EST_OFFSET}`;
  }

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
    if (
      data === undefined &&
      (typeof err === "string" || typeof err?.message === "string")
    ) {
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
    setReview(null);
    let local = {};
    const rawPrice = String(price ?? "").trim();
    const rawQty = String(quantity ?? "").trim();
    const priceValid = /^(\d+(\.\d+)?|\.\d+)$/.test(rawPrice);
    const qtyValid = /^\d+$/.test(rawQty);
    const nPrice = priceValid ? Number.parseFloat(rawPrice) : NaN;
    const nQty = qtyValid ? Number.parseFloat(rawQty) : NaN;
    if (!timestamp) local.timestamp = "Required";
    if (!priceValid || !Number.isFinite(nPrice)) local.price = "Must be a number";
    if (!qtyValid || !Number.isFinite(nQty)) local.quantity = "Must be a valid number";
    if (!side) local.side = "Required";
    if (!symbol) local.symbol = "Required";
    if (Object.keys(local).length) {
      setFieldErrors(local);
      setMetrics(null);
      setMsg(
        "Warning: The information you entered doesn't meet the requirements. Please fix the highlighted fields."
      );
      const order = ["timestamp", "price", "quantity", "side", "symbol"];
      const first = order.find((k) => local[k]);
      if (first)
        requestAnimationFrame(() => {
          document.querySelector(`[name="${first}"]`)?.focus();
        });
      return;
    }
    try {
      const tsIso = buildEstIsoFromLocal(timestamp);
      const payload = {
        timestamp: tsIso,
        price: nPrice,
        quantity: nQty,
        side,
        symbol,
        request: mode,
      };
      const r = await calcPost(payload);
      setMetrics(r?.metrics || null);
      setReview(r?.review || null);
      setMsg("calculated");
    } catch (err) {
      const { status, data } = parseApiError(err);
      setMetrics(null);
      setReview(null);
      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors(fe);
        setMsg(
          "Warning: The information you entered doesn't meet the requirements. Please fix the highlighted fields."
        );
        const order = ["timestamp", "price", "quantity", "side", "symbol"];
        const first = order.find((k) => fe[k]);
        if (first) {
          requestAnimationFrame(() => {
            document.querySelector(`[name="${first}"]`)?.focus();
          });
        }
        return;
      }
      setMsg(`Warning: ${data?.error || err?.message || "Something went wrong"}`);
    }
  }

  async function save() {
    if (!metrics) {
      setMsg("No metrics to save");
      return;
    }
    setMsg("");
    setFieldErrors({});

    const fe = {};
    let tsIso = "";
    try {
      tsIso = buildEstIsoFromLocal(timestamp);
    } catch {
      fe.timestamp = "must be valid RFC3339 datetime (e.g. 2025-10-12T14:00:00-04:00)";
    }

    const rawPrice = String(price ?? "").trim();
    const priceValid = /^(\d+(\.\d+)?|\.\d+)$/.test(rawPrice);
    const nPrice = priceValid ? Number.parseFloat(rawPrice) : NaN;
    if (!Number.isFinite(nPrice) || nPrice <= 0)
      fe.price = "must be a positive number";

    const rawQty = String(quantity ?? "").trim();
    const qtyValid = /^\d+$/.test(rawQty);
    const nQty = qtyValid ? Number.parseFloat(rawQty) : NaN;
    if (!Number.isFinite(nQty) || nQty <= 0 || !Number.isInteger(nQty))
      fe.quantity = "must be a positive integer";

    if (side !== "buy" && side !== "sell") fe.side = "must be 'buy' or 'sell'";

    const sym = String(symbol || "").trim();
    if (!/^[A-Z]+$/.test(sym))
      fe.symbol = "must contain only uppercase letters (A to Z), no spaces";

    if (Object.keys(fe).length) {
      setFieldErrors(fe);
      setMsg(
        "Warning: The information you entered doesn't meet the requirements. Please fix the highlighted fields."
      );
      const order = ["timestamp", "price", "quantity", "side", "symbol"];
      const first = order.find((k) => fe[k]);
      if (first)
        requestAnimationFrame(() => {
          document.querySelector(`[name="${first}"]`)?.focus();
        });
      return;
    }

    try {
      // Extract numeric prefix from each metric (e.g. "-141.25" from "-141.25 bps — text")
      const parsedMetrics = {};
      for (const [k, v] of Object.entries(metrics || {})) {
        if (typeof v === "string") {
          const m = v.match(/-?\d+(\.\d+)?/);
          parsedMetrics[k] = m ? parseFloat(m[0]) : 0;
        } else if (typeof v === "number") {
          parsedMetrics[k] = v;
        } else {
          parsedMetrics[k] = 0;
        }
      }
      const payload = {
        fill: {
          timestamp: tsIso,
          price: nPrice,
          quantity: nQty,
          side,
          symbol: sym,
          mode: mode.toLowerCase(),
        },
        metrics: parsedMetrics,
      };

      await apiPost("/v1/fills", payload);
      setMsg("calculated: Your fills and metrics were saved!");
    } catch (err) {
      let { status, data } = parseApiError(err);
      if (status === 422 && data && typeof data === "object") {
        const fe2 = data.field_errors || {};
        setFieldErrors(fe2);
        setMsg(
          "Warning: The information you entered doesn't meet the requirements. Please fix the highlighted fields."
        );
        const order = ["timestamp", "price", "quantity", "side", "symbol"];
        const first = order.find((k) => fe2[k]);
        if (first) {
          requestAnimationFrame(() => {
            document.querySelector(`[name="${first}"]`)?.focus();
          });
        }
        return;
      }
      setMsg(`Warning: ${data?.error || err?.message || "Something went wrong"}`);
    }
  }

  const isOk = msg.toLowerCase().startsWith("calculated");
  const isErr = msg.toLowerCase().startsWith("warning");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <style>{`
        input[type="datetime-local"]::-webkit-calendar-picker-indicator {
          filter: invert(1);
          cursor: pointer;
        }
        select { color: #f3f4f6; background-color: rgba(30,30,30,0.6); }
        option { background-color: #1e1e1e; color: #f3f4f6; }
      `}</style>
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Calculate</h2>

        <form
          onSubmit={run}
          className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-5 shadow-soft"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className={labelCls}>Date & time</label>
              <input
                className={inputClass("timestamp")}
                type="datetime-local"
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
                className={inputClass("price")}
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
                className={inputClass("quantity")}
                placeholder="e.g. 10"
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
              <label className={labelCls}>Side</label>
              <select
                className={inputClass("side")}
                value={side}
                onChange={(e) => setSide(e.target.value)}
                required
                name="side"
              >
                <option value="" disabled>
                  Select side
                </option>
                <option value="buy">buy</option>
                <option value="sell">sell</option>
              </select>
              {fieldErrors.side && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.side}</p>
              )}
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
                required
                name="symbol"
              />
              {fieldErrors.symbol && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.symbol}</p>
              )}

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
                <span className="text-brand-accent">Result</span>
              </h3>
              <button onClick={save} className={btnPrimary}>
                Save to DB
              </button>
            </div>
            {review && (
              <div className="mb-4 rounded-lg border border-brand-border bg-black/30 px-4 py-3 text-sm text-gray-200 shadow-sm space-y-2">
                <div className="text-base font-semibold text-gray-100">
                  {review.summary}
                </div>
                {review.axis_summary && (
                  <div className="text-xs text-gray-300">
                    Axes: {review.axis_summary}
                  </div>
                )}
              </div>
            )}
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
