import React, { useState } from "react";
import { apiPost } from "../api";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [msg, setMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});

  const inputCls =
    "w-full rounded-lg bg-brand-card/60 border border-brand-border px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-accent/70 focus:border-brand-accent/60 transition";
  const errorInput =
    "w-full rounded-lg border-2 border-red-500 bg-brand-card/60 px-3 py-2 text-gray-100 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500/60 transition";
  const inputClass = (field) => (fieldErrors[field] ? errorInput : inputCls);

  const labelCls = "text-sm text-gray-300";
  const btn =
    "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium bg-brand-accent text-black hover:brightness-110 transition shadow-soft";

  function pwReqError(pw) {
    const errs = [];
    if (!pw || pw.length < 12) errs.push("≥12 chars");
    if (!/[A-Z]/.test(pw)) errs.push("uppercase");
    if (!/[a-z]/.test(pw)) errs.push("lowercase");
    if (!/[0-9]/.test(pw)) errs.push("number");
    if (!/[^A-Za-z0-9]/.test(pw)) errs.push("symbol");
    return errs.length ? `Must include ${errs.join(", ")}` : "";
  }

  // helper to render either string or array error as text
  function renderError(err) {
    if (!err) return null;
    if (Array.isArray(err)) return err.join(", ");
    return err;
  }

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    const localErrors = {};

    // --- email checks ---
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      localErrors.email = "Email is required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      localErrors.email = "Invalid email format";
    }

    // --- name checks ---
    if (!name.trim()) {
      localErrors.name = "First name is required";
    }

    if (!lastName.trim()) {
      localErrors.last_name = "Last name is required";
    }

    // --- password checks ---
    const pwErr = pwReqError(password);
    if (pwErr) localErrors.password = pwErr;

    if (password !== confirmPassword) {
      localErrors.confirm_password = "Passwords do not match";
    }

    if (Object.keys(localErrors).length) {
      setFieldErrors(localErrors);
      setMsg(
        "❌ The information you entered doesn’t meet the requirements. Please fix the highlighted fields."
      );
      const order = ["email", "name", "last_name", "password", "confirm_password"];
      const first = order.find((k) => localErrors[k]);
      if (first) {
        requestAnimationFrame(() => {
          document.querySelector(`[name="${first}"]`)?.focus();
        });
      }
      return;
    }

    try {
      await apiPost("/v1/users", {
        email: trimmedEmail,
        name,
        last_name: lastName,
        password,
      });
      setMsg("✅ Your profile was successfully created!");
    } catch (err) {
      let status = err?.status ?? err?.response?.status ?? null;
      let data = err?.data ?? err?.response?.data ?? undefined;

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

      if (status === 422 && data && typeof data === "object") {
        const fe = data.field_errors || {};
        setFieldErrors({
          email: fe.email,
          name: fe.name,
          last_name: fe.last_name,
          password: fe.password,
          confirm_password: fe.confirm_password,
        });
        setMsg(
          "❌ The information you entered doesn’t meet the requirements. Please fix the highlighted fields."
        );
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
            {/* EMAIL */}
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

            {/* NAME / LAST NAME */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className={labelCls}>First name</label>
                <input
                  className={inputClass("name")}
                  placeholder="First name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  name="name"
                />
                {fieldErrors.name && (
                  <p className="mt-1 text-xs text-red-400">
                    {renderError(fieldErrors.name)}
                  </p>
                )}
              </div>
              <div>
                <label className={labelCls}>Last name</label>
                <input
                  className={inputClass("last_name")}
                  placeholder="Last name"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  name="last_name"
                />
                {fieldErrors.last_name && (
                  <p className="mt-1 text-xs text-red-400">
                    {renderError(fieldErrors.last_name)}
                  </p>
                )}
              </div>
            </div>

            {/* PASSWORD */}
            <div className="relative">
              <div className="flex items-center gap-2">
                <label className={labelCls}>Password</label>
                <div className="group relative cursor-pointer">
                  <div className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-brand-border text-[10px] text-gray-300">
                    i
                  </div>
                  <div className="absolute left-6 top-0 z-10 hidden w-60 rounded-lg border border-brand-border bg-brand-card/95 p-3 text-xs text-gray-200 shadow-lg group-hover:block">
                    Password must include:
                    <ul className="list-disc pl-5 mt-1 space-y-0.5 text-gray-300">
                      <li>At least 12 characters</li>
                      <li>1 uppercase letter</li>
                      <li>1 lowercase letter</li>
                      <li>1 number</li>
                      <li>1 symbol</li>
                    </ul>
                  </div>
                </div>
              </div>
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

            {/* CONFIRM PASSWORD */}
            <div>
              <label className={labelCls}>Confirm password</label>
              <input
                className={inputClass("confirm_password")}
                placeholder="••••••••"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                name="confirm_password"
              />
              {fieldErrors.confirm_password && (
                <p className="mt-1 text-xs text-red-400">
                  {renderError(fieldErrors.confirm_password)}
                </p>
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
