import React from "react";
import { useAuth } from "../auth";
import { apiPost } from "../api";

export default function Home() {
  const { user, refresh } = useAuth();

  async function logout() {
    try {
      await apiPost("/v1/logout", {});
      await refresh();
    } catch (err) {
      console.error(err);
    }
  }

  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  const sectionTitle = "text-xl font-semibold text-white mb-2";
  const paragraph = "text-gray-300 leading-relaxed";
  const subTitle = "text-lg font-medium text-brand-accent mt-6 mb-1";
  const list = "list-disc pl-6 space-y-1 text-gray-300";

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-3xl px-4 py-10">
        <h2 className="text-2xl font-semibold tracking-tight mb-6">Home</h2>

        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft mb-8">
          {user ? (
            <>
              <div className="text-gray-300">
                Signed in as{" "}
                <strong className="text-white">{user.name || user.email}</strong>
              </div>
              <button onClick={logout} className={`${btn} mt-4`}>
                Logout
              </button>
            </>
          ) : (
            <div className="text-gray-300">Not signed in</div>
          )}
        </div>

        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft space-y-4">
          <h3 className={sectionTitle}>Green Vault</h3>
          <p className={paragraph}>
            Trades are not simply good or bad — each contains multiple components that influence the
            outcome of your trade. Green Vault provides a clear way to see your performance so you can
            learn fast and improve faster.
          </p>

          <h3 className={subTitle}>The Three Cost Drivers</h3>
          <ul className={list}>
            <li><strong className="text-white">Spread:</strong> How much you paid to access liquidity.</li>
            <li><strong className="text-white">Timing:</strong> How the market moved while you executed the order.</li>
            <li><strong className="text-white">Impact:</strong> How much your trading permanently influences future prices.</li>
          </ul>

          <h3 className={subTitle}>Metric Guide</h3>
          <p className={paragraph}>Values are calculated in bps (1 bps = 0.01%).</p>

          <h4 className={subTitle}>VWAP Slippage</h4>
          <p className={paragraph}>
            Measures how your execution price compares to the market’s volume-weighted average price
            during your execution window. Positive slippage = worse fill. Negative slippage = better fill.
          </p>

          <h4 className={subTitle}>Implementation Shortfall</h4>
          <p className={paragraph}>
            The cost of not getting filled instantly at the arrival price. Positive = market moved
            against you. Zero = matched arrival. Negative = price improved in your favor.
          </p>

          <h4 className={subTitle}>Effective Spread</h4>
          <p className={paragraph}>
            Shows your immediate execution cost relative to the mid-price. Positive = worse (crossed
            the spread). Negative = better (closer to or better than mid).
          </p>

          <h4 className={subTitle}>Realized Spread</h4>
          <p className={paragraph}>
            Compares your trade price to the market a few minutes later. Positive = worse outcome
            after the fact. Negative = better outcome.
          </p>

          <h4 className={subTitle}>Market Impact</h4>
          <p className={paragraph}>
            The portion of shortfall caused by the price moving while you traded. Large trades can
            push prices up (buying) or down (selling). Positive = price moved against you. Negative =
            moved in your favor.
          </p>

          <h4 className={subTitle}>Drift</h4>
          <p className={paragraph}>
            Price movement after your trade finished. Positive = market drifted against you. Negative =
            drifted in your favor.
          </p>

          <h4 className={subTitle}>How to Read Combinations</h4>
          <p className={paragraph}>
            Different combinations highlight different issues. For example: if you buy a stock and
            VWAP slippage is +5 bps but implementation shortfall is +40 bps, your execution was fine,
            but your timing wasn’t. Most of the cost came from price movement before your order fully
            filled, not from paying a worse price than other traders.
          </p>
        </div>
      </div>
    </div>
  );
}
