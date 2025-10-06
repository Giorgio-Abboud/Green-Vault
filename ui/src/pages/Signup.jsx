import React, { useState } from "react";
import { apiPost } from "../api";

export default function Signup() {
  const [email,setEmail]=useState("");
  const [name,setName]=useState("");
  const [lastName,setLastName]=useState("");
  const [password,setPassword]=useState("");
  const [msg,setMsg]=useState("");

  async function submit(e){
    e.preventDefault(); setMsg("");
    try{
      const r = await apiPost("/v1/users", { email, name, last_name: lastName, password });
      setMsg(`✅ created: ${r.email}`);
    }catch(err){ setMsg(`❌ ${err.message}`); }
  }

  return (
    <form onSubmit={submit} className="form">
      <h2>Sign up</h2>
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} required />
      <input placeholder="name" value={name} onChange={e=>setName(e.target.value)} />
      <input placeholder="last name" value={lastName} onChange={e=>setLastName(e.target.value)} />
      <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} required />
      <button type="submit">Create account</button>
      <div className="banner">{msg}</div>
    </form>
  );
}
