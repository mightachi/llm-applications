"""Reconciliation + ITC-leakage engine.

Given the buyer's purchase register (`books`) and the auto-fetched/uploaded `GSTR-2B`,
match every invoice, classify each line, and quantify ITC that is safe vs at risk.

Matching strategy (deterministic first, fuzzy fallback):
  1. Exact key match on (supplier_gstin, normalized_invoice_no).
  2. For leftovers, fuzzy candidate match within the same GSTIN using
     invoice-no similarity + tax-amount tolerance + a date window.
This mirrors how a careful accountant reconciles, but at machine speed and scale.
"""

from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta

from .models import (
    Invoice,
    ITCRisk,
    MatchStatus,
    ReconLine,
    ReconResult,
    ReconSummary,
)

try:  # fuzzy matching is optional; we degrade to exact-only if rapidfuzz is absent
    from rapidfuzz import fuzz

    def _similar(a: str, b: str) -> float:
        return float(fuzz.ratio(a, b))
except Exception:  # pragma: no cover - fallback path

    def _similar(a: str, b: str) -> float:
        return 100.0 if a == b else 0.0


# Tax delta (in INR) below which two invoices are treated as "the same amount".
AMOUNT_TOLERANCE = 1.0
# Buyer GSTIN is needed to decide intra/inter-state; configurable per tenant.
DATE_WINDOW_DAYS = 5
FUZZY_INVOICE_THRESHOLD = 85.0


def normalize_invoice_no(no: str) -> str:
    """Drop separators/leading zeros noise so 'INV-001' == 'inv001'."""
    return re.sub(r"[^A-Z0-9]", "", (no or "").upper())


def _key(inv: Invoice) -> tuple[str, str]:
    return (inv.supplier_gstin, normalize_invoice_no(inv.invoice_no))


def _date_close(a: Invoice, b: Invoice) -> bool:
    if not a.invoice_date or not b.invoice_date:
        return True
    return abs((a.invoice_date - b.invoice_date).days) <= DATE_WINDOW_DAYS


def reconcile(books: list[Invoice], gstr2b: list[Invoice]) -> ReconResult:
    lines: list[ReconLine] = []

    # 1. Detect duplicates inside the books themselves.
    seen: dict[tuple[str, str], int] = defaultdict(int)
    for b in books:
        seen[_key(b)] += 1
    dup_keys = {k for k, c in seen.items() if c > 1}

    books_by_key: dict[tuple[str, str], Invoice] = {}
    dup_count = 0
    for b in books:
        k = _key(b)
        if k in books_by_key:  # second+ occurrence
            dup_count += 1
            lines.append(
                ReconLine(
                    supplier_gstin=b.supplier_gstin,
                    supplier_name=b.supplier_name,
                    invoice_no=b.invoice_no,
                    invoice_date=b.invoice_date,
                    status=MatchStatus.DUPLICATE,
                    itc_risk=ITCRisk.AT_RISK,
                    books_tax=b.total_tax,
                    itc_at_risk=b.total_tax,
                    reason="Invoice booked more than once; duplicate ITC claim risk.",
                    match_score=100.0,
                )
            )
            continue
        books_by_key[k] = b

    twob_by_key: dict[tuple[str, str], Invoice] = {_key(g): g for g in gstr2b}
    matched_2b_keys: set[tuple[str, str]] = set()

    # 2. Exact-key pass over (deduped) books.
    unmatched_books: list[Invoice] = []
    for k, b in books_by_key.items():
        g = twob_by_key.get(k)
        if g is None:
            unmatched_books.append(b)
            continue
        matched_2b_keys.add(k)
        lines.append(_compare(b, g, score=100.0))

    # 3. Fuzzy pass for books still unmatched (supplier filed under a typo'd invoice no).
    remaining_2b = [
        g for k, g in twob_by_key.items() if k not in matched_2b_keys
    ]
    twob_by_gstin: dict[str, list[Invoice]] = defaultdict(list)
    for g in remaining_2b:
        twob_by_gstin[g.supplier_gstin].append(g)

    still_unmatched_books: list[Invoice] = []
    for b in unmatched_books:
        best, best_score = None, 0.0
        for g in twob_by_gstin.get(b.supplier_gstin, []):
            if _key(g) in matched_2b_keys:
                continue
            score = _similar(
                normalize_invoice_no(b.invoice_no), normalize_invoice_no(g.invoice_no)
            )
            amount_ok = abs(b.total_tax - g.total_tax) <= max(AMOUNT_TOLERANCE, b.total_tax * 0.02)
            if score >= FUZZY_INVOICE_THRESHOLD and amount_ok and _date_close(b, g):
                if score > best_score:
                    best, best_score = g, score
        if best is not None:
            matched_2b_keys.add(_key(best))
            lines.append(_compare(b, best, score=best_score))
        else:
            still_unmatched_books.append(b)

    # 4. Books invoices with no 2B counterpart -> supplier hasn't filed -> ITC at risk.
    for b in still_unmatched_books:
        lines.append(
            ReconLine(
                supplier_gstin=b.supplier_gstin,
                supplier_name=b.supplier_name,
                invoice_no=b.invoice_no,
                invoice_date=b.invoice_date,
                status=MatchStatus.MISSING_IN_2B,
                itc_risk=ITCRisk.AT_RISK,
                books_tax=b.total_tax,
                gstr2b_tax=0.0,
                tax_delta=b.total_tax,
                itc_at_risk=b.total_tax,
                reason="Not in GSTR-2B: supplier has not filed/uploaded this invoice. "
                "Claiming ITC now risks reversal.",
                match_score=0.0,
            )
        )

    # 5. 2B invoices with no books counterpart -> possibly a missed purchase entry.
    for k, g in twob_by_key.items():
        if k in matched_2b_keys:
            continue
        lines.append(
            ReconLine(
                supplier_gstin=g.supplier_gstin,
                supplier_name=g.supplier_name,
                invoice_no=g.invoice_no,
                invoice_date=g.invoice_date,
                status=MatchStatus.MISSING_IN_BOOKS,
                itc_risk=ITCRisk.SAFE,
                gstr2b_tax=g.total_tax,
                tax_delta=-g.total_tax,
                itc_at_risk=0.0,
                reason="In GSTR-2B but not in your books: you may be missing a purchase "
                "entry and unclaimed ITC.",
                match_score=0.0,
            )
        )

    return ReconResult(summary=_summarize(books, gstr2b, lines), lines=lines)


