# GST Compliance & Cashflow Copilot — Market & Use-Case Validation

> Working thesis: Indian MSMEs silently lose Input Tax Credit (ITC) every month because
> reconciling their purchase register against `GSTR-2B` is manual, error-prone, and
> English-first. We sell **recovered cash**, not "software".

---

## 1. The problem (quantified)

| Pain | Evidence | Cost to an MSME |
| --- | --- | --- |
| Manual `GSTR-2B` vs purchase-register reconciliation | Most common monthly compliance task; done in Excel | 1–3 days/month of accountant time |
| ITC leakage on non-recurring spend | Up to ~60% of ITC lost when matching is manual | Thousands of ₹ per month, permanently |
| Invoice data-entry errors / duplication | ~₹12,000/month average loss | Direct cash + rework |
| GSTN rejections (wrong GSTIN/HSN/date) | ~20% of SME invoices rejected | ITC mismatch → notice → penalty chain |
| Compliance overhead | 15–25% of SME operating time; ₹5–15 lakh/year (staff + CA + tools) | Opportunity cost |
| e-invoicing threshold dropping to ₹2 crore | Real-time GSTN analytics now auto-flag GSTR-1 vs 3B mismatches | Compliance risk rising fast |

**Wedge:** "Run a free ITC-leakage audit on last quarter — see exactly how much credit you lost."
This is measurable, urgent, and converts to a paid subscription once trust is established.

---

## 2. Market sizing

- ~5.0M GST-registered businesses in India (serviceable digital base growing with e-invoicing).
- India accounting & budgeting software market: **~$780M (2026) → ~$2.13B (2035)**, ~11.8% CAGR.
- Bottom-up TAM (our slice): 5.0M businesses × ~₹50,000/yr blended ACV ceiling is the optimistic cap;
  a realistic SOM at 1% penetration of paying MSMEs (~50,000 accounts) × ₹18,000/yr ≈ **₹90 crore ARR**.

| Layer | Definition | Size |
| --- | --- | --- |
| TAM | All GST-registered businesses needing reconciliation | ~5.0M businesses |
| SAM | MSMEs ₹2–50 cr turnover, 100+ suppliers, cloud-willing | ~0.8–1.2M businesses |
| SOM (3–5 yr) | 1% of SAM as paying subscribers | ~50,000 accounts |

---

## 3. Ideal Customer Profile (ICP)

**Primary ICP — "The leaking mid-MSME"**
- Turnover ₹2–50 crore (e-invoicing already or soon mandatory).
- 100–500+ suppliers, 200–1,000+ purchase invoices/month.
- 1–2 in-house accounts staff + an external CA.
- Uses Tally/Busy/Excel; invoices arrive as PDF, scan, photo, and email.
- Decision maker: owner/promoter or finance head. Influencer/blocker: their CA.

**Secondary ICP — "The CA / tax practitioner"**
- Manages 30–200 GST clients. Wants a multi-client reconciliation cockpit.
- Becomes our distribution channel (one CA = many MSMEs).

---

## 4. Competitor teardown & positioning

| Player | Strength | Gap we exploit |
| --- | --- | --- |
| ClearTax | Strong filing + reconciliation, brand, GSP | Mid/enterprise-priced; English-first; ITC-recovery not the headline |
| Zoho Books | Full accounting suite, cheap | Reconciliation is a feature, not a recovery engine; no vernacular copilot |
| Cygnet IMS | Enterprise-grade IMS, scales to 100k+ invoices | Enterprise sales motion; overkill + costly for small MSMEs |
| Tally + add-ons | Ubiquitous desktop install base | Desktop-bound; bolt-on reconciliation; no AI copilot |
| Nanonets (OCR) | Best-in-class invoice OCR | A component, not an end-to-end GST/ITC outcome |

**Our positioning:** *ITC-recovery-first, vernacular, MSME-priced, CA-distributed.*
We do not try to replace Tally — we **read** Tally exports and the GSTN, and hand back recovered cash + a review-ready return.

**Moat (compounding):**
1. Reconciliation + ITC engine tuned on real Indian invoice/vendor-behaviour data (the data-engineering IP).
2. Vendor-behaviour graph (who files late, who never files) → predictive ITC-risk score.
3. Vernacular copilot that explains *why* in the owner's language → trust + retention.

---

## 5. Pricing hypothesis

| Tier | Target | Price (₹/mo) | Limits |
| --- | --- | --- | --- |
| Audit (lead magnet) | First-touch | Free | One-time leakage audit on uploaded data |
| Starter | Micro MSME | 999 | ≤ 200 invoices/mo, 1 GSTIN |
| Growth | Mid MSME | 2,499 | ≤ 1,000 invoices/mo, 3 GSTINs, vendor nudges |
| Practice | CA / multi-client | 7,999+ | Multi-client cockpit, 25 GSTINs, white-label |

Value framing: if we recover even ₹15–20k/month of ITC, a ₹2,499 plan is a >5x ROI — easy sell.

---

## 6. Go-to-market

1. **Free ITC-leakage audit** as the top of funnel (upload last quarter's data → instant "₹X recovered" report).
2. **CA channel partnerships** — one CA onboards dozens of MSME clients; revenue-share.
3. **MSME clusters / industry associations** (Maharashtra & Gujarat first — highest cloud-accounting adoption).
4. Content in Hindi + regional languages on "ITC bachao" (save your ITC).

---

## 7. Validation plan (do before/while building)

- 8–10 discovery calls (5 MSME owners/finance heads + 3–5 CAs). Script in `discovery_call_script.md`.
- For each: quantify (a) hours/month on reconciliation, (b) estimated ITC lost last year, (c) current tool, (d) willingness to pay.
- Success signal to proceed: ≥ 6/10 report >₹10k/month leakage AND ≥ 4/10 verbally commit to a paid pilot.
- Recruit 3–5 **design partners** who give real (anonymised) data for the prototype demo.

---

## 8. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| GSP/ASP API access delay | Ship with manual `GSTR-2B` JSON upload; integrate GSP in parallel |
| Data privacy (DPDP Act) | Consent + audit trail + data-residency; never train on client data without opt-in |
| Incumbents add ITC-recovery framing | Win on price, vernacular, CA channel, and speed-to-value |
| Extraction accuracy on poor scans | Human-in-the-loop exception queue; confidence thresholds |
