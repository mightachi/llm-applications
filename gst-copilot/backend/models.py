"""Pydantic schemas shared across extraction, reconciliation and the API.

All monetary values are in INR. Tax is split into CGST/SGST (intra-state) or IGST
(inter-state). `taxable_value` excludes tax; `total_tax = cgst + sgst + igst`.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MatchStatus(str, Enum):
    MATCHED = "matched"                 # present and consistent on both sides
    AMOUNT_MISMATCH = "amount_mismatch"  # matched invoice, tax/value differs
    MISSING_IN_2B = "missing_in_2b"      # in books, supplier has NOT filed -> ITC at risk
    MISSING_IN_BOOKS = "missing_in_books"  # in GSTR-2B, not in books -> possible missed entry
    DUPLICATE = "duplicate"              # same invoice booked twice


class ITCRisk(str, Enum):
    SAFE = "safe"          # claim now
    AT_RISK = "at_risk"    # supplier not filed / mismatch -> may lose ITC
    BLOCKED = "blocked"    # ineligible under Sec 17(5) etc.


class Invoice(BaseModel):
    """A single tax invoice line (header-level), from books or from GSTR-2B."""

    source: str = Field(description="'books' or 'gstr2b'")
    supplier_gstin: str
    supplier_name: Optional[str] = None
    invoice_no: str
    invoice_date: Optional[date] = None
    taxable_value: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    hsn: Optional[str] = None
    place_of_supply: Optional[str] = None
    # confidence from extraction (1.0 for structured data such as Tally export / 2B JSON)
    extraction_confidence: float = 1.0

    @property
    def total_tax(self) -> float:
        return round(self.cgst + self.sgst + self.igst, 2)

    @property
    def invoice_value(self) -> float:
        return round(self.taxable_value + self.total_tax, 2)

    @field_validator("supplier_gstin")
    @classmethod
    def _norm_gstin(cls, v: str) -> str:
        return (v or "").strip().upper()


class ReconLine(BaseModel):
    """Result of matching one logical invoice across books and GSTR-2B."""

    supplier_gstin: str
    supplier_name: Optional[str] = None
    invoice_no: str
    invoice_date: Optional[date] = None
    status: MatchStatus
    itc_risk: ITCRisk
    books_tax: float = 0.0
    gstr2b_tax: float = 0.0
    tax_delta: float = 0.0          # books_tax - gstr2b_tax
    itc_at_risk: float = 0.0        # rupees of ITC that may be lost
    reason: str = ""
    match_score: float = 0.0        # 0..100 fuzzy match confidence


class ReconSummary(BaseModel):
    total_books_invoices: int
    total_2b_invoices: int
    matched: int
    amount_mismatch: int
    missing_in_2b: int
    missing_in_books: int
    duplicates: int
    total_itc_in_books: float
    total_itc_at_risk: float
    total_itc_safe: float
    recoverable_itc: float  # at-risk ITC that a vendor nudge can plausibly recover


class ReconResult(BaseModel):
    summary: ReconSummary
    lines: list[ReconLine]
