import React, { useState } from "react";
import { apiPost } from "../api";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");

  const inputCls =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const labelCls = "text-sm text-gray-300";
  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    try {
      await apiPost("/v1/users", { email, name, last_name: lastName, password });
      setMsg("✅ Your profile was successfully created!");
    } catch (err) {
      setMsg(`❌ ${err.message}`);
    }
  }

  const isOk = msg.startsWith("✅");
  const isErr = msg.startsWith("❌");

  return (
    <div className="min-h-screen bg-brand-bg text-gray-100">
      <div className="mx-auto max-w-md px-4 py-10">
        <div className="rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft">
          <h2 className="text-xl font-semibold tracking-tight mb-4">Sign up</h2>

          <form onSubmit={submit} className="space-y-4">
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

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className={labelCls}>First name</label>
                <input
                  className={inputCls}
                  placeholder="First name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
              <div>
                <label className={labelCls}>Last name</label>
                <input
                  className={inputCls}
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </div>
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
              Create account
            </button>
          </form>

          {msg && (
            <div
              className={[
                "mt-4 rounded-lg border px-4 py-3 text-sm",
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
    </div>
  );
}
