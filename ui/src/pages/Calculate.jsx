import React, { useState } from "react";
import { calcPost, apiPost } from "../api";

export default function Calculate() {
  const [timestamp,setTimestamp]=useState("");
  const [price,setPrice]=useState("");
  const [quantity,setQuantity]=useState("");
  const [side,setSide]=useState("");
  const [symbol,setSymbol]=useState("");
  const [mode,setMode]=useState("Analyze"); // Analyze | Estimate

  const [metrics,setMetrics]=useState(null);
  const [msg,setMsg]=useState("");

  async function run(e){
    e.preventDefault(); setMsg("");
    try{
      const r = await calcPost({ timestamp, price, quantity, side, symbol, request: mode });
      // FastAPI returns { ok, request_id, fills, metrics }
      setMetrics(r?.metrics || null);
      setMsg("✅ calculated");
    }catch(err){ setMsg(`❌ ${err.message}`); }
  }

  async function save(){
    if(!metrics){ setMsg("No metrics to save"); return; }
    try{
      const payload = {
        fill: { timestamp, price, quantity, side, symbol, mode, result: "SUCCESS" },
        metrics,
        client_request_id: metrics.request_id || "",
      };
      const r = await apiPost("/v1/fills", payload); // returns { fill_id, metric_id } as data
      setMsg("✅ Your fills and metrics were saved!");
    }catch(err){ setMsg(`❌ ${err.message}`); }
  }

  return (
    <div>
      <h2>Calculate</h2>
      <form onSubmit={run} className="form">
        <input placeholder="timestamp (RFC3339)" value={timestamp} onChange={e=>setTimestamp(e.target.value)} required />
        <input placeholder="price" value={price} onChange={e=>setPrice(e.target.value)} required />
        <input placeholder="quantity" value={quantity} onChange={e=>setQuantity(e.target.value)} required />
        <input placeholder="side buy/sell" value={side} onChange={e=>setSide(e.target.value)} required />
        <input placeholder="symbol" value={symbol} onChange={e=>setSymbol(e.target.value)} required />

        <div style={{ display:"flex", gap:8, marginTop: 8 }}>
          <button type="button" onClick={()=>setMode("Analyze")} disabled={mode==="Analyze"}>Analyze</button>
          <button type="button" onClick={()=>setMode("Estimate")} disabled={mode==="Estimate"}>Estimate</button>
          <button type="submit">Run</button>
        </div>
        <div style={{marginTop:4, opacity:.8}}>Mode: <strong>{mode}</strong></div>
      </form>

      {metrics && (
        <div style={{marginTop:12}}>
          <pre>{JSON.stringify(metrics, null, 2)}</pre>
          <button onClick={save}>Save to DB</button>
        </div>
      )}
      {msg && <div className="banner" style={{marginTop:12}}>{msg}</div>}
    </div>
  );
}
