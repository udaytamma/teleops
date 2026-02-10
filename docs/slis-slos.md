# TeleOps SLI/SLO Definitions

**Date:** February 2026
**Status:** Active
**Scope:** TeleOps NOC Incident RCA Platform (single-node demo deployment)

## Philosophy

TeleOps uses a two-tier RCA architecture:

- **Baseline RCA** is deterministic, rule-based, and always available. It executes in sub-millisecond time and serves as the guaranteed fallback for every incident. This is the reliability floor.
- **LLM RCA** is RAG-enhanced (Gemini + Qdrant) and provides deeper, context-aware analysis. It is inherently best-effort due to external API dependencies, variable latency, and potential for malformed output.

The SLO framework reflects this: baseline availability is the non-negotiable foundation, while LLM quality and latency targets are aspirational and designed to degrade gracefully. If the LLM path fails, operators still receive a valid RCA from the baseline path.

---

## SLI/SLO Table

| SLI | Measurement | SLO Target | Rationale |
|-----|-------------|------------|-----------|
| RCA Availability | % of incidents that receive at least one RCA (baseline always available as fallback) | 99.9% | Baseline ensures near-100% availability; only catastrophic failures (process crash, disk full) prevent RCA generation |
| Baseline Latency P99 | 99th percentile of baseline RCA generation time | &lt;50ms | Deterministic rule evaluation is millisecond-class; 50ms budget includes DB read/write overhead |
| LLM Latency P90 | 90th percentile of LLM RCA generation time | &lt;5s | Acceptable for secondary analysis that operators review asynchronously; p50 is ~3.2s |
| LLM Success Rate | % of LLM RCA attempts that return valid, parseable JSON | >90% | LLM output is best-effort; baseline is the fallback, so partial LLM failure is tolerable |
| Evaluation Accuracy | Mean semantic similarity of top hypothesis vs ground truth | >=0.75 (baseline) | Measured via cosine similarity between predicted root cause and labeled ground truth |
| Human Review SLA | % of RCA artifacts reviewed (accepted/rejected) within target time | >80% within 1 hour (demo target) | Ensures operator engagement with the review workflow; production targets would be tighter |
| API Availability | % of API requests returning non-5xx responses | 99.5% | Single-node demo deployment with no HA; accounts for restarts, resource exhaustion |

---

## Error Budget

The error budget is the tolerance for SLO violations before corrective action is required.

**Baseline RCA** is the safety net. Because it is deterministic and has no external dependencies, its error budget is extremely tight:

- **RCA Availability (99.9%):** Allows ~8.7 hours of total downtime per year. In practice, the only scenarios that breach this are process crashes or storage failures -- not logic errors.
- **Baseline Latency (&lt;50ms P99):** Violations here indicate resource contention (CPU saturation, disk I/O) rather than algorithmic issues.

**LLM RCA** has a deliberately wider error budget:

- **LLM Success Rate (>90%):** Up to 10% of LLM calls can fail (timeout, malformed JSON, API errors) without breaching the SLO. This accounts for Gemini API instability, rate limits, and edge-case prompts.
- **LLM Latency (&lt;5s P90):** The remaining 10% of requests can exceed 5s. Spikes typically correlate with Gemini API load or large RAG context windows.

**When the error budget is exhausted:**

1. Freeze non-critical changes to the LLM pipeline.
2. Investigate root cause (API degradation, prompt regression, RAG corpus issues).
3. Consider tightening retry/timeout configuration before relaxing the SLO.

The baseline path should never consume its error budget under normal operation. If it does, treat it as a P0 incident.

---

## Monitoring

### Metrics to Track

| Metric | Source | Check Frequency |
|--------|--------|-----------------|
| RCA generation count (baseline vs LLM) | Application logs, `/metrics/overview` | Continuous |
| Baseline RCA latency (p50, p90, p99) | Application logs | Per-request |
| LLM RCA latency (p50, p90, p99) | Application logs | Per-request |
| LLM RCA error rate | Application logs (failed/total) | Per-request |
| API 5xx error count | FastAPI middleware / access logs | Continuous |
| Human review pending count | SQLite query on review status | Every 15 minutes |
| Human review time-to-action | SQLite (review timestamp - creation timestamp) | Hourly |
| Evaluation accuracy scores | Evaluation pipeline output (`docs/evaluation/`) | Per evaluation run |

### Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /metrics/overview` | Dashboard-level metrics (incident counts, RCA stats) |
| `GET /incidents` | List incidents with RCA status |
| `GET /health` | API liveness check (use for uptime monitoring) |

### Alerting Thresholds (Recommended)

| Condition | Severity | Action |
|-----------|----------|--------|
| RCA Availability drops below 99.9% over 1 hour | P0 | Investigate baseline path failures immediately |
| Baseline P99 latency exceeds 50ms | P1 | Check CPU/memory/disk on host |
| LLM success rate drops below 85% over 30 minutes | P2 | Check Gemini API status, review recent prompt changes |
| LLM P90 latency exceeds 8s | P2 | Check Gemini API latency, reduce RAG context size |
| API 5xx rate exceeds 1% over 15 minutes | P1 | Check application logs, restart if necessary |
| Pending reviews older than 2 hours exceed 50% | P3 | Notify operators; may indicate disengagement |
