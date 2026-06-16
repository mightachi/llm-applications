"""Tests for the reconciliation engine and extraction, using the generated samples."""

from __future__ import annotations

import json
import os

from backend.extraction import (
    extract_invoice_from_text,
    parse_gstr2b_json,
    parse_purchase_register_csv,
)
from backend.models import MatchStatus
from backend.reconcile import normalize_invoice_no, reconcile

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "data", "samples")


def _load():
    with open(os.path.join(SAMPLES, "purchase_register.csv"), encoding="utf-8-sig") as f:
        books = parse_purchase_register_csv(f.read())
    with open(os.path.join(SAMPLES, "gstr2b.json"), encoding="utf-8-sig") as f:
        twob = parse_gstr2b_json(json.load(f))
    return books, twob


def test_parsing_counts():
    books, twob = _load()
    assert len(books) == 8  # includes the duplicate row
    assert len(twob) == 6


def test_normalize_invoice_no():
    assert normalize_invoice_no("GJ/778") == normalize_invoice_no("GJ778") == "GJ778"
    assert normalize_invoice_no("inv-001") == "INV001"


def test_reconcile_classifications():
    books, twob = _load()
    result = reconcile(books, twob)
    s = result.summary
    # One duplicate row (Konkan Logistics booked twice)
    assert s.duplicates == 1
    # Pune Hardware + Mumbai Packaging not filed by suppliers
    assert s.missing_in_2b == 2
    # Nashik Chemicals filed but never booked
    assert s.missing_in_books == 1
    # Bharat Steel filed lower tax
    assert s.amount_mismatch == 1


def test_fuzzy_match_handles_invoice_typo():
    books, twob = _load()
    result = reconcile(books, twob)
    # Gujarat Polymers: books 'GJ/778' vs 2B 'GJ778' should MATCH via fuzzy/normalize.
    gj = [ln for ln in result.lines if ln.supplier_gstin == "24AAACG3333C1Z3"]
    assert len(gj) == 1
    assert gj[0].status == MatchStatus.MATCHED


def test_itc_at_risk_is_positive_and_recoverable():
    books, twob = _load()
    result = reconcile(books, twob)
    s = result.summary
    assert s.total_itc_at_risk > 0
    # Pune (10,800) + Mumbai (16,200) missing + Bharat mismatch (1,800)
    #   + Konkan duplicate (8,100) = 36,900 total at risk.
    assert round(s.total_itc_at_risk, 0) == 36900
    # Recoverable excludes the duplicate (fixed by removing a row, not a vendor nudge): 28,800.
    assert round(s.recoverable_itc, 0) == 28800
    assert s.total_itc_safe == round(s.total_itc_in_books - s.total_itc_at_risk, 2)


def test_amount_mismatch_only_counts_excess_as_risk():
    books, twob = _load()
    result = reconcile(books, twob)
    bharat = [ln for ln in result.lines if ln.supplier_gstin == "27AAACS2222B1Z2"][0]
    assert bharat.status == MatchStatus.AMOUNT_MISMATCH
    # books 45000 tax vs 2B 43200 -> 1800 at risk
    assert round(bharat.itc_at_risk, 0) == 1800


def test_regex_extraction_from_unstructured_text():
    with open(os.path.join(SAMPLES, "invoices", "pune_hardware.txt"), encoding="utf-8") as f:
        inv = extract_invoice_from_text(f.read())
    assert inv.supplier_gstin == "27AAACS4444D1Z4"
    assert normalize_invoice_no(inv.invoice_no) == "PH50"
    assert inv.cgst == 5400.0
