# LLM Applications Curriculum — Exercise Workbook & Exit-Criterion Tests

**Companion document to the 7-month Production LLM Applications curriculum.**

For each phase: concrete exercises with measurable success criteria, plus an **Exit-Criterion Test** — a specific scenario that verifies you can actually do what the phase claims you can do. If you can pass the exit test, move on. If you can't, the phase isn't done, regardless of how much time you've spent.

---

## Phase 0 — Prerequisites

### Exercises

**Exercise 0.1 — Async I/O Warmup**
Write a Python script that fetches 20 URLs concurrently using `httpx.AsyncClient`. Compare elapsed time to a sequential version. Add per-request timeouts, error handling, and use `asyncio.Semaphore(5)` to cap concurrency.
- **Success criteria:** Total elapsed time is approximately the latency of the *slowest* request, not the sum of all requests. The semaphore demonstrably limits in-flight requests.

**Exercise 0.2 — FastAPI CRUD**
Build a `tasks` API with five endpoints: `POST /tasks`, `GET /tasks`, `GET /tasks/{id}`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`. Use Pydantic models for request and response. Add a `GET /tasks?status=pending&limit=10` filter and an SSE endpoint `GET /tasks/stream` that streams creation events.
- **Success criteria:** All endpoints work, the auto-generated OpenAPI docs at `/docs` correctly describe every route, and the SSE endpoint streams events in real time when you POST a task in another terminal.

**Exercise 0.3 — Containerize It**
Write a multi-stage `Dockerfile`. Build stage installs dependencies (use `uv` or `poetry`); runtime stage uses a slim Python base and copies only what's needed. Image must be under 200MB.
- **Success criteria:** `docker run -p 8000:8000 mytasks` works end-to-end. Run `docker images` and verify size.

**Exercise 0.4 — Postgres Integration**
Add SQLAlchemy with the `asyncpg` driver. Use Alembic for migrations. Define the `tasks` table with indexes on `status` and `created_at`. A JSONB column for `metadata`. Wire it into the API.
- **Success criteria:** Data survives container restarts. The `?status=pending` query uses an index (verify with `EXPLAIN ANALYZE`).

**Exercise 0.5 — Docker Compose Stack**
Write `docker-compose.yml` with three services: `app`, `postgres`, `redis`. Add health checks. Use environment variables for all config (no hardcoded passwords). The app must wait for Postgres to be healthy before starting.
- **Success criteria:** `docker compose up` brings up the whole stack; `docker compose down` cleans up completely. Killing and restarting Postgres alone doesn't crash the app permanently (it reconnects).

**Exercise 0.6 — Redis Caching & Rate Limiting**
Cache `GET /tasks/{id}` in Redis with a 60-second TTL. Invalidate on PATCH/DELETE. Add an IP-based rate limiter: 10 requests per minute per IP, returns HTTP 429 with `Retry-After` when exceeded.
- **Success criteria:** Cache hits and misses are logged. Hitting the endpoint 11 times in 60 seconds returns 429 on the 11th. Updating a task immediately reflects in the next GET (proves invalidation works).

### Exit-Criterion Test: The 90-Minute URL Shortener

**Scenario:** Empty directory. Timer starts. In under 90 minutes, ship:

A URL shortener service with these endpoints:
- `POST /shorten {url}` → returns `{short_code, short_url}`
- `GET /{short_code}` → 302 redirect to the original URL
- `GET /{short_code}/stats` → returns `{hits, created_at, original_url}`

Backed by:
- Postgres: persistent `urls` table (id, short_code, original_url, created_at)
- Redis: hit counter (incremented per redirect, flushed to Postgres every 60 seconds)

Packaged as:
- Multi-stage Dockerfile
- `docker-compose.yml` with health checks
- At least one passing pytest unit test

**Pass criterion:** You finish in under 90 minutes, all endpoints work, and the stack comes up cleanly on a fresh machine via `docker compose up`. If you missed the time, redo the exercises above before moving to Phase 1.

---

## Phase 1 — LLM API Mastery & Prompt Engineering

### Exercises

**Exercise 1.1 — Multi-Provider Abstraction**
Build a small Python package `llm_router` exposing one interface: `await generate(prompt, model: str, **kwargs) -> CompletionResponse` where `CompletionResponse` includes `text`, `tokens_in`, `tokens_out`, `cost_usd`, `latency_ms`. Support four backends: OpenAI, Anthropic, Google Gemini, and one OpenRouter-hosted open-source model. Streaming must work uniformly via an async generator.
- **Success criteria:** The same call signature with only the model string changed works across all four providers, with accurate token and cost accounting per provider.

**Exercise 1.2 — Model Benchmark Spreadsheet**
Task: extract `{company_name, founding_year, hq_city}` from the first paragraph of 50 Wikipedia "company" articles. Hand-label ground truth. Benchmark 7+ models (frontier, mid-tier, small, plus one open-source 70B-class). For each: cost per call, p50/p95 latency over 50 runs, accuracy.
- **Success criteria:** A spreadsheet with all numbers. You can name the optimal model for this task with a one-sentence cost/quality justification.

**Exercise 1.3 — Prompt Caching ROI**
Pick a long-document workflow: load a 50K-token document, ask 25 different questions about it. Implement once without prompt caching, once with explicit `cache_control` (Anthropic) or prefix-stable structure (OpenAI/Gemini). Measure total cost both ways.
- **Success criteria:** Cost reduction of at least 70% with caching enabled, with no accuracy degradation.

### Exit-Criterion Test: The 10-Minute Model Selection Drill

**Scenario:** I (or a peer) hand you 5 use cases on a piece of paper. You have 10 minutes total.

Example use cases:
1. Real-time customer support intent classifier (10K requests/minute peak)
2. Weekly investment-research summarizer (200 long PDFs/week, output ~2 pages each, runs Sunday night)
3. Code-review bot for PRs in a large open-source Python project
4. Voice-assistant intent + entity extractor (must respond in <300ms TTFT)
5. Legal contract clause-by-clause risk analysis (50-page contracts, accuracy critical, cost less critical)

For each, write in 2 minutes:
- Chosen model (specific version)
- Estimated cost per request
- Expected p95 latency
- One-sentence justification

**Pass criterion:** Five reasoned answers in 10 minutes. The cost estimates are within 2x of reality. Each justification mentions at least one of: latency budget, cost ceiling, output token volume, accuracy requirement.

---

## Phase 2 — Structured Outputs & Function Calling

### Exercises

**Exercise 2.1 — Contact Card Extractor**
Build a Pydantic-schema-validated extractor that parses messy text (email signatures, LinkedIn bios, business cards transcribed by OCR) into `{name, title, company, email, phone, links[]}`. Test set: 100 hand-collected messy inputs covering edge cases (multiple phones, international formats, missing fields, typos).
- **Success criteria:** >99% JSON validity, >95% field-level accuracy on the test set. Self-correction loop on validation failure (re-ask with the error in context) is implemented and demonstrably helps.

**Exercise 2.2 — Tool-Selection Stress Test**
Build an agent with 5 tools: `weather(city)`, `calculator(expression)`, `current_time(timezone)`, `web_search(query)`, `file_read(path)`. Curate 50 test queries: 30 single-tool-obvious, 10 tool-ambiguous, 10 multi-tool. Run across 3 providers (OpenAI, Anthropic, Gemini).
- **Success criteria:** A per-provider accuracy table. Documented failure mode taxonomy (e.g., "Gemini calls `web_search` when `current_time` would suffice 4/10 times"). At least one mitigation per documented failure mode.

**Exercise 2.3 — Self-Healing Extraction**
Extraction target: natural-language calendar requests → structured event objects (`{title, start, end, all_day, recurrence, attendees[], location, reminders[]}`). Include adversarial inputs: "every other Friday except Fed holidays", "next Tuesday but actually Wednesday", "block 2 hours sometime Thursday afternoon".
- **Success criteria:** >99.5% final JSON validity after retry loop (allow up to 3 retries with error feedback). Track and report average retry count — should converge to <1.2 attempts.

### Exit-Criterion Test: Email-Invitation Parser

**Scenario:** Parse 200 real (or hand-crafted) email invitations into a structured event object with all fields above, including correctly handling:
- All-day vs. timed
- Recurrence rules (RFC 5545 RRULE format)
- Multiple time zones
- Virtual meeting links (Zoom, Meet, Teams) vs. physical addresses
- Implicit reminders ("the day before")

**Pass criterion:** >99.5% JSON validity, >90% per-field accuracy averaged across all fields, with documented breakdown per field. Code is production-shaped (Pydantic schemas, typed, tested, with the retry loop instrumented in logs).

---

## Phase 3 — Embeddings, Vector Search & RAG Foundations

### Exercises

**Exercise 3.1 — Embedding Model Bake-Off**
Pick a domain corpus (10K docs minimum — arXiv abstracts in an area you know, FDA approval letters, your own Confluence wiki). Build a 100-query golden set with hand-labeled relevant doc IDs. Benchmark 5 embedding models on recall@5, recall@10, MRR.
- **Success criteria:** Spreadsheet with metrics + cost per million tokens for each. Defensible recommendation with rationale.

**Exercise 3.2 — Vector Store Trade-Off Study**
Index the same 10K-doc corpus in three vector stores: Pinecone (managed), Qdrant (self-hosted), Postgres + `pgvector`. Measure indexing time, query p95 latency at 100 QPS load, monthly cost projection at 1M and 100M doc scale.
- **Success criteria:** Documented recommendation that names break-even points (e.g., "use pgvector below 5M docs, switch to Qdrant above").

**Exercise 3.3 — Chunking Ablation**
Same corpus, same eval set. Compare four strategies: 512-token fixed, 1024-token with 128 overlap, recursive (langchain `RecursiveCharacterTextSplitter`), semantic (embedding-similarity-driven).
- **Success criteria:** Plot of recall@5 across strategies, plus a written explanation of *why* one wins for this corpus (not just *that* it wins).

### Exit-Criterion Test: Weekend RAG Build

**Scenario:** Friday 6pm. Pick a corpus you have never touched. Examples: all SEC 10-K filings of S&P 500 companies for 2025, the complete Linux kernel mailing list archive for the last year, all Federal Reserve speeches since 2015. By Sunday 6pm, deliver:

- A deployed (even if just locally containerized) RAG service over the corpus
- A simple web UI (Gradio is fine) for asking questions
- A README documenting: corpus stats, chunking choice, embedding model choice, vector store choice — with brief reasoning for each
- 20 example queries with returned answers, manually scored as good/partial/bad

**Pass criterion:** It works end-to-end on a fresh machine. At least 14/20 answers are "good." You can defend every architectural choice without saying "I just used what the tutorial said."

---

## Phase 4 — Advanced RAG

### Exercises

**Exercise 4.1 — Hybrid Search + Reranking**
On your Phase 3 system, add: BM25 in parallel with dense retrieval (use `rank_bm25` or Elasticsearch), then a cross-encoder reranker on the union (Cohere Rerank v3+ or BGE-reranker-large). Tune the dense/sparse weighting on a held-out 50-query set.
- **Success criteria:** Documented recall@5 improvement of at least 20% over the dense-only baseline.

**Exercise 4.2 — Query Router**
Classify queries into 4 types appropriate for your domain (e.g., factual, comparative, summary, time-bound). Build a classifier using a fast small model with few-shot prompting. Route each type to a tailored retrieval pipeline.
- **Success criteria:** Per-category recall@5 is measurably higher than the monolithic-retrieval baseline for at least 3 of the 4 categories.

**Exercise 4.3 — Contextual Retrieval (Anthropic Pattern)**
For each chunk, generate a 1–2 sentence context paragraph describing where it sits in the parent document, using a cheap model. Prepend this context before embedding. Use prompt caching aggressively to keep the indexing cost manageable.
- **Success criteria:** Indexing cost per document documented. Quality improvement on eval set documented. Net recommendation: "use this when X, skip when Y" — based on measured cost/benefit.

**Exercise 4.4 — Ragas in CI**
Build a 50-query golden set with reference answers. Set up Ragas computing faithfulness, answer relevance, context precision, context recall. Wire it into GitHub Actions: every PR runs eval, posts results as a PR comment, blocks merge if any metric drops more than 5%.
- **Success criteria:** A deliberately bad PR (e.g., reducing retrieval top-k from 10 to 2) actually gets blocked.

### Exit-Criterion Test: The Broken RAG Diagnosis

**Scenario:** I (or a peer) give you a RAG system that's failing 30% of the time on its eval set. You have access to: the code, the eval set with model outputs, and the trace logs. You have 4 hours.

Your job:
1. Diagnose whether the failure is in (a) retrieval, (b) reranking/filtering, (c) prompt construction, or (d) generation
2. Provide evidence from the data — not just intuition
3. Propose a concrete fix (does not need to be implemented)
4. Predict the expected improvement from the fix and justify the number

**Pass criterion:** Root cause correctly identified, evidence cited from at least 5 specific failing examples, fix proposal is concrete and defensible, prediction is within 30% of the actual improvement when the fix is applied.

---

## Phase 5 — Single-Agent Architectures

### Exercises

**Exercise 5.1 — ReAct from Scratch**
~200 lines of Python, no agent framework. Three tools: `web_search` (use Tavily or Brave), `calculator`, `python_exec` (sandboxed via subprocess timeout, or just `eval` on trusted input). Task: "How many active Wikipedia editors are there this month, and how does that compare to a year ago? What's the percent change?"
- **Success criteria:** Agent reaches a correct numerical answer with at least one citation. Full reasoning trace is logged and human-readable.

**Exercise 5.2 — Reflection Layer**
Add a reflection step after each tool call: "Did this result advance the goal? What should I do next?" Run the same 20 tasks with and without reflection. Compare quality, total LLM cost, total wall time.
- **Success criteria:** Documented tradeoff — reflection helps on X type of task, hurts (or wastes money) on Y type.

**Exercise 5.3 — Budget Bounding**
Add hard limits: max 10 tool calls per run, max $0.50 spend per run, max 60 seconds wall time. Implement graceful early termination: when a limit is hit, the agent returns whatever partial result it has plus a clear "I had to stop early because..." message.
- **Success criteria:** Test with an adversarial query designed to loop indefinitely. Agent stops cleanly with a useful partial result, not a crash.

**Exercise 5.4 — Durable Execution**
Wrap the agent in a Temporal workflow (or Inngest, or restate.dev). While a long-running agent task is executing, kill the worker process. Restart it.
- **Success criteria:** Workflow resumes from the last completed activity, doesn't re-execute already-completed tool calls.

### Exit-Criterion Test: The Daily-Brief Agent

**Scenario:** Build a "person brief" agent. Input: a person's name and role/context. Output: a 5-paragraph written briefing suitable for a meeting prep — career, recent public statements, notable achievements, current focus, conversation hooks.

Constraints:
- < $0.10 per brief in LLM + tool costs
- < 30 seconds end-to-end wall time
- No hallucinated facts (every concrete claim must trace to a tool result)
- Tools available: web search, news search, optionally one more of your choice

**Test set:** 20 people across politicians, executives, academics, athletes, authors. Manually grade each brief: useful / partial / unusable. Score each fact for hallucination (cross-check against tool outputs).

**Pass criterion:** 17/20 briefs are "useful." Zero hallucinated concrete facts across all 20. Average cost and latency within budget.

---

## Phase 6 — Multi-Agent Systems

### Exercises

**Exercise 6.1 — State-Machine Multi-Agent (No Framework)**
Three agents — planner, executor, reviewer — implemented as a hand-rolled Python state machine. Task: "Write a 500-word blog post on a given topic with at least 3 verified factual claims and at least one cited source per claim."
- **Success criteria:** Works on 10 different topics. Output post quality is at least readable (you'd publish it on a personal blog). Every factual claim has a traceable source.

**Exercise 6.2 — Same Thing in LangGraph**
Reimplement Exercise 6.1 in LangGraph. Document side-by-side: lines of code, debuggability (try injecting a bug in each version — how long does it take to find?), ease of adding a new agent.
- **Success criteria:** Honest written comparison. The right answer might be "framework helps" or "framework gets in the way" — what matters is you have evidence either way.

**Exercise 6.3 — Distributed Tracing**
Add LangFuse or Phoenix to your multi-agent system. For each run, log: every LLM call, every tool call, every agent-to-agent transition, costs and latencies for each.
- **Success criteria:** Given any failed run, you can diagnose where it failed in under 5 minutes purely from the trace, without reading the code.

### Exit-Criterion Test: The Competitor Analysis Agent

**Scenario:** Input: a startup's website URL. Output: a competitor analysis covering — primary competitors (top 5), competitive dimensions, positioning differences, market gaps. Roughly 1,000 words.

Process:
1. **Whiteboard first** (no code). On paper, design: how many agents, what each one does, what messages flow between them, what state is shared, what the failure modes are. Defend why this is multi-agent rather than one agent with more tools.
2. **Implement** the system.
3. **Test** on 5 startups across different verticals (SaaS B2B, consumer mobile, deep-tech, marketplace, dev tools).

**Pass criterion:** The whiteboard design holds up to interview-style probing ("why does the synthesis agent exist? could the search agent do it directly?"). Implementation produces a useful analysis for 4/5 startups. Distributed traces show clean agent transitions, not chaotic loops.

---

## Phase 7 — Document Intelligence

### Exercises

**Exercise 7.1 — PDF Parser Bake-Off**
30 invoices spanning: well-formed digital PDFs, scanned-and-OCRed, multi-page with line items spilling pages, multi-currency, handwritten signatures, two-column layouts. Compare: `pypdf`, `pdfplumber`, `PyMuPDF`, Unstructured.io, LlamaParse, Claude Sonnet 4.6 vision.
- **Success criteria:** Per-tool table: text-extraction quality (0–10), table-extraction quality (0–10), cost per page, latency per page. Resulting recommendation matrix: "for document type X, use tool Y."

**Exercise 7.2 — Schema-First Invoice Extractor**
Pydantic schema: `vendor_name, vendor_address, invoice_number, invoice_date, due_date, line_items[{description, quantity, unit_price, total}], subtotal, tax, total, currency, payment_terms`. Test set: 100 invoices, hand-labeled. Two-pass: extract + cross-field validate (line items sum to subtotal within tolerance).
- **Success criteria:** >95% field-level accuracy. Written failure-mode catalog: "model misses tax line on 8 invoices because tax appears below total in those layouts."

**Exercise 7.3 — Confidence Scoring + Human Review Queue**
Per-field confidence scoring. Two approaches: logprobs (if exposed), or ask the model to self-rate alongside the extraction. Plot calibration: predicted confidence vs. actual accuracy. Route the bottom 5% of confidence to a "needs review" queue.
- **Success criteria:** Routed items are demonstrably less accurate than non-routed items (confidence score is informative). The remaining 95% achieves higher net accuracy than no-routing baseline.

### Exit-Criterion Test: Research Paper Extractor

**Scenario:** A document type you've never built for — research papers. Extract: title, authors with affiliations, abstract, full citation list, section structure (sections with start/end pages), key findings (3–5 bullets), methodology summary. Test on 30 arXiv papers + 30 PubMed papers (different layouts).

Deliverables:
- Production-shaped extractor: schema-first, validated, confidence-scored
- Eval report: accuracy per field across both sources, cost per paper, latency per paper
- Limitations section that names specific failure modes honestly

**Pass criterion:** Documented accuracy per field exceeds 90% on at least 5 of the 7 fields, across both arXiv and PubMed. Cost per paper under $0.10. The limitations section is candid — anyone reading it knows exactly when not to trust the system.

---

## Phase 8 — MCP

### Exercises

**Exercise 8.1 — Hello-World MCP Server**
Python MCP server exposing one tool: `add_numbers(a: int, b: int) -> int`. Run via stdio. Connect from Claude Desktop or your own MCP client. Watch the tool get invoked.
- **Success criteria:** End-to-end call works. You can show the initialization handshake, the `tools/list` response, and the `tools/call` request/response in logs.

**Exercise 8.2 — Postgres-Wrapping MCP Server**
Server exposes:
- **Resources:** list of tables with column schemas
- **Tools:** `query(sql)` (read-only, write statements blocked), `describe_table(name)`, `sample_table(name, n)`
SQL injection and DDL blocked at the server level (not just by the LLM prompt).
- **Success criteria:** Connect from an LLM client. Successfully answer 5 analytical questions in natural language. Attempted destructive SQL is refused at the server, not just the LLM.

**Exercise 8.3 — Deployed Production MCP**
Streamable HTTP transport (not stdio). API-key authentication via headers. Deployed on Modal/Fly.io/Railway with TLS. Per-key rate limiting. Structured logging.
- **Success criteria:** Publicly reachable URL. A second person, given an API key, can connect from their own MCP client and exercise the tools. Rate limit triggers correctly at the configured threshold.

### Exit-Criterion Test: The GitHub MCP Server

**Scenario:** Build an MCP server that exposes the GitHub API. At minimum:
- **Tools (8+):** `search_repos`, `get_repo`, `list_issues`, `get_issue`, `list_prs`, `get_pr`, `get_file_contents`, `search_code`
- **Resources (2+):** authenticated user's starred repos as a browsable resource, authenticated user's open PRs as a browsable resource

Deploy with TLS and authentication. Connect to it from an LLM client.

Five LLM-driven tasks that must succeed end-to-end via your server:
1. "Find the most-commented open issue in `pytorch/pytorch` from the last month and summarize the discussion."
2. "What's the most recent merged PR in `microsoft/vscode` that touches the terminal subsystem? Summarize what it changed."
3. "Across my starred repos, which three have had the most release activity in the last 90 days?"
4. "Find a Python project on GitHub with >10K stars that uses both FastAPI and SQLAlchemy. Get its README."
5. "In `python/cpython`, find an open issue tagged 'easy' and 'help wanted' and propose a starting approach."

**Pass criterion:** All 5 tasks succeed end-to-end via your server. Traces show the LLM making appropriate tool calls and your server responding correctly. No GitHub API rate-limit failures (you implemented backoff).

---

## Phase 9 — Observability, Evaluation, Guardrails

### Exercises

**Exercise 9.1 — Full Observability for the Phase 6 System**
Pick LangFuse or Phoenix. Trace every LLM call, tool call, and inter-agent message. Tag every trace with: user ID, request ID, model name, total cost, success/failure flag, latency breakdown.
- **Success criteria:** Answer "what was the single most expensive request today, and why was it expensive?" in under 2 minutes from the dashboard.

**Exercise 9.2 — Golden Eval Set in CI**
For your Phase 7 extractor: curate a 100-item golden set with field-level ground truth. Implement evaluation as a pytest suite. GitHub Actions: every PR runs eval, posts a result table as a PR comment, blocks merge on any field-level regression greater than 2%.
- **Success criteria:** Create a deliberately-bad PR (e.g., swap the model to a worse one). Eval correctly catches it. Merge is blocked.

**Exercise 9.3 — Prompt Injection Defense**
Test your Phase 5 or 6 agent against 20 known prompt-injection patterns from Simon Willison's catalog plus a subset of Lakera's PINT benchmark. Build a layered defense: input filter (heuristic + classifier), tool-call constraints, output filter.
- **Success criteria:** Documented before/after defense rate. The defense layer reduces successful injections by at least 80% with under 2% false positives on legitimate inputs.

### Exit-Criterion Test: The 5-Day Production-Hardening Sprint

**Scenario:** Take your Phase 6 multi-agent system (which has none of the production infrastructure yet). In 5 working days, ship all of:

1. **Full distributed tracing** — every LLM call, tool call, agent transition logged with trace IDs (Day 1)
2. **Golden eval set wired to CI** — minimum 50 examples covering all major paths (Day 2)
3. **Input + output guardrails** — PII detection, prompt-injection defense, hallucination/refusal handling (Day 3)
4. **Cost attribution per user per day** — dashboard query that breaks down spend (Day 4)
5. **On-call runbook for top 3 expected failure modes** — what alerts trigger, who's paged, what the immediate mitigation is (Day 5)

**Pass criterion:** All five items shipped within five days. Demo'd end-to-end to a peer who plays the role of an SRE asking hard questions ("show me where the alert fires when cost spikes," "what happens if the eval CI is broken on a Friday at 5pm?"). They sign off, or you find what's missing and fix it.

---

## Phase 10 — Scale, Latency & Cost Optimization

### Exercises

**Exercise 10.1 — Latency Profile**
For your Phase 6 system, log every latency component over 1,000 requests: network time to provider, prefill time, decode time per token, tool-call wall times, total per agent step, total per turn. Plot histograms.
- **Success criteria:** You can name the p95 latency bottleneck with data. Hypothesis for fix is grounded in the breakdown, not intuition.

**Exercise 10.2 — Prompt-Cache Optimization**
Pick your most expensive prompt in any prior project. Restructure for cache friendliness: static content (instructions, tool defs, few-shot examples) at the top in stable order; dynamic content (user input, recent context) at the bottom. Measure cache hit rate before/after over 100 real-shape requests.
- **Success criteria:** Documented cost reduction of at least 50%. Cache hit rate verified from provider's response metadata.

**Exercise 10.3 — Three-Tier Model Router**
Build a query-complexity classifier (prompt-engineered small model, output 1/2/3). Route: 1→Haiku-class, 2→Sonnet-class, 3→Opus-class. Run 200 representative queries. Compare cost and quality vs. always-Opus baseline.
- **Success criteria:** 60%+ cost reduction at no worse than 5% quality regression on a human-rated sample of 50 outputs.

**Exercise 10.4 — Semantic Cache**
Implement embedding-based cache lookup with cosine-similarity threshold. Start conservative (>0.95 similarity required for a hit). Validate by manually reviewing 50 cache hits: was the cached answer actually correct for the new query?
- **Success criteria:** Documented hit rate AND documented accuracy of cache hits (≥95% — anything less means your threshold is too loose).

### Exit-Criterion Test: The Calibration Drill

**Scenario:** Pick a project — your own from earlier phases, or a popular open-source LLM app you can clone (something nontrivial, e.g., a RAG-based question-answering app or an open-source agent). Steps:

1. **Profile it** — produce a latency breakdown and cost breakdown report for 100 real-shaped requests.
2. **Identify the top 3 optimizations** by expected impact. Write them down with predictions:
   - "Optimization A: prompt caching restructure → expected 55% cost reduction"
   - "Optimization B: tool-call parallelization → expected 40% p95 latency reduction"
   - "Optimization C: small-model routing for simple queries → expected 30% cost reduction"
3. **Implement** all three.
4. **Re-measure** and compare predictions to actual results.

**Pass criterion:** Your three actual results are each within 25% of your predictions. This is the real test — not whether you can optimize (anyone can), but whether your *intuition* about where time and money go is *calibrated*. Senior engineers in this market are calibrated; juniors guess.

---

## Phase 11A — Capstone 1 (Document Intelligence + MCP)

The capstone *is* the exit test. No separate test needed.

### Day-Level Sprint Plan

**Week 1 (Days 1–5):** Schema design for 4 document types (invoice, contract, form, research paper). Ingest API with queue. Classifier agent. Specialist extractor for invoices end-to-end.

**Week 2 (Days 6–10):** Specialist extractors for the remaining three types. Validator agent with cross-field rules. Confidence scoring + calibration plot. Postgres storage layer.

**Week 3 (Days 11–15):** MCP server: tools + resources. Deployment (Modal/Fly.io). Observability (LangFuse). Eval pipeline in CI. Architecture doc. Demo video. Public README.

### Pass Criteria (Repeat from Main Curriculum)
- 100 docs/minute throughput on commodity hardware
- ≥95% field-level accuracy across types on the held-out eval set
- ≤$0.05 per document averaged across types
- p95 end-to-end latency ≤30s per document
- MCP server publicly reachable with auth
- Reproducible setup from a clean clone in ≤10 minutes

---

## Phase 11B — Capstone 2 (OTA Conversational Agent)

The capstone *is* the exit test.

### Week-Level Sprint Plan

**Week 1:** Mocked travel APIs (flights, hotels, bookings). Orchestrator state machine. Streaming frontend wired to backend SSE.

**Week 2:** Search agent + booking agent end-to-end. Memory layer (Redis short-term, Postgres long-term).

**Week 3:** Modification + support agents. RAG layer for policy / T&C support. Guardrails for PII and prompt injection.

**Week 4:** Optimization sprint — prompt caching, model routing, semantic caching, parallel tool calls, distillation of the intent classifier. Load testing. Final docs and demo.

### Pass Criteria (Repeat from Main Curriculum)
- First-token latency under 1s on ≥95% of turns
- Average cost per conversation ≤$0.05 (5–10 turn sessions)
- 500 concurrent conversations on a single application server (proven via load test)
- Task completion ≥85% on the 200-conversation golden set
- All optimizations documented with before/after metrics

---

## Phase 12 — Interview Preparation

### Exit-Criterion Test: The Mock Interview Loop

Find a peer or hire a mock interviewer. Run a full 90-minute loop:

- **30 min — System design.** Pick one from the list in the main curriculum. Whiteboard.
- **30 min — Project deep-dive.** They probe one of your capstones with hard questions: "why this architecture not that one," "show me the failure modes," "walk me through the most expensive bug."
- **15 min — Technical depth.** Random selection from the depth question bank.
- **15 min — Behavioral / debrief.** What's your strongest project, what would you do over.

**Pass criterion:** The mock interviewer would extend an offer at a senior-engineer level. If not, identify the two weakest areas and drill them for another week before re-running the loop.

---

## How to Use This Workbook

1. **Don't skip exit tests.** They're the difference between "I read about this" and "I can do this." Hiring managers can tell the difference in 5 minutes.

2. **Time-box exercises.** If an exercise is taking 3x longer than expected, stop and diagnose: are you missing a prerequisite, or is this just hard and worth the time? Both answers are fine — knowing which one matters.

3. **Document everything.** Every exit test produces an artifact: a report, a benchmark spreadsheet, a deployed URL, a video. Save them. They are your portfolio, and you will reference them in interviews.

4. **Re-take exit tests later.** Six months after you "pass" Phase 4, attempt the Phase 4 exit test again from scratch. If you can't pass it cold, the knowledge wasn't durable — and you'll see exactly which gaps to refill.

5. **Calibrate as you go.** For every prediction you make (cost, latency, accuracy), record it before measuring. Track your prediction error over time. This is the single highest-leverage habit for becoming a senior LLM engineer.

---

*End of workbook. Pair with the main curriculum document.*
