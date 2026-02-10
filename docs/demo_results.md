# Demo + Results (One Page)

**Objective:** Demonstrate end-to-end incident RCA with baseline vs LLM output, supported by KPIs and evaluation evidence.

## Story (60-90 seconds)
1) Generate a scenario from the Scenario Builder (e.g., DNS outage).
2) Show correlated incidents and alert samples.
3) Run baseline RCA vs LLM RCA side-by-side.
4) Open Observability dashboard to show KPIs, coverage, and evaluation scores.

## KPIs Snapshot (Latest Run)
| Metric | Value |
| --- | --- |
| Test pass rate | 100% |
| Coverage | 79.25% |
| Baseline RCA avg (synthetic) | 0.894 |
| LLM RCA avg (synthetic) | 0.658 |
| Manual label avg | 0.451 |

## Baseline vs LLM: Complementary Strengths

The baseline and LLM serve different purposes in the RCA workflow. They are complementary, not competing.

| Dimension | Baseline | LLM | Operator Benefit |
| --- | --- | --- | --- |
| Speed | Sub-millisecond | ~3.2s (p50) | Baseline provides instant triage; LLM adds depth |
| Consistency | Deterministic | Variable | Baseline is reproducible for audit; LLM handles novel patterns |
| Specificity | High (pattern-matched) | Medium (improves with prompt tuning) | Baseline catches known patterns; LLM reasons about unknown ones |
| RAG Evidence | None | Provided in output | LLM cites runbook context that baseline cannot |
| Confidence | Fixed (0.52-0.70) | Adaptive | LLM calibrates uncertainty; baseline is honest about limits |
| vs Manual Triage | N/A | 475x faster than ~25 min manual | Both vastly outperform human-only RCA |

## Why LLM Semantic Scores Are Lower (Short Analysis)
- LLM scores trail the baseline in the latest 50-run evaluation (see `storage/evaluation_results.json`).
- **Prompt generality**: LLM returns paraphrased hypotheses rather than matching exact ground-truth strings. This penalizes the LLM under cosine similarity but does not mean the hypotheses are wrong.
- **RAG depth**: The RAG corpus is intentionally minimal; evidence is present but not highly specific.
- **Semantic scoring**: Evaluation uses cosine similarity via `sentence-transformers/all-MiniLM-L6-v2`. Exact string matches (baseline) naturally score higher than paraphrases (LLM).
- **Run count**: Limited runs (50) reduce statistical stability.

## Improvements Planned
- Expand RAG corpus with scenario-specific runbooks.
- Add structured slots in the prompt (device, interface, symptom).
- Increase evaluation runs beyond 50 for better confidence.

## Screenshots (Optional)
Screenshots are not committed in this repo; add them to `docs/assets/` before a hiring demo.
Expected filenames:
- `teleops-console.png`
- `teleops-rca-comparison.png`
- `teleops-observability.png`
