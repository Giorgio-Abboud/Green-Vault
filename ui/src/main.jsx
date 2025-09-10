import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API = import.meta.env.VITE_CALC_BASE_URL || "http://localhost:8000";

function App() {
  const [timestamp, setTimestamp] = useState("");
  const [price, setPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [side, setSide] = useState("");

  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [requestId, setRequestId] = useState("");
  const [errorText, setErrorText] = useState("");

  async function submit(e) {
    e.preventDefault();
    setStatus("loading");
    setErrorText("");
    setRequestId("");

    // set Analyse to default
    const reqType = e.nativeEvent?.submitter?.value || "Analyze";

    try {
      const res = await fetch(`${API}/calculate`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          timestamp,
          price,
          quantity,
          side,
          request: reqType,
        }),
      });

      if (!res.ok) {
        let detail = "";
        try {
          const j = await res.json();
          detail = j?.detail ? `: ${JSON.stringify(j.detail)}` : "";
        } catch {}
        throw new Error(`Request failed (${res.status})${detail}`);
      }

      const data = await res.json();
      if (data?.ok) {
        setRequestId(data.request_id || "");
        setStatus("success");
      } else {
        throw new Error("Operation not OK");
      }
    } catch (err) {
      setErrorText(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }

  return (
    <div>
      <h1>Green Vault UI</h1>

      {status === "loading" && <div className="banner loading">Processing…</div>}
      {status === "success" && (
        <div className="banner success">
          ✅ Calculation recorded! {requestId && `(request_id: ${requestId})`}
        </div>
      )}
      {status === "error" && (
        <div className="banner error">❌ {errorText || "Something went wrong"}</div>
      )}

      <form onSubmit={submit}>
        <label>
          Timestamp
          <input value={timestamp} onChange={(e) => setTimestamp(e.target.value)} required />
        </label>

        <label>
          Price
          <input value={price} onChange={(e) => setPrice(e.target.value)} required />
        </label>

        <label>
          Quantity
          <input value={quantity} onChange={(e) => setQuantity(e.target.value)} required />
        </label>

        <label>
          Side
          <input value={side} onChange={(e) => setSide(e.target.value)} required placeholder="buy/sell" />
        </label>

        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
          <button type="submit" value="Analyze" disabled={status === "loading"}>
            {status === "loading" ? "Working…" : "Analyze"}
          </button>
          <button type="submit" value="Estimate" disabled={status === "loading"}>
            {status === "loading" ? "Working…" : "Estimate"}
          </button>
        </div>
      </form>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
