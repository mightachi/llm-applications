const BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export const inr = (n) =>
  "₹" + Number(n || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 });

async function json(res) {
  if (!res.ok) throw new Error((await res.text()) || res.statusText);
  return res.json();
}

export async function runDemo() {
  const res = await fetch(`${BASE}/demo`, { method: "POST" });
  const runId = res.headers.get("X-Run-Id");
  const data = await json(res);
  return { runId, ...data };
}

export async function reconcileUpload(prFile, twobFile) {
  const fd = new FormData();
  fd.append("purchase_register", prFile);
  fd.append("gstr2b", twobFile);
  const res = await fetch(`${BASE}/reconcile`, { method: "POST", body: fd });
  const runId = res.headers.get("X-Run-Id");
  const data = await json(res);
  return { runId, ...data };
}

export const getGstr3b = (runId) => fetch(`${BASE}/runs/${runId}/gstr3b`).then(json);

export const explainLine = (line, language) =>
  fetch(`${BASE}/explain`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ line, language }),
  }).then(json);

export const draftNudge = (line, buyerName, language) =>
  fetch(`${BASE}/nudge`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ line, buyer_name: buyerName, language }),
  }).then(json);

export const reviewLine = (runId, lineIndex, state, note) =>
  fetch(`${BASE}/runs/${runId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ line_index: lineIndex, state, note }),
  }).then(json);

export const getAudit = (runId) =>
  fetch(`${BASE}/audit${runId ? `?run_id=${runId}` : ""}`).then(json);
