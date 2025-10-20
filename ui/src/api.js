const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
const CALC = import.meta.env.VITE_CALC_BASE_URL || "http://localhost:8000";

// Small helper to throw nice errors and unwrap { ok, data }
async function handleJson(res) {
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  const out = await res.json();
  // Our Go API returns { ok, data?, error? } – prefer .data if present
  return typeof out === "object" && out && "data" in out ? out.data : out;
}

export async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  return handleJson(res);
}

export async function apiGet(path) {
  const res = await fetch(`${API}${path}`, { credentials: "include" });
  return handleJson(res);
}

export async function apiPut(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  return handleJson(res);
}

export async function calcPost(body) {
  const res = await fetch(`${CALC}/calculate`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  return handleJson(res);
}

export async function apiPostRaw(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });
  let json = {};
  try {
    json = await res.json();
  } catch {}
  return { status: res.status, ok: res.ok, json };
}
