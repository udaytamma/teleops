# Architecture

## Components
- **Data plane:** Synthetic alert generator + SQLite alert store.
- **Control plane:** FastAPI endpoints with token-based auth.
- **AI plane:** RAG pipeline (LlamaIndex + HuggingFace embeddings) + LLM RCA (Gemini / local).
- **Evaluation plane:** Semantic similarity scoring, quality metrics, confidence calibration.
- **Presentation:** Streamlit UI with NOC-style dashboard.

## Data Flow
1) Generate synthetic alerts via configurable scenario builder.
2) Correlate alerts into incidents using tag-based grouping.
3) Run baseline RCA (pattern matching, &lt;10ms).
4) Run LLM RCA with RAG context (Gemini 2.0 Flash, ~2s).
5) **Human reviews and accepts/rejects hypothesis** (process gate; API supports status filtering but does not enforce acceptance by default).
6) Display comparison results with timing and confidence metrics.
7) Audit trail captures all review decisions.

## Evaluation Pipeline
1) Run count is configurable; the latest stored results use 11 seeded scenarios across 11 incident types.
2) Score RCA hypotheses against ground truth using **semantic cosine similarity** (sentence-transformers/all-MiniLM-L6-v2).
3) Compute decision quality metrics: precision, recall, wrong-but-confident rate, confidence calibration.
4) Results persisted to `storage/evaluation_results.json` and displayed on Observability dashboard.

---

## Where Automation Stops

**Design principle: "AI suggests, human decides, system audits."**

Fully autonomous RCA is dangerous in telecom operations. A wrong hypothesis acted upon without human validation can trigger incorrect remediation (e.g., rerouting traffic based on a hallucinated fiber cut), escalating a P2 into a P1. This section explicitly defines the automation boundary.

### Automation Boundary Table

| Step | Automated | Human Required | Rationale |
|------|-----------|----------------|-----------|
| Alert ingestion | Yes | No | Standard data pipeline, deterministic |
| Alert correlation | Yes | No | Tag-based grouping, no judgment needed |
| Noise filtering | Yes | No | Statistical threshold, reversible |
| Baseline RCA generation | Yes | No | Pattern matching against known rules |
| LLM RCA generation | Yes | No | AI hypothesis generation |
| **RCA hypothesis acceptance** | **No** | **Yes** | Human validates AI output before action |
| **Remediation planning** | **No** | **Yes** | Operator designs corrective actions |
| **Remediation execution** | **No** | **Yes** | Operator confirms and executes changes |
| Post-incident review | Assisted | Yes | AI summarizes, human validates lessons |

MVP note: The API does not enforce acceptance by default; consumers should query `/rca/{id}/latest?status=accepted` to enforce this gate.

### Why Fully Autonomous RCA Is Dangerous

1. **Hallucination risk:** LLMs can generate plausible but incorrect hypotheses. A "BGP flap" diagnosis when the actual root cause is a fiber cut leads to wrong remediation steps.
2. **Blast radius:** Telecom network changes affect thousands of subscribers. Acting on a wrong hypothesis without human review can cascade failures.
3. **Confidence is not correctness:** High confidence scores (0.8+) do not guarantee accuracy. Our evaluation shows a measurable "wrong-but-confident" rate that must be monitored.
4. **Novel incidents:** Scenarios outside training data produce unreliable outputs. The system has no way to distinguish "novel" from "familiar" without human judgment.

### Escalation Triggers

The following signals should trigger escalation to a senior operator rather than automated action:

- **Low confidence:** Any hypothesis with confidence &lt;0.5 requires senior review before proceeding.
- **Competing hypotheses:** When multiple hypotheses have similar confidence scores (gap &lt;0.1), the system cannot distinguish root cause and needs human triage.
- **Novel incident type:** Scenarios with no pattern match in baseline rules AND low RAG retrieval similarity indicate an incident type not represented in training data.
- **High-severity incidents:** P1/Critical incidents always require human confirmation regardless of confidence level.
- **Conflicting evidence:** When alert patterns match multiple rules with contradictory remediation steps.

### Audit Trail

Every RCA review decision is logged to `storage/audit_log.jsonl` with:
- Artifact ID, incident ID, timestamp
- Decision (accepted/rejected)
- Reviewer identity
- Optional notes
- Original hypothesis and model used

This audit trail enables:
- **Accountability:** Who approved what, when.
- **Feedback loop:** Rejected hypotheses identify model weaknesses.
- **Compliance:** Auditable decision history for incident post-mortems.
- **Quality tracking:** Acceptance rate trends signal model drift or improvement.

### Monitoring the Human-AI Boundary

In production, the following metrics would be tracked to ensure the boundary remains effective:

| Metric | Target | Signal |
|--------|--------|--------|
| Acceptance rate | 70-90% | Below 70% = model quality issue; above 90% = rubber-stamping risk |
| Wrong-but-confident rate | &lt;5% | Rising rate = model drift, retrain or adjust thresholds |
| Time to review | &lt;5 min | Increasing = operator fatigue or alert volume issue |
| Override rate | &lt;10% | Operators changing hypothesis before accepting |
| Escalation rate | 5-15% | Too low = operators not escalating novel cases |
