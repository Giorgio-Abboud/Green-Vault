import React, { useState } from "react";
import { apiPostRaw } from "../api";

export default function Signup(){
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [msg, setMsg] = useState("");

  async function submit(e){
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    const res = await apiPostRaw("/v1/users", { email, name, last_name: lastName, password });

    if (res.status === 201) {
      setMsg("✅ Your profile was successfully created!");
      return;
    }

    if (res.status === 422) {
      setFieldErrors(res.json.field_errors || {});
      return;
    }

    if (res.status === 409) {
      setFieldErrors({ email: "email already registered" });
      return;
    }

    setMsg(`❌ ${res.json?.error || "Unexpected error"}`);
  }

  const inputClass = name =>
    `w-full p-2 border rounded ${fieldErrors[name] ? "error" : ""}`;

  return (
    <div>
      <h2>Sign up</h2>
      <form onSubmit={submit} className="form space-y-3">
        {/* Email */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            placeholder="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            className={inputClass("email")}
            required
          />
          {fieldErrors.email && (
            <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
              {fieldErrors.email}
            </span>
          )}
        </div>

        {/* First name */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            placeholder="first name"
            value={name}
            onChange={e => setName(e.target.value)}
            className={inputClass("name")}
            required
          />
          {fieldErrors.name && (
            <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
              {fieldErrors.name}
            </span>
          )}
        </div>

        {/* Last name */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            placeholder="last name"
            value={lastName}
            onChange={e => setLastName(e.target.value)}
            className={inputClass("last_name")}
            required
          />
          {fieldErrors.last_name && (
            <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
              {fieldErrors.last_name}
            </span>
          )}
        </div>

        {/* Password */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            placeholder="password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className={inputClass("password")}
            required
          />
          {fieldErrors.password && (
            <span style={{ color: "#ef4444", fontSize: "0.9rem" }}>
              {fieldErrors.password}
            </span>
          )}
        </div>

        <button type="submit">Create account</button>
      </form>

      {msg && <div className="banner">{msg}</div>}
    </div>
  );
}
