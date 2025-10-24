import React, { useState } from "react";
import { apiPost } from "../api";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const inputCls =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const labelCls = "text-sm text-gray-300";
  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    try {
      await apiPost("/v1/users", {
        email,
        name,
        last_name: lastName,
        password,
      });
      setMsg("✅ Your profile was successfully created!");
    } catch (err) {
      // ---- normalize error (works for object, axios-like, fetch-like, or plain string) ----
      let status = err?.status ?? err?.response?.status ?? null;
      let data = err?.data ?? err?.response?.data ?? undefined;

      if (!data && (typeof err === "string" || typeof err?.message === "string")) {
        const raw = String(typeof err === "string" ? err : err.message).trim();
        const m = raw.match(/^(\d{3})\s+(.+)$/); // e.g. "422 {...}"
        if (m) {
          status = Number(m[1]);
          const bodyStr = m[2];
          try { data = JSON.parse(bodyStr); } catch { data = { error: bodyStr }; }
        } else {
          try { data = JSON.parse(raw); } catch { data = { error: raw }; }
        }
      }
      if (typeof data === "string") {
        try { data = JSON.parse(data); } catch { data = { error: data }; }
      }

      // ---- handle by status ----
      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors({
          email: fe.email,
          name: fe.name,
          last_name: fe.last_name,
          password: fe.password,
        });
        setMsg("❌ The information you entered doesn’t meet the requirements. Please fix the highlighted fields.");
        // focus first field with error
        const order = ["email", "name", "last_name", "password"];
        const first = order.find((k) => fe[k]);
        if (first) {
          requestAnimationFrame(() => {
            document.querySelector(`[name="${first}"]`)?.focus();
          });
        }
        return;
      }

      if (status === 409) {
        setMsg("❌ That email is already in use.");
        requestAnimationFrame(() => {
          document.querySelector('input[name="email"]')?.focus();
        });
        return;
      }

      setMsg(`❌ ${data?.error || err?.message || "Something went wrong"}`);
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
                name="email"
              />
              {fieldErrors.email && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.email}</p>
              )}
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
                  name="name"
                />
                {fieldErrors.name && (
                  <p className="mt-1 text-xs text-red-400">{fieldErrors.name}</p>
                )}
              </div>
              <div>
                <label className={labelCls}>Last name</label>
                <input
                  className={inputCls}
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                  name="last_name"
                />
                {fieldErrors.last_name && (
                  <p className="mt-1 text-xs text-red-400">{fieldErrors.last_name}</p>
                )}
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
                name="password"
              />
              {fieldErrors.password && (
                <p className="mt-1 text-xs text-red-400">{fieldErrors.password}</p>
              )}
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