def _compare(b: Invoice, g: Invoice, score: float) -> ReconLine:
    delta = round(b.total_tax - g.total_tax, 2)
    if abs(delta) <= AMOUNT_TOLERANCE:
        return ReconLine(
            supplier_gstin=b.supplier_gstin,
            supplier_name=b.supplier_name or g.supplier_name,
            invoice_no=b.invoice_no,
            invoice_date=b.invoice_date,
            status=MatchStatus.MATCHED,
            itc_risk=ITCRisk.SAFE,
            books_tax=b.total_tax,
            gstr2b_tax=g.total_tax,
            tax_delta=0.0,
            itc_at_risk=0.0,
            reason="Matched and consistent with GSTR-2B. ITC safe to claim.",
            match_score=score,
        )
    # Mismatch: only the portion where books claim MORE than 2B is genuinely at risk.
    at_risk = max(delta, 0.0)
    return ReconLine(
        supplier_gstin=b.supplier_gstin,
        supplier_name=b.supplier_name or g.supplier_name,
        invoice_no=b.invoice_no,
        invoice_date=b.invoice_date,
        status=MatchStatus.AMOUNT_MISMATCH,
        itc_risk=ITCRisk.AT_RISK if at_risk > 0 else ITCRisk.SAFE,
        books_tax=b.total_tax,
        gstr2b_tax=g.total_tax,
        tax_delta=delta,
        itc_at_risk=round(at_risk, 2),
        reason=(
            f"Tax differs: books ₹{b.total_tax:,.2f} vs GSTR-2B ₹{g.total_tax:,.2f}. "
            f"₹{at_risk:,.2f} of ITC is at risk until reconciled."
        ),
        match_score=score,
    )


def _summarize(
    books: list[Invoice], gstr2b: list[Invoice], lines: list[ReconLine]
) -> ReconSummary:
    by_status: dict[MatchStatus, int] = defaultdict(int)
    for ln in lines:
        by_status[ln.status] += 1

    total_itc_books = round(sum(b.total_tax for b in books), 2)
    total_at_risk = round(sum(ln.itc_at_risk for ln in lines), 2)
    # Recoverable = at-risk ITC where the only problem is the supplier hasn't filed yet.
    recoverable = round(
        sum(
            ln.itc_at_risk
            for ln in lines
            if ln.status in (MatchStatus.MISSING_IN_2B, MatchStatus.AMOUNT_MISMATCH)
        ),
        2,
    )
    return ReconSummary(
        total_books_invoices=len(books),
        total_2b_invoices=len(gstr2b),
        matched=by_status[MatchStatus.MATCHED],
        amount_mismatch=by_status[MatchStatus.AMOUNT_MISMATCH],
        missing_in_2b=by_status[MatchStatus.MISSING_IN_2B],
        missing_in_books=by_status[MatchStatus.MISSING_IN_BOOKS],
        duplicates=by_status[MatchStatus.DUPLICATE],
        total_itc_in_books=total_itc_books,
        total_itc_at_risk=total_at_risk,
        total_itc_safe=round(total_itc_books - total_at_risk, 2),
        recoverable_itc=recoverable,
    )
