# GST Compliance & Cashflow Copilot for MSMEs

An AI "accountant" for India's ~5M GST-registered MSMEs. It ingests invoices, reconciles
them against **GSTR-2B**, surfaces the **Input Tax Credit (ITC) you are silently losing**,
explains each issue in **Hindi/English**, and drafts supplier follow-ups — then prepares a
review-ready **GSTR-3B** ITC summary.

> Built as a Make-in-India prototype within a ₹2 lakh budget, fundable via the
> DPIIT → SISFS → Mudra/CGTMSE ladder. See `funding/funding_checklist.md`.

The whole prototype **runs fully offline** (no API keys needed). Add an LLM key to upgrade
extraction + the copilot from deterministic templates to a real model.

---

## What's inside

| Path | What |
| --- | --- |
| `backend/` | FastAPI app, extraction, reconciliation + ITC engine, GST rules, copilot, store |
| `pipeline/` | Prefect batch flow (monthly per-tenant reconciliation) |
| `frontend/` | React + Vite + Tailwind dashboard (exception queue, copilot, audit trail) |
| `data/` | Synthetic sample data + generator (`generate_samples.py`) |
| `deck/` | Investor pitch deck (Markdown source + `python-pptx` generator) |
| `research/` | Market validation + discovery-call script |
| `funding/` | DPIIT/SISFS/Mudra/CGTMSE action checklist |
| `tests/` | Engine + extraction tests |

## Architecture

```
Invoices (PDF/img/xlsx/Tally) ─┐
                               ├─► Extraction ─► Reconciliation + ITC engine ─► Copilot ─► Dashboard
GSTR-2B (GSP API / upload) ────┘                         │                                  + Audit trail
                                                  GST rules engine                          + GSTR-3B summary
```

## Quickstart

### 1. Backend
```bash
cd gst-copilot
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python data/generate_samples.py          # create demo data
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

### 2. Frontend
```bash
cd gst-copilot/frontend
npm install
npm run dev
# open http://localhost:5173 and click "Run demo audit"
```

### 3. Run the pipeline directly (no server)
```bash
python -m pipeline.flows
```

### 4. Tests
```bash
python -m pytest tests -q
```

### 5. Build the pitch deck
```bash
python deck/build_deck.py   # -> deck/GST_Copilot_Pitch.pptx
```

## Enabling the LLM copilot (optional)
```bash
cp .env.example .env
# set LLM_PROVIDER=openai and OPENAI_API_KEY=...
```
Without this, explanations and vendor nudges use deterministic Hindi/English templates,
and invoice extraction uses a regex fallback — so demos never fail offline.

## Demo script (for investors)
1. `Run demo audit` → headline: **₹36,900 ITC at risk, ₹28,800 recoverable**.
2. Open the **Exceptions** tab → show a "supplier not filed" line.
3. Click **Explain** (switch to हिन्दी) → vernacular explanation.
4. Click **Draft nudge** → ready-to-send WhatsApp message to the supplier.
5. Approve/reject lines → show the **audit trail** updating.
6. Show the **GSTR-3B advice**: claim now vs defer vs recoverable.

## Roadmap
- GSP/ASP live integration (auto-fetch GSTR-2B).
- Vernacular **voice** copilot via Bhashini.
- Vendor-behaviour ITC-risk score; TDS/GSTR-1 modules.
- Postgres-backed multi-tenant store (the `store.py` surface is already swappable).
