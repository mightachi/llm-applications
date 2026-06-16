"""GST domain rules used by the reconciliation engine.

These are intentionally explicit and auditable (no black-box ML) so a CA can defend
every decision. Covers: GSTIN structure validation, intra/inter-state classification,
a pragmatic subset of Section 17(5) blocked-credit detection, and tax-consistency checks.
"""

from __future__ import annotations

import re

# State code (first 2 digits of GSTIN) -> state name. Subset; extend as needed.
GST_STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana", "07": "Delhi",
    "08": "Rajasthan", "09": "Uttar Pradesh", "10": "Bihar", "19": "West Bengal",
    "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat", "27": "Maharashtra",
    "29": "Karnataka", "32": "Kerala", "33": "Tamil Nadu", "36": "Telangana",
    "37": "Andhra Pradesh",
}

# GSTIN: 2 state digits + 10-char PAN + 1 entity + 'Z' + 1 checksum char.
_GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")

# Pragmatic Section 17(5) blocked-credit keywords (description-based heuristic).
_BLOCKED_KEYWORDS = (
    "motor vehicle", "car ", "food", "beverage", "catering", "membership",
    "club", "health insurance", "life insurance", "travel benefit", "personal",
)


def is_valid_gstin(gstin: str) -> bool:
    return bool(_GSTIN_RE.match((gstin or "").strip().upper()))


def state_code(gstin: str) -> str | None:
    g = (gstin or "").strip()
    return g[:2] if len(g) >= 2 else None


def state_name(gstin: str) -> str | None:
    return GST_STATE_CODES.get(state_code(gstin) or "")


def is_interstate(supplier_gstin: str, buyer_gstin: str) -> bool:
    """Inter-state when supplier and buyer state codes differ -> IGST expected."""
    s, b = state_code(supplier_gstin), state_code(buyer_gstin)
    if not s or not b:
        return False
    return s != b


def is_blocked_credit(description: str | None, hsn: str | None = None) -> bool:
    """Heuristic Section 17(5) check on the line description."""
    text = (description or "").lower()
    return any(k in text for k in _BLOCKED_KEYWORDS)


def tax_split_is_consistent(
    supplier_gstin: str, buyer_gstin: str, cgst: float, sgst: float, igst: float
) -> bool:
    """Inter-state should use IGST only; intra-state should use CGST+SGST only."""
    interstate = is_interstate(supplier_gstin, buyer_gstin)
    has_igst = igst > 0.01
    has_cgst_sgst = (cgst > 0.01) or (sgst > 0.01)
    if interstate:
        return has_igst and not has_cgst_sgst
    return has_cgst_sgst and not has_igst
