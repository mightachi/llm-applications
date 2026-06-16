"""FastAPI app wiring the ingest -> reconcile -> copilot loop into a demoable API.

Run:  uvicorn backend.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import __version__
from .copilot import draft_vendor_nudge, explain_line, gstr3b_itc_summary
from .extraction import parse_gstr2b_json, parse_purchase_register_csv
from .llm import is_enabled
from .models import ReconLine, ReconResult
from .reconcile import reconcile
from .store import STORE

app = FastAPI(title="GST Compliance & Cashflow Copilot", version=__version__)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Run-Id"],
)


import json
import os

_SAMPLES = os.path.join(os.path.dirname(__file__), "..", "data", "samples")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "llm_enabled": is_enabled()}


@app.post("/demo", response_model=ReconResult)
def demo(response: Response, tenant: str = "demo") -> ReconResult:
    """One-click reconciliation on the bundled synthetic dataset (for the frontend demo)."""
    with open(os.path.join(_SAMPLES, "purchase_register.csv"), encoding="utf-8-sig") as f:
        books = parse_purchase_register_csv(f.read())
    with open(os.path.join(_SAMPLES, "gstr2b.json"), encoding="utf-8-sig") as f:
        twob = parse_gstr2b_json(json.load(f))
    result = reconcile(books, twob)
    run_id = STORE.save_run(result, tenant=tenant)
    response.headers["X-Run-Id"] = run_id
    return result


@app.post("/reconcile", response_model=ReconResult)
async def reconcile_endpoint(
    response: Response,
    purchase_register: UploadFile = File(..., description="Purchase register CSV"),
    gstr2b: UploadFile = File(..., description="GSTR-2B JSON"),
    tenant: str = Form("demo"),
) -> ReconResult:
    try:
        books = parse_purchase_register_csv((await purchase_register.read()).decode("utf-8-sig"))
        twob = parse_gstr2b_json((await gstr2b.read()).decode("utf-8-sig"))
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Could not parse inputs: {e}") from e
    result = reconcile(books, twob)
    run_id = STORE.save_run(result, tenant=tenant)
    response.headers["X-Run-Id"] = run_id  # frontend reads this to fetch follow-ups
    return result


@app.get("/runs")
def list_runs() -> dict:
    return {"runs": STORE.list_runs()}


@app.get("/runs/{run_id}")
def get_run(run_id: str) -> dict:
    run = STORE.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run


@app.get("/runs/{run_id}/gstr3b")
def gstr3b(run_id: str) -> dict:
    run = STORE.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return gstr3b_itc_summary(ReconResult.model_validate(run["result"]))


class ExplainRequest(BaseModel):
    line: ReconLine
    language: str = "en"


@app.post("/explain")
def explain(req: ExplainRequest) -> dict:
    return {"explanation": explain_line(req.line, req.language)}


class NudgeRequest(BaseModel):
    line: ReconLine
    buyer_name: str = "Our company"
    language: str = "en"


@app.post("/nudge")
def nudge(req: NudgeRequest) -> dict:
    return {"message": draft_vendor_nudge(req.line, req.buyer_name, req.language)}


class ReviewRequest(BaseModel):
    line_index: int
    state: str  # "approved" | "rejected" | "follow_up_sent"
    note: str = ""


@app.post("/runs/{run_id}/review")
def review(run_id: str, req: ReviewRequest) -> dict:
    ok = STORE.review_line(run_id, req.line_index, req.state, req.note)
    if not ok:
        raise HTTPException(status_code=404, detail="run not found")
    return {"ok": True}


@app.get("/audit")
def audit(run_id: str | None = None) -> dict:
    return {"audit": STORE.audit_trail(run_id)}
