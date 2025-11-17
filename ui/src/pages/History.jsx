import React, { useState } from "react";
import { apiGet } from "../api";

export default function History() {
  const [loading, setLoading] = useState(false);
  const [fills, setFills] = useState(null);
  const [userId, setUserId] = useState("");
  const [msg, setMsg] = useState("");
  const [symbol, setSymbol] = useState("");
  const [filterActive, setFilterActive] = useState(false);

  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft disabled:opacity-50 disabled:cursor-not-allowed";

  function applyFilter() {
    if (!symbol.trim()) {
      setMsg("Please enter a symbol to filter.");
      setFilterActive(false);
      return;
    }

    setMsg(`Filter applied: ${symbol.trim().toUpperCase()}`);
    setFilterActive(true);
  }

  function clearFilter() {
    setSymbol("");
    setFilterActive(false);
    setMsg("Filter cleared. Click 'List All' to refresh data.");
  }

  async function listAll() {
    setLoading(true);
    setMsg("");
    try {
      let endpoint = "/v1/history/data";

      if (filterActive && symbol.trim()) {
        endpoint = `/v1/history/data?symbol=${encodeURIComponent(
          symbol.trim()
        )}`;
      }

      const data = await apiGet(endpoint);

      const uid = data.user_id || "";
      const arr = Array.isArray(data.fills) ? data.fills : [];

      setUserId(uid);
      setFills(arr);

      if (arr.length === 0) {
        if (filterActive) {
          setMsg(`No trade data found for symbol "${symbol.trim()}"`);
        } else {
          setMsg("You don't have saved fills and metrics yet");
        }
      }
    } catch (err) {
      setFills([]);
      setMsg(err?.message || "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-4xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">
          Trade History
        </h2>

        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-gray-300">
                Use the filter if you want, then click List All to search.
              </p>
              {userId && (
                <p className="text-xs text-gray-400 mt-1">
                  User ID: <span className="font-mono">{userId}</span>
                </p>
              )}
            </div>

            <div className="flex items-center gap-3">
              <input
                className="rounded-lg px-3 py-2 text-sm bg-black/30 border border-brand-border text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-brand-accent"
                placeholder="Filter by Symbol (optional)"
                value={symbol}
                onChange={(e) => {
                  setSymbol(e.target.value.toUpperCase());
                  setFilterActive(false);
                }}
              />

              <button onClick={applyFilter} disabled={loading} className={btn}>
                Apply Filter
              </button>

              {filterActive && (
                <button
                  onClick={clearFilter}
                  disabled={loading}
                  className="inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-gray-500 text-white hover:brightness-110 transition shadow-soft"
                >
                  Clear Filter
                </button>
              )}

              <button onClick={listAll} disabled={loading} className={btn}>
                {loading ? "Loading..." : "List All"}
              </button>
            </div>
          </div>

          {msg && (
            <div className="mt-4 rounded-lg border border-brand-border bg-black/30 px-4 py-3 text-sm text-gray-200">
              {msg}
            </div>
          )}
        </div>

        {fills && fills.length > 0 && (
          <div className="space-y-4">
            {fills.map((fill) => {
              const metric = fill.Metric || fill.metric || {};
              return (
                <div
                  key={fill.ID || fill.id}
                  className="rounded-xl2 border border-brand-border bg-brand-card p-4 shadow-soft"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 border-b border-brand-border/60 pb-2 mb-3">
                    <div className="flex flex-col">
                      <span className="text-sm text-gray-400">Symbol</span>
                      <span className="text-lg font-semibold text-white">
                        {fill.Symbol || fill.symbol}
                      </span>
                    </div>
                    <div className="flex gap-6 text-sm text-gray-300">
                      <div>
                        <span className="block text-gray-400 text-xs">Side</span>
                        <span className="uppercase">
                          {fill.Side || fill.side}
                        </span>
                      </div>
                      <div>
                        <span className="block text-gray-400 text-xs">
                          Quantity
                        </span>
                        <span>{fill.Quantity || fill.quantity}</span>
                      </div>
                      <div>
                        <span className="block text-gray-400 text-xs">Price</span>
                        <span>{fill.Price || fill.price}</span>
                      </div>
                      <div>
                        <span className="block text-gray-400 text-xs">Mode</span>
                        <span>{fill.Mode || fill.mode}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm text-gray-200">
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">VWAP Slippage</div>
                      <div className="font-semibold">
                        {metric.VwapSlippage ?? metric.vwap_slippage ?? "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">
                        Implementation Shortfall
                      </div>
                      <div className="font-semibold">
                        {metric.Shortfall ?? metric.shortfall ?? "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">Effective Spread</div>
                      <div className="font-semibold">
                        {metric.EffectiveSpread ?? metric.effective_spread ?? "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">Realized Spread</div>
                      <div className="font-semibold">
                        {metric.RealizedSpread ?? metric.realized_spread ?? "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">Market Impact</div>
                      <div className="font-semibold">
                        {metric.MarketImpact ?? metric.market_impact ?? "—"}
                      </div>
                    </div>
                    <div className="rounded-lg border border-brand-border bg-black/30 px-3 py-2">
                      <div className="text-xs text-gray-400">Drift</div>
                      <div className="font-semibold">
                        {metric.Drift ?? metric.drift ?? "—"}
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-xs text-gray-400">
                    <div>
                      Timestamp: {fill.Timestamp || fill.timestamp || "Unknown time"}
                    </div>
                    <div>
                      Result: {fill.Result || fill.result || "Unknown result"}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
