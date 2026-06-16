"""Vernacular copilot: explains mismatches, drafts vendor nudges, and prepares a
review-ready GSTR-3B ITC summary. LLM-powered when enabled, deterministic otherwise.
"""

from __future__ import annotations

from .llm import chat, is_enabled
from .models import MatchStatus, ReconLine, ReconResult


# ---------------------------------------------------------------- explain a line

def explain_line(line: ReconLine, language: str = "en") -> str:
    if is_enabled():
        out = chat(
            system=(
                "You are a friendly Indian GST advisor for small business owners. "
                "Explain the reconciliation issue in 2 short sentences, plain language, "
                f"in {'Hindi' if language == 'hi' else 'English'}. Be specific about the rupee impact."
            ),
            user=line.model_dump_json(),
            temperature=0.3,
        )
        if out:
            return out.strip()
    return _explain_offline(line, language)


def _explain_offline(line: ReconLine, language: str) -> str:
    hi = language == "hi"
    if line.status == MatchStatus.MISSING_IN_2B:
        return (
            f"आपके सप्लायर ने यह इनवॉइस ({line.invoice_no}) अभी तक GSTR-1 में फ़ाइल नहीं की है, "
            f"इसलिए ₹{line.itc_at_risk:,.0f} का ITC जोखिम में है। सप्लायर से फ़ाइल करवाएँ।"
            if hi
            else f"Your supplier has not yet filed invoice {line.invoice_no} in GSTR-1, "
            f"so ₹{line.itc_at_risk:,.0f} of ITC is at risk. Ask the supplier to file it."
        )
    if line.status == MatchStatus.AMOUNT_MISMATCH:
        return (
            f"इनवॉइस {line.invoice_no} में टैक्स का अंतर है (₹{line.tax_delta:,.0f})। "
            f"₹{line.itc_at_risk:,.0f} का ITC तब तक जोखिम में है जब तक मिलान न हो।"
            if hi
            else f"Tax on invoice {line.invoice_no} differs by ₹{line.tax_delta:,.0f}. "
            f"₹{line.itc_at_risk:,.0f} of ITC stays at risk until reconciled."
        )
    if line.status == MatchStatus.DUPLICATE:
        return (
            f"इनवॉइस {line.invoice_no} दो बार दर्ज है — दोहरा ITC क्लेम जोखिम। एक हटाएँ।"
            if hi
            else f"Invoice {line.invoice_no} is entered twice — duplicate ITC risk. Remove one."
        )
    if line.status == MatchStatus.MISSING_IN_BOOKS:
        return (
            f"यह इनवॉइस GSTR-2B में है पर आपकी बुक्स में नहीं — शायद ₹{line.gstr2b_tax:,.0f} ITC छूट रहा है।"
            if hi
            else f"This invoice is in GSTR-2B but not your books — you may be missing "
            f"₹{line.gstr2b_tax:,.0f} of claimable ITC."
        )
    return (
        f"इनवॉइस {line.invoice_no} मिल गया, ITC सुरक्षित है।"
        if hi
        else f"Invoice {line.invoice_no} matched; ITC is safe to claim."
    )


# ---------------------------------------------------------------- vendor nudge

def draft_vendor_nudge(line: ReconLine, buyer_name: str = "Our company", language: str = "en") -> str:
    if is_enabled():
        out = chat(
            system=(
                "Draft a short, polite WhatsApp message from a buyer to a supplier asking them "
                "to file/correct a GST invoice so the buyer can claim ITC. "
                f"Language: {'Hindi' if language == 'hi' else 'English'}. Keep under 60 words."
            ),
            user=f"Buyer: {buyer_name}. Issue: {line.reason} Invoice: {line.invoice_no}, "
            f"date {line.invoice_date}, ITC at risk ₹{line.itc_at_risk:,.0f}.",
            temperature=0.4,
        )
        if out:
            return out.strip()
    if language == "hi":
        return (
            f"नमस्ते {line.supplier_name or 'सर/मैम'}, इनवॉइस {line.invoice_no} "
            f"(दिनांक {line.invoice_date}) अभी तक GSTR-1 में नहीं दिख रही। कृपया जल्द फ़ाइल/सुधार करें "
            f"ताकि हम ₹{line.itc_at_risk:,.0f} का ITC क्लेम कर सकें। धन्यवाद — {buyer_name}"
        )
    return (
        f"Hi {line.supplier_name or 'there'}, invoice {line.invoice_no} "
        f"(dated {line.invoice_date}) isn't reflecting in GSTR-2B yet. Please file/correct it "
        f"so we can claim ₹{line.itc_at_risk:,.0f} of ITC. Thanks — {buyer_name}"
    )


# ---------------------------------------------------------------- GSTR-3B summary

def gstr3b_itc_summary(result: ReconResult) -> dict:
    """A review-ready Table 4 (ITC) style summary the user can sanity-check before filing."""
    s = result.summary
    eligible_now = s.total_itc_safe
    deferred = s.total_itc_at_risk
    return {
        "table_4A_itc_available_as_per_2b": round(
            sum(
                ln.gstr2b_tax
                for ln in result.lines
                if ln.status in (MatchStatus.MATCHED, MatchStatus.AMOUNT_MISMATCH, MatchStatus.MISSING_IN_BOOKS)
            ),
            2,
        ),
        "itc_claimable_now_safe": eligible_now,
        "itc_to_defer_at_risk": deferred,
        "itc_recoverable_via_followup": s.recoverable_itc,
        "advice": (
            f"Claim ₹{eligible_now:,.0f} now (matched ITC). Defer ₹{deferred:,.0f} until suppliers "
            f"file/correct — of which ₹{s.recoverable_itc:,.0f} is recoverable with follow-up."
        ),
    }
