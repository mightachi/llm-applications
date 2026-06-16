# GST Copilot — Investor Pitch Deck (source)

> This Markdown is the single source of truth for the deck. Run `python deck/build_deck.py`
> to generate `deck/GST_Copilot_Pitch.pptx`. One slide per `## Slide` heading.
> Speaker notes go under a `Notes:` block and are embedded into the PPTX notes pane.

---

## Slide 1 — Title
**GST Copilot**
Recover the Input Tax Credit India's MSMEs are silently losing.

Founder: <Your name> · ex-MLE / Data Engineer (10 yrs) · Make in India
<contact / email / phone>

Notes: One-liner pitch. We are an AI accountant that finds and recovers lost ITC for small businesses. Keep this to 20 seconds.

---

## Slide 2 — The Problem
- Reconciling the purchase register against GSTR-2B is manual, monthly, and painful.
- MSMEs lose up to **60% of ITC** on non-recurring spend and ~**₹12,000/month** to invoice errors.
- ~**20%** of SME invoices get rejected by GSTN (wrong GSTIN/HSN/date) → notices, penalties.
- Compliance eats **15–25%** of SME operating time; ₹5–15 lakh/year per business.

Notes: Lead with the pain in rupees. Every owner in the room has felt this. Tell one concrete anecdote from discovery calls.

---

## Slide 3 — Why now
- e-invoicing threshold dropping to **₹2 crore** turnover → millions more MSMEs pulled in.
- GSTN now runs **real-time analytics**, auto-flagging GSTR-1 vs 3B mismatches.
- 57%+ of internet users are rural; vernacular, voice-first interfaces finally viable.
- AI OCR + LLMs make accurate extraction cheap enough to serve a ₹999/month customer.

Notes: The regulatory squeeze is the tailwind. "Fix it later" is no longer an option for MSMEs.

---

## Slide 4 — The Solution
An AI "accountant" that runs the full loop:
1. **Ingest** invoices (PDF/photo/Excel/Tally) + auto-fetch GSTR-2B.
2. **Reconcile** every line; flag mismatches, unfiled suppliers, duplicates.
3. **Quantify** ITC that is safe vs at risk vs recoverable.
4. **Act**: explain each issue in Hindi/English, draft supplier follow-ups, prep GSTR-3B.

Notes: Show the product screenshot here. The headline number "₹X at risk" is the hook.

---

## Slide 5 — Product / Live demo
- Demo: upload last quarter → instant **"₹36,900 ITC at risk, ₹28,800 recoverable"**.
- Exception queue with one-click vendor nudge + human-in-the-loop review + audit trail.
- Vernacular copilot explains *why* in the owner's language.

Notes: Run the actual demo if possible. Fall back to screenshots. Emphasise time-to-value: under 5 minutes.

---

## Slide 6 — Market
- ~**5.0M** GST-registered businesses in India.
- Accounting/compliance software: **~$780M (2026) → ~$2.13B (2035)**, ~11.8% CAGR.
- TAM 5.0M businesses · SAM ~0.8–1.2M mid-MSMEs · SOM (3–5 yr) ~50,000 paying accounts ≈ **₹90 cr ARR**.

Notes: Bottom-up, not top-down. 1% of serviceable base at a modest ACV already builds a real company.

---

## Slide 7 — Business model
| Tier | Price (₹/mo) | For |
| --- | --- | --- |
| Audit | Free | Lead magnet — one-time leakage audit |
| Starter | 999 | Micro MSME, ≤200 invoices |
| Growth | 2,499 | Mid MSME, vendor nudges, 3 GSTINs |
| Practice | 7,999+ | CA multi-client cockpit |

If we recover ₹15–20k/month of ITC, a ₹2,499 plan is >5x ROI.

Notes: We sell recovered cash, not software. ROI sells itself.

---

## Slide 8 — Go-to-market
- **Free ITC-leakage audit** as top of funnel.
- **CA channel partners**: one CA = dozens of MSME clients; revenue share.
- **MSME clusters & associations** in Maharashtra + Gujarat first (highest cloud adoption).
- Vernacular content: "ITC bachao".

Notes: CAs are the wedge — they are trusted, and they hate manual reconciliation too.

---

## Slide 9 — Competition & moat
| Player | Gap we exploit |
| --- | --- |
| ClearTax | Mid/enterprise-priced, English-first |
| Zoho Books | Reconciliation is a feature, not recovery |
| Cygnet IMS | Enterprise sales, overkill for MSMEs |
| Tally add-ons | Desktop-bound, no AI copilot |

Moat: reconciliation engine tuned on real Indian invoice/vendor data + vendor-behaviour risk score + vernacular copilot.

Notes: We don't replace Tally; we read it and the GSTN, and hand back cash.

---

## Slide 10 — Traction & validation
- <N> discovery calls; median reported leakage ₹<X>/month.
- <M> design partners signed; ₹<Y> ITC surfaced in pilots.
- Working prototype (this demo) reconciles real GSTR-2B data today.

Notes: Fill with real numbers as you gather them. Even 5 design partners + a working demo is strong at pre-seed.

---

## Slide 11 — Team
- Founder: 10 years as MLE + Data Engineer — reconciliation/extraction is exactly our domain.
- Advisors: <CA / tax expert>, <GTM advisor>.
- Hiring plan tied to SISFS milestones.

Notes: Your unfair advantage is the data-engineering depth. Most GST tools are built by accountants, not ML engineers.

---

## Slide 12 — Funding ask & use of funds
- Self-funded **₹2 lakh** prototype (built — you're seeing it).
- Seeking **SISFS grant up to ₹20 lakh** (prototype → product trials, milestone-based).
- Then **Mudra (≤₹20L) / CGTMSE (collateral-free)** for go-to-market.
- Use of funds: GSP integration, design-partner rollout, 1 ML + 1 GTM hire, compliance/DPDP.

Notes: Map each rupee to a SISFS milestone (prototype, product testing, market-ready). Investors love the de-risked govt-grant ladder.

---

## Slide 13 — Roadmap & vision
- Q1: GSP live, 25 paying MSMEs, CA pilot.
- Q2: vernacular **voice** copilot (Bhashini), TDS/GSTR-1 modules.
- Q3+: vendor-behaviour ITC-risk score, financing on recovered ITC.
- Vision: the financial-ops brain for every Indian MSME.

Notes: Land with reconciliation, expand to the full compliance + cashflow OS.
