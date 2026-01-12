# Demo + Results (One Page)

**Objective:** Demonstrate end-to-end incident RCA with baseline vs LLM output, supported by KPIs and evaluation evidence.

## Story (60–90 seconds)
1) Generate a scenario from the Scenario Builder (e.g., DNS outage).
2) Show correlated incidents and alert samples.
3) Run baseline RCA vs LLM RCA side-by-side.
4) Open Observability dashboard to show KPIs, coverage, and evaluation scores.

## KPIs Snapshot (Latest Run)
| Metric | Value |
| --- | --- |
| Test pass rate | 100% |
| Coverage | 87% |
| Baseline RCA avg (synthetic) | 1.00 |
| LLM RCA avg (synthetic) | 0.44 |
| Manual label avg | 0.44 |

## Before/After (Baseline vs LLM)
| Dimension | Baseline | LLM |
| --- | --- | --- |
| Consistency | Deterministic | Variable |
| Specificity | High (pattern-matched) | Medium (needs more domain grounding) |
| RAG Evidence | None | Provided in output |
| Confidence | Fixed | Adaptive |

## Why LLM Scores Lag (Short Analysis)
- **Prompt generality**: LLM returns generic hypotheses rather than matching specific ground-truth strings.
- **RAG depth**: The RAG corpus is intentionally minimal; evidence is present but not highly specific.
- **Similarity scoring**: The evaluation rubric rewards exact or near-exact matches; LLM paraphrases are penalized.
- **Run count**: Limited runs reduce statistical stability.

## Improvements Planned
- Expand RAG corpus with scenario-specific runbooks.
- Add structured slots in the prompt (device, interface, symptom).
- Use semantic similarity or rubric-based scoring (not exact matching only).
- Increase evaluation runs to 20–50 for better confidence.

## Screenshots (Drop-in)
![TeleOps Console](docs/assets/teleops-console.png)
![RCA Comparison](docs/assets/teleops-rca-comparison.png)
![Observability Dashboard](docs/assets/teleops-observability.png)

## Demo Video/GIF
Add the walkthrough here: `[Demo video link](TBD)`
