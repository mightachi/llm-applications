"""Ingestion + extraction layer.

Turns the many shapes of MSME input into a clean `list[Invoice]`:
  - Purchase register CSV / Excel (Tally-style export)         -> structured
  - GSTR-2B JSON (official GSTN download or GSP API response)  -> structured
  - Unstructured invoice text (from OCR of a PDF/photo)        -> LLM or regex fallback

Real OCR (PaddleOCR/Tesseract) and the GSP API plug in here; for an offline demo we
parse structured files directly and use a regex fallback for unstructured text.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import datetime

from .llm import chat, is_enabled
from .models import Invoice


def _to_float(v) -> float:
    if v is None or v == "":
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return float(re.sub(r"[^0-9.\-]", "", str(v)) or 0)


def _parse_date(v):
    if not v:
        return None
    s = str(v).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- purchase register

PR_ALIASES = {
    "supplier_gstin": ["gstin", "supplier_gstin", "supplier gstin", "gstin of supplier"],
    "supplier_name": ["supplier", "supplier_name", "supplier name", "party", "vendor"],
    "invoice_no": ["invoice_no", "invoice no", "invoice number", "bill no", "inv no"],
    "invoice_date": ["invoice_date", "invoice date", "date", "bill date"],
    "taxable_value": ["taxable_value", "taxable value", "taxable", "amount"],
    "cgst": ["cgst", "cgst amount"],
    "sgst": ["sgst", "sgst amount"],
    "igst": ["igst", "igst amount"],
    "hsn": ["hsn", "hsn/sac", "hsn code"],
}


def _resolve_columns(header: list[str]) -> dict[str, str]:
    lower = {h.lower().strip(): h for h in header}
    mapping: dict[str, str] = {}
    for field, aliases in PR_ALIASES.items():
        for a in aliases:
            if a in lower:
                mapping[field] = lower[a]
                break
    return mapping


def parse_purchase_register_csv(text: str) -> list[Invoice]:
    reader = csv.DictReader(io.StringIO(text))
    cols = _resolve_columns(reader.fieldnames or [])
    if "supplier_gstin" not in cols or "invoice_no" not in cols:
        raise ValueError(
            "Purchase register must contain at least a GSTIN and an invoice number column."
        )
    invoices: list[Invoice] = []
    for row in reader:
        invoices.append(
            Invoice(
                source="books",
                supplier_gstin=row.get(cols["supplier_gstin"], ""),
                supplier_name=row.get(cols.get("supplier_name", ""), None),
                invoice_no=row.get(cols["invoice_no"], ""),
                invoice_date=_parse_date(row.get(cols.get("invoice_date", ""))),
                taxable_value=_to_float(row.get(cols.get("taxable_value", ""))),
                cgst=_to_float(row.get(cols.get("cgst", ""))),
                sgst=_to_float(row.get(cols.get("sgst", ""))),
                igst=_to_float(row.get(cols.get("igst", ""))),
                hsn=row.get(cols.get("hsn", ""), None),
            )
        )
    return invoices


# ------------------------------------------------------------------------- GSTR-2B

def parse_gstr2b_json(data: dict | str) -> list[Invoice]:
    """Parse the official GSTR-2B JSON (docdata.b2b...) into header-level invoices."""
    if isinstance(data, str):
        data = json.loads(data)

    invoices: list[Invoice] = []
    b2b = (data.get("data", data).get("docdata", {}) or {}).get("b2b", [])
    for supplier in b2b:
        ctin = supplier.get("ctin", "")
        trdnm = supplier.get("trdnm") or supplier.get("trade_name")
        for inv in supplier.get("inv", []):
            cgst = sgst = igst = txval = 0.0
            for item in inv.get("items", []) or [{}]:
                cgst += _to_float(item.get("camt"))
                sgst += _to_float(item.get("samt"))
                igst += _to_float(item.get("iamt"))
                txval += _to_float(item.get("txval"))
            invoices.append(
                Invoice(
                    source="gstr2b",
                    supplier_gstin=ctin,
                    supplier_name=trdnm,
                    invoice_no=str(inv.get("inum", "")),
                    invoice_date=_parse_date(inv.get("dt") or inv.get("idt")),
                    taxable_value=txval or _to_float(inv.get("txval")),
                    cgst=cgst,
                    sgst=sgst,
                    igst=igst,
                    place_of_supply=inv.get("pos"),
                )
            )
    return invoices


# ----------------------------------------------------- unstructured invoice (OCR text)

_EXTRACT_SYSTEM = (
    "You extract structured fields from a single Indian GST tax invoice. "
    "Return ONLY compact JSON with keys: supplier_gstin, supplier_name, invoice_no, "
    "invoice_date (DD-MM-YYYY), taxable_value, cgst, sgst, igst, hsn. Numbers only for amounts."
)

_GSTIN_RE = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b")


def extract_invoice_from_text(text: str) -> Invoice:
    """LLM extraction when enabled, else a best-effort regex fallback."""
    if is_enabled():
        raw = chat(_EXTRACT_SYSTEM, text, temperature=0.0)
        if raw:
            try:
                payload = json.loads(re.search(r"\{.*\}", raw, re.S).group(0))
                return Invoice(
                    source="books",
                    supplier_gstin=payload.get("supplier_gstin", ""),
                    supplier_name=payload.get("supplier_name"),
                    invoice_no=str(payload.get("invoice_no", "")),
                    invoice_date=_parse_date(payload.get("invoice_date")),
                    taxable_value=_to_float(payload.get("taxable_value")),
                    cgst=_to_float(payload.get("cgst")),
                    sgst=_to_float(payload.get("sgst")),
                    igst=_to_float(payload.get("igst")),
                    hsn=payload.get("hsn"),
                    extraction_confidence=0.9,
                )
            except Exception:
                pass  # fall through to regex
    return _regex_extract(text)


def _regex_extract(text: str) -> Invoice:
    gstin_m = _GSTIN_RE.search(text)
    inv_m = re.search(r"(?:invoice|inv|bill)\s*(?:no\.?|#|number)?\s*[:\-]?\s*([A-Z0-9/\-]+)", text, re.I)
    date_m = re.search(r"(\d{1,2}[-/][A-Za-z0-9]{1,4}[-/]\d{2,4})", text)
    cgst = _amount_after(text, r"cgst")
    sgst = _amount_after(text, r"sgst")
    igst = _amount_after(text, r"igst")
    txval = _amount_after(text, r"taxable")
    return Invoice(
        source="books",
        supplier_gstin=gstin_m.group(0) if gstin_m else "",
        invoice_no=inv_m.group(1) if inv_m else "",
        invoice_date=_parse_date(date_m.group(1)) if date_m else None,
        taxable_value=txval,
        cgst=cgst,
        sgst=sgst,
        igst=igst,
        extraction_confidence=0.5,
    )


def _amount_after(text: str, label: str) -> float:
    """Find the rupee amount near a label, skipping rate tokens like '9%'."""
    m = re.search(label, text, re.I)
    if not m:
        return 0.0
    tail = text[m.end(): m.end() + 40]
    # Prefer a properly formatted amount (decimal or thousands-separated).
    formatted = re.findall(r"[0-9][0-9,]*\.[0-9]{2}|[0-9]{1,3}(?:,[0-9]{2,3})+", tail)
    if formatted:
        return _to_float(formatted[0])
    # Fallback: a bare number that is not a percentage rate.
    m2 = re.search(r"([0-9][0-9,]*)(?!\s*%)", tail)
    return _to_float(m2.group(1)) if m2 else 0.0
