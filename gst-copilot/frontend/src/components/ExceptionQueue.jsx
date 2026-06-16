import React, { useState } from "react";
import { inr, explainLine, draftNudge, reviewLine } from "../lib/api.js";

const STATUS_META = {
  matched: { label: "Matched", cls: "bg-emerald-100 text-emerald-700" },
  amount_mismatch: { label: "Amount mismatch", cls: "bg-amber-100 text-amber-700" },
  missing_in_2b: { label: "Not filed by supplier", cls: "bg-rose-100 text-rose-700" },
  missing_in_books: { label: "Missing in books", cls: "bg-sky-100 text-sky-700" },
  duplicate: { label: "Duplicate", cls: "bg-purple-100 text-purple-700" },
};

function Row({ line, index, runId, language }) {
  const [explanation, setExplanation] = useState("");
  const [nudge, setNudge] = useState("");
  const [reviewed, setReviewed] = useState(null);
  const [busy, setBusy] = useState(false);
  const meta = STATUS_META[line.status] || { label: line.status, cls: "bg-slate-100" };

  const onExplain = async () => {
    setBusy(true);
    try {
      setExplanation((await explainLine(line, language)).explanation);
    } finally {
      setBusy(false);
    }
  };
  const onNudge = async () => {
    setBusy(true);
    try {
      setNudge((await draftNudge(line, "Our Company", language)).message);
    } finally {
      setBusy(false);
    }
  };
  const onReview = async (state) => {
    await reviewLine(runId, index, state, "");
    setReviewed(state);
  };

  return (
    <>
      <tr className="border-t border-slate-100 align-top">
        <td className="px-3 py-3 font-medium">{line.supplier_name || "—"}<div className="text-xs text-slate-400">{line.supplier_gstin}</div></td>
        <td className="px-3 py-3">{line.invoice_no}<div className="text-xs text-slate-400">{line.invoice_date || ""}</div></td>
        <td className="px-3 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-medium ${meta.cls}`}>{meta.label}</span></td>
        <td className="px-3 py-3 text-right tabular-nums">{inr(line.books_tax)}</td>
        <td className="px-3 py-3 text-right tabular-nums">{inr(line.gstr2b_tax)}</td>
        <td className="px-3 py-3 text-right tabular-nums font-semibold text-rose-600">{line.itc_at_risk > 0 ? inr(line.itc_at_risk) : "—"}</td>
        <td className="px-3 py-3">
          <div className="flex flex-wrap gap-1">
            <button onClick={onExplain} disabled={busy} className="rounded bg-slate-100 px-2 py-1 text-xs hover:bg-slate-200">Explain</button>
            {line.itc_at_risk > 0 && line.status !== "duplicate" && (
              <button onClick={onNudge} disabled={busy} className="rounded bg-indigo-100 px-2 py-1 text-xs text-indigo-700 hover:bg-indigo-200">Draft nudge</button>
            )}
            <button onClick={() => onReview("approved")} className={`rounded px-2 py-1 text-xs ${reviewed === "approved" ? "bg-emerald-600 text-white" : "bg-emerald-100 text-emerald-700 hover:bg-emerald-200"}`}>✓</button>
            <button onClick={() => onReview("rejected")} className={`rounded px-2 py-1 text-xs ${reviewed === "rejected" ? "bg-rose-600 text-white" : "bg-rose-100 text-rose-700 hover:bg-rose-200"}`}>✕</button>
          </div>
        </td>
      </tr>
      {(explanation || nudge) && (
        <tr className="bg-slate-50">
          <td colSpan={7} className="px-3 py-3">
            {explanation && <div className="mb-2 text-sm"><span className="font-semibold text-slate-600">Copilot: </span>{explanation}</div>}
            {nudge && (
              <div className="rounded-lg border border-indigo-200 bg-white p-3 text-sm">
                <div className="mb-1 text-xs font-semibold uppercase text-indigo-500">Suggested supplier message (WhatsApp)</div>
                {nudge}
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export default function ExceptionQueue({ lines, runId, language }) {
  const [tab, setTab] = useState("at_risk");
  if (!lines) return null;
  const filtered = lines.filter((l) =>
    tab === "all" ? true : tab === "at_risk" ? l.itc_at_risk > 0 || l.status !== "matched" : l.status === "matched"
  );
  const tabs = [
    { id: "at_risk", label: `Exceptions (${lines.filter((l) => l.status !== "matched").length})` },
    { id: "matched", label: `Matched (${lines.filter((l) => l.status === "matched").length})` },
    { id: "all", label: `All (${lines.length})` },
  ];
  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex gap-2 border-b border-slate-100 p-3">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)} className={`rounded-lg px-3 py-1 text-sm ${tab === t.id ? "bg-slate-800 text-white" : "bg-slate-100 hover:bg-slate-200"}`}>{t.label}</button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Supplier</th>
              <th className="px-3 py-2">Invoice</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2 text-right">Books tax</th>
              <th className="px-3 py-2 text-right">2B tax</th>
              <th className="px-3 py-2 text-right">ITC at risk</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((line) => (
              <Row key={`${line.supplier_gstin}-${line.invoice_no}-${line.status}`} line={line} index={lines.indexOf(line)} runId={runId} language={language} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
