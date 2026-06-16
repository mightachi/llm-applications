import React, { useState } from "react";
import { runDemo, reconcileUpload, getGstr3b, inr } from "./lib/api.js";
import SummaryCards from "./components/SummaryCards.jsx";
import ExceptionQueue from "./components/ExceptionQueue.jsx";
import AuditTrail from "./components/AuditTrail.jsx";

export default function App() {
  const [result, setResult] = useState(null);
  const [runId, setRunId] = useState(null);
  const [gstr3b, setGstr3b] = useState(null);
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [prFile, setPrFile] = useState(null);
  const [twobFile, setTwobFile] = useState(null);

  const load = async (fn) => {
    setLoading(true);
    setError("");
    try {
      const data = await fn();
      setResult(data);
      setRunId(data.runId);
      setGstr3b(await getGstr3b(data.runId));
    } catch (e) {
      setError(e.message || "Something went wrong. Is the backend running on :8000?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <header className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">GST Compliance & Cashflow Copilot</h1>
          <p className="text-sm text-slate-500">Find the Input Tax Credit you are silently losing — then recover it.</p>
        </div>
        <div className="flex items-center gap-2">
          <select value={language} onChange={(e) => setLanguage(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm">
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
          </select>
          <button onClick={() => load(runDemo)} disabled={loading} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? "Running…" : "Run demo audit"}
          </button>
        </div>
      </header>

      <div className="mb-6 rounded-xl border border-dashed border-slate-300 bg-white p-4">
        <div className="mb-2 text-sm font-medium text-slate-600">Or upload your own data</div>
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <label className="text-slate-500">Purchase register (CSV)
            <input type="file" accept=".csv" onChange={(e) => setPrFile(e.target.files[0])} className="ml-2 text-xs" />
          </label>
          <label className="text-slate-500">GSTR-2B (JSON)
            <input type="file" accept=".json" onChange={(e) => setTwobFile(e.target.files[0])} className="ml-2 text-xs" />
          </label>
          <button
            onClick={() => load(() => reconcileUpload(prFile, twobFile))}
            disabled={!prFile || !twobFile || loading}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-white hover:bg-slate-900 disabled:opacity-40"
          >Reconcile</button>
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>}

      {result && (
        <div className="space-y-6">
          <SummaryCards summary={result.summary} />

          {gstr3b && (
            <div className="rounded-xl border border-indigo-200 bg-indigo-50 p-4">
              <div className="text-sm font-semibold text-indigo-700">GSTR-3B ITC advice</div>
              <p className="mt-1 text-sm text-slate-700">{gstr3b.advice}</p>
              <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-600">
                <span>Claim now (safe): <b>{inr(gstr3b.itc_claimable_now_safe)}</b></span>
                <span>Defer (at risk): <b>{inr(gstr3b.itc_to_defer_at_risk)}</b></span>
                <span>Recoverable: <b>{inr(gstr3b.itc_recoverable_via_followup)}</b></span>
              </div>
            </div>
          )}

          <ExceptionQueue lines={result.lines} runId={runId} language={language} />
          <AuditTrail runId={runId} refreshKey={result.lines} />
        </div>
      )}

      {!result && !loading && (
        <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-500">
          Click <b>Run demo audit</b> to reconcile a sample MSME's books against GSTR-2B and see the ITC at risk.
        </div>
      )}

      <footer className="mt-10 text-center text-xs text-slate-400">
        Prototype · Make in India · runs fully offline; add an LLM key to upgrade the copilot.
      </footer>
    </div>
  );
}
