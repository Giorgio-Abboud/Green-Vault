import React, { useState } from "react";
import { apiPostRaw } from "../api";
import { useAuth } from "../auth";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [msg, setMsg] = useState("");
  const { refresh } = useAuth();

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    const res = await apiPostRaw("/v1/login", { email, password });

    if (res.status === 200) {
      await refresh();
      setMsg("✅ Logged in");
      return;
    }

    if (res.status === 422) {
      setFieldErrors(res.json.field_errors || {});
      return;
    }

    if (res.status === 401) {
      // just show banner, no per-field errors
      setMsg("❌ Invalid credentials");
      return;
    }

    setMsg(`❌ ${res.json?.error || "Unexpected error"}`);
  }

  const inputClass = (name) =>
    `w-full p-2 border rounded ${fieldErrors[name] ? "error" : ""}`;

  return (
    <form onSubmit={submit} className="form space-y-3">
      <h2>Log in</h2>

      {/* Email */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <input
          placeholder="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClass("email")}
          required
        />
        {fieldErrors.email && (
          <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
            {fieldErrors.email}
          </span>
        )}
      </div>

      {/* Password */}
      <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
        <input
          placeholder="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputClass("password")}
          required
        />
        {fieldErrors.password && (
          <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
            {fieldErrors.password}
          </span>
        )}
      </div>

      <button type="submit">Log in</button>
      {msg && <div className="banner error">{msg}</div>}
    </form>
  );
}
