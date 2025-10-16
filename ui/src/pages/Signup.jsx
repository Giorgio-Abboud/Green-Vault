import React, { useState } from "react";
import { apiPostRaw } from "../api";

function InfoTooltip({ text }) {
  return (
    <span className="tooltip-inline">
      ℹ️
      <span className="tooltip-inline-text">{text}</span>
    </span>
  );
}

export default function Signup() {
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [lastName, setLastName] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [msg, setMsg] = useState("");

  async function submit(e) {
    e.preventDefault();
    setMsg("");
    setFieldErrors({});

    const res = await apiPostRaw("/v1/users", {
      email,
      name,
      last_name: lastName,
      password,
    });

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

  const inputClass = (name) =>
    `w-full p-2 border rounded ${fieldErrors[name] ? "error" : ""}`;

  return (
    <div>
      <h2>Sign up</h2>
      <form onSubmit={submit} className="form space-y-4">
        {/* Email */}
        <div className="form-group">
          <label>
            Email <InfoTooltip text="Must follow the format username@domain.tld (e.g. pepito1@gmail.com)." />
          </label>
          <input
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputClass("email")}
            required
          />
        </div>

        {/* First name */}
        <div className="form-group">
          <label>
            Name <InfoTooltip text="Only letters A–Z with valid characters (' -). (e.g. Roary)." />
          </label>
          <input
            placeholder="first name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={inputClass("name")}
            required
          />
        </div>

        {/* Last name */}
        <div className="form-group">
          <label>
            Last name{" "}
            <InfoTooltip text="Only letters A–Z with valid characters (' -). (Gonzales, O'Neal)." />
          </label>
          <input
            placeholder="last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            className={inputClass("last_name")}
            required
          />
        </div>

        {/* Password */}
        <div className="form-group">
          <label>
            Password{" "}
            <InfoTooltip text="Must be 12–128 characters long and include at least one lowercase, one uppercase, one digit, and one symbol. (e.g. StrongPass#25)." />
          </label>
          <input
            placeholder="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className={inputClass("password")}
            required
          />
        </div>

        <button type="submit">Create account</button>
      </form>

      {msg && <div className="banner">{msg}</div>}
    </div>
  );
}
