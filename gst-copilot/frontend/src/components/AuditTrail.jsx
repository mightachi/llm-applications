import React, { useEffect, useState } from "react";
import { getAudit } from "../lib/api.js";

export default function AuditTrail({ runId, refreshKey }) {
  const [items, setItems] = useState([]);
  useEffect(() => {
    if (!runId) return;
    getAudit(runId).then((d) => setItems(d.audit)).catch(() => {});
  }, [runId, refreshKey]);
  if (!runId) return null;
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-2 text-sm font-semibold text-slate-600">Audit trail</div>
      <ul className="space-y-2 text-xs text-slate-500">
        {items.length === 0 && <li>No events yet.</li>}
        {items.map((a, i) => (
          <li key={i} className="flex gap-2">
            <span className="font-mono text-slate-400">{new Date(a.ts).toLocaleTimeString()}</span>
            <span className="font-medium text-slate-600">{a.action}</span>
            <span>{a.detail}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
