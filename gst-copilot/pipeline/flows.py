"""Prefect batch pipeline: ingest -> reconcile -> persist -> alert.

This is the production-shaped version of what the API does per-request. A scheduled
deployment can run this monthly per tenant right after GSTR-2B is generated (14th).

Run ad-hoc:  python -m pipeline.flows
With Prefect: `prefect deployment ...` (optional; the flow also runs as a plain script).
"""

from __future__ import annotations

import json
import os

try:
    from prefect import flow, task
except Exception:  # Prefect optional -> no-op decorators so the script still runs
    def task(fn=None, **_):
        return fn if fn else (lambda f: f)

    def flow(fn=None, **_):
        return fn if fn else (lambda f: f)

from backend.extraction import parse_gstr2b_json, parse_purchase_register_csv
from backend.models import ReconResult
from backend.reconcile import reconcile

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "data", "samples")


@task
def load_books(path: str):
    with open(path, encoding="utf-8-sig") as f:
        return parse_purchase_register_csv(f.read())


@task
def load_2b(path: str):
    with open(path, encoding="utf-8-sig") as f:
        return parse_gstr2b_json(json.load(f))


@task
def run_reconcile(books, twob) -> ReconResult:
    return reconcile(books, twob)


@task
def alert_high_risk(result: ReconResult, threshold: float = 5000.0) -> list[str]:
    alerts = [
        f"{ln.supplier_name or ln.supplier_gstin}: ₹{ln.itc_at_risk:,.0f} at risk ({ln.status.value})"
        for ln in result.lines
        if ln.itc_at_risk >= threshold
    ]
    for a in alerts:
        print("ALERT:", a)
    return alerts


@flow(name="gst-monthly-reconciliation")
def monthly_reconciliation(
    books_path: str | None = None, twob_path: str | None = None
) -> ReconResult:
    books_path = books_path or os.path.join(SAMPLES, "purchase_register.csv")
    twob_path = twob_path or os.path.join(SAMPLES, "gstr2b.json")
    books = load_books(books_path)
    twob = load_2b(twob_path)
    result = run_reconcile(books, twob)
    alert_high_risk(result)
    s = result.summary
    print(
        f"\nReconciled {s.total_books_invoices} booked invoices vs {s.total_2b_invoices} in GSTR-2B."
        f"\n  matched={s.matched} mismatch={s.amount_mismatch} missing_in_2b={s.missing_in_2b} "
        f"missing_in_books={s.missing_in_books} duplicates={s.duplicates}"
        f"\n  ITC safe ₹{s.total_itc_safe:,.0f} | at risk ₹{s.total_itc_at_risk:,.0f} | "
        f"recoverable ₹{s.recoverable_itc:,.0f}"
    )
    return result


if __name__ == "__main__":
    monthly_reconciliation()
