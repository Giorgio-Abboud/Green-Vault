import React, { useState } from "react";
import { apiPost } from "../api";
import { useAuth } from "../auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const { refresh } = useAuth();

  const inputCls =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const labelCls = "text-sm text-gray-300";
  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    try {
      await apiPost("/v1/login", { email, password });
      await refresh();
      setMsg("✅ logged in");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-md px-4 py-10">
        <form
          onSubmit={submit}
          className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft"
        >
          <h2 className="text-xl font-semibold tracking-tight">Log in</h2>

          <div>
            <label className={labelCls}>Email</label>
            <input
              className={inputCls}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              type="email"
            />
          </div>

          <div>
            <label className={labelCls}>Password</label>
            <input
              className={inputCls}
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className={btn}>
            Log in
          </button>

          {msg && (
            <div
              className={[
                "rounded-lg border px-4 py-3 text-sm",
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
        </form>
      </div>
    </div>
  );
}
