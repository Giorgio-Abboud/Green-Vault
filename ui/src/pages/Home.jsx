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
            Trades are not simply good or bad, they each contain various components that influence the outcome of your 
            trade. GreenVault provides a clear way to see your performances so you can learn fast and improve faster.
          </p>

          <h3 className={subTitle}>The Three Cost Drivers</h3>
          <ul className={list}>
            <li><strong className="text-white">Spread:</strong> How much you paid to access liquidity.</li>
            <li><strong className="text-white">Timing:</strong> How the market moved while you executed the order.</li>
            <li><strong className="text-white">Impact:</strong> How much your trading permanently influences the future prices.</li>
          </ul>

          <h3 className={subTitle}>Metric Guide</h3>
          <p className={paragraph}>The values will be calculated in bps (1 bps = 0.01%).</p>

          <h4 className={subTitle}>VWAP Slippage</h4>
          <p className={paragraph}>
            The slippage between your trade price and the market’s volume-weighted average price (VWAP) over your 
            execution window. It tells you how your price compares to what other traders paid, on average, during that 
            same period. Positive slippage means a worse fill (you paid more on a buy or sold for less on a sell). 
            Negative slippage means a better fill (you paid less on a buy or sold for more on a sell).
          </p>

          <h4 className={subTitle}>Implementation Shortfall</h4>
          <p className={paragraph}>
            The cost of not getting filled instantly at the price when you started the trade. It measures the difference 
            between your execution price and the market price at your decision time. Positive shortfall means the 
            market moved against you (your fill was worse than the arrival price). Zero means you effectively matched 
            the arrival price. Negative means the market moved in your favor and you improved on the arrival price.
          </p>

          <h4 className={subTitle}>Effective Spread</h4>
          <p className={paragraph}>
            The difference between an execution price and the midpoint of the bid-ask spread. It reflects your immediate 
            trading cost at execution. Positive values mean you crossed more of the spread and paid more or received less
            than the mid (worse). Negative values mean you traded closer to or even better than the mid (better).
          </p>

          <h4 className={subTitle}>Realized Spread</h4>
          <p className={paragraph}>
            Compares your trade price to an approximate market price a few minutes after the trade. From the trader’s 
            point of view, it shows whether your price ended up looking good or bad once the market settled. Positive 
            values mean your trade looks worse than the later market price (you would have done better by waiting). 
            Negative values mean you traded at a better price than where the market was minutes later.
          </p>

          <h4 className={subTitle}>Market Impact</h4>
          <p className={paragraph}>
            The part of your implementation shortfall that comes from the price moving against you while you were 
            trading. This is the cost that results from moving the market price with your own trade. Large orders can 
            push prices up when buying or down when selling. Positive values mean the price moved against you during 
            the window. Negative values mean the price moved in your favor while you traded.
          </p>

          <h4 className={subTitle}>Drift</h4>
          <p className={paragraph}>
            The part of your implementation shortfall that comes from price movement after you finished trading, 
            essentially timing and luck. It shows whether the market kept moving against you or in your favor once your 
            order was done. Positive values mean the market drifted further against you after completion (bad timing). 
            Negative values mean the market later moved in your favor (good timing).
          </p>

          <h4 className={subTitle}>How to Read Combinations</h4>
          <p className={paragraph}>
            Different combinations result in different outcomes. For example, you buy a stock and VWAP slippage is
            +5 bps, but implementation shortfall is +40 bps. That combination means your execution vs the market was 
            fine, but your timing wasn’t ideal. Most of the cost came from the price moving against you before you got
            filled (your order fully going through), not from getting a bad price relative to other traders.
          </p>
        </div>
      </div>
    </div>
  );
}
