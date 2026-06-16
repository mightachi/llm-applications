import React from "react";
import { inr } from "../lib/api.js";

function Card({ label, value, sub, tone = "slate" }) {
  const tones = {
    slate: "bg-white border-slate-200",
    green: "bg-emerald-50 border-emerald-200",
    red: "bg-rose-50 border-rose-200",
    amber: "bg-amber-50 border-amber-200",
  };
  return (
    <div className={`rounded-xl border p-4 shadow-sm ${tones[tone]}`}>
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
      {sub && <div className="mt-1 text-xs text-slate-500">{sub}</div>}
    </div>
  );
}

export default function SummaryCards({ summary }) {
  if (!summary) return null;
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <Card label="ITC in Books" value={inr(summary.total_itc_in_books)} sub="Total tax credit claimed" />
      <Card label="ITC Safe to Claim" value={inr(summary.total_itc_safe)} sub="Matched in GSTR-2B" tone="green" />
      <Card label="ITC at Risk" value={inr(summary.total_itc_at_risk)} sub="Mismatch / not filed / duplicate" tone="red" />
      <Card label="Recoverable" value={inr(summary.recoverable_itc)} sub="With supplier follow-up" tone="amber" />
    </div>
  );
}
