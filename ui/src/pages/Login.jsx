import React, { useState } from "react";
import { apiPost } from "../api";
import { useAuth } from "../auth";

export default function Login() {
  const [email,setEmail]=useState("");
  const [password,setPassword]=useState("");
  const [msg,setMsg]=useState("");
  const { refresh } = useAuth();

  async function submit(e){
    e.preventDefault(); setMsg("");
    try{
      await apiPost("/v1/login", { email, password });
      await refresh();
      setMsg("✅ logged in");
    }catch(err){ setMsg(`❌ ${err.message}`); }
  }

  return (
    <form onSubmit={submit} className="form">
      <h2>Log in</h2>
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} required />
      <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
      <button type="submit">Log in</button>
      <div className="banner">{msg}</div>
    </form>
  );
}
