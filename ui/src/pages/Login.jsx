import React, { useState } from "react";
import { apiPost } from "../api";
import { useAuth } from "../auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const { refresh } = useAuth();

  const baseInput =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const errorInput =
    "w-full rounded-lg border-2 border-red-500 bg-brand-card/60 px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/60 transition";
  const inputClass = (field) => (fieldErrors[field] ? errorInput : baseInput);

  const labelCls = "text-sm text-gray-300";
  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  function renderError(err) {
    if (!err) return null;
    if (typeof err === "boolean") return "Invalid value";
    if (Array.isArray(err)) return err.join(", ");
    return err;
  }

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    // ---------- CLIENT-SIDE VALIDATION ----------
    const localErrors = {};
    const trimmedEmail = email.trim();

    if (!trimmedEmail) {
      localErrors.email = "Email is required";
    } else if (!emailRegex.test(trimmedEmail)) {
      localErrors.email = "Invalid email format";
    }

    if (!password) {
      localErrors.password = "Password is required";
    }

    if (Object.keys(localErrors).length) {
      setFieldErrors(localErrors);
      setMsg("❌ Please fix the highlighted fields.");
      const first = localErrors.email ? "email" : "password";
      requestAnimationFrame(() => {
        document.querySelector(`input[name="${first}"]`)?.focus();
      });
      return;
    }

    // ---------- API CALL ----------
    try {
      await apiPost("/v1/login", { email: trimmedEmail, password });
      await refresh();
      setMsg("✅ logged in");
    } catch (err) {
      let status =
        err?.status ??
        err?.response?.status ??
        null;

      let data =
        err?.data ??
        err?.response?.data ??
        undefined;

      if (!data && (typeof err === "string" || typeof err?.message === "string")) {
        const raw = String(typeof err === "string" ? err : err.message).trim();
        const m = raw.match(/^(\d{3})\s+(.+)$/);
        if (m) {
          status = Number(m[1]);
          const bodyStr = m[2];
          try {
            data = JSON.parse(bodyStr);
          } catch {
            data = { error: bodyStr };
          }
        } else {
          try {
            data = JSON.parse(raw);
          } catch {
            data = { error: raw };
          }
        }
      }
      if (typeof data === "string") {
        try {
          data = JSON.parse(data);
        } catch {
          data = { error: data };
        }
      }
      setFieldErrors({});

      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors({
          email: fe.email,
          password: fe.password,
        });
        setMsg(`❌ ${data.error || "validation failed"}`);
        return;
      }

      if (status === 401) {
        const text =
          (data?.error && typeof data.error === "string")
            ? (data.error.toLowerCase().includes("credential") || data.error.toLowerCase().includes("invalid")
                ? "Invalid email or password"
                : data.error)
            : "Unauthorized";
        setFieldErrors({ email: true, password: true });
        setMsg(`❌ ${text}`);
        requestAnimationFrame(() => {
          document.querySelector('input[name="password"]')?.focus();
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
        <form
          onSubmit={submit}
          noValidate   // <-- disables browser tooltip validation
          className="space-y-4 rounded-xl2 border border-brand-border bg-brand-card p-6 shadow-soft"
        >
          <h2 className="text-xl font-semibold tracking-tight">Log in</h2>

          <div>
            <label className={labelCls}>Email</label>
            <input
              className={inputClass("email")}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              name="email"
            />
            {fieldErrors.email && (
              <p className="mt-1 text-xs text-red-400">
                {renderError(fieldErrors.email)}
              </p>
            )}
          </div>

          <div>
            <label className={labelCls}>Password</label>
            <input
              className={inputClass("password")}
              placeholder="••••••••"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              name="password"
            />
            {fieldErrors.password && (
              <p className="mt-1 text-xs text-red-400">
                {renderError(fieldErrors.password)}
              </p>
            )}
          </div>

          <button type="submit" className={btn}>
            Log in
          </button>

          <div className="mt-4 text-center text-sm text-gray-300">
            Don’t have an account?{" "}
            <a
              href="/signup"
              className="text-brand-accent hover:underline"
            >
              Sign up
            </a>
          </div>

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
