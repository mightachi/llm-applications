"""In-memory store for reconciliation runs + an append-only audit trail.

Deliberately swappable for Postgres later (same method surface). Keeping it in-memory
means the prototype starts with zero infra. Every state change is recorded so a CA can
see who reviewed/approved what — important for DPDP-grade auditability.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .models import ReconResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self) -> None:
        self._runs: dict[str, dict] = {}
        self._audit: list[dict] = []

    def save_run(self, result: ReconResult, *, tenant: str = "demo") -> str:
        run_id = uuid.uuid4().hex[:12]
        self._runs[run_id] = {
            "run_id": run_id,
            "tenant": tenant,
            "created_at": _now(),
            "result": result.model_dump(mode="json"),
            "reviews": {},  # line index -> review state
        }
        self._audit.append(
            {"ts": _now(), "tenant": tenant, "run_id": run_id, "action": "recon_run_created",
             "detail": f"{result.summary.total_books_invoices} invoices reconciled, "
                       f"₹{result.summary.total_itc_at_risk:,.0f} ITC at risk"}
        )
        return run_id

    def get_run(self, run_id: str) -> dict | None:
        return self._runs.get(run_id)

    def list_runs(self) -> list[dict]:
        return [
            {"run_id": r["run_id"], "tenant": r["tenant"], "created_at": r["created_at"],
             "summary": r["result"]["summary"]}
            for r in sorted(self._runs.values(), key=lambda x: x["created_at"], reverse=True)
        ]

    def review_line(self, run_id: str, line_index: int, state: str, note: str = "") -> bool:
        run = self._runs.get(run_id)
        if not run:
            return False
        run["reviews"][str(line_index)] = {"state": state, "note": note, "ts": _now()}
        self._audit.append(
            {"ts": _now(), "tenant": run["tenant"], "run_id": run_id,
             "action": "line_reviewed", "detail": f"line {line_index} -> {state}. {note}".strip()}
        )
        return True

    def audit_trail(self, run_id: str | None = None) -> list[dict]:
        if run_id is None:
            return list(reversed(self._audit))
        return list(reversed([a for a in self._audit if a.get("run_id") == run_id]))


STORE = Store()
