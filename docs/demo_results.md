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
| Coverage | 79.57% |
| Baseline RCA avg (synthetic) | 0.894 |
| LLM RCA avg (synthetic) | Not run in latest results |
| Manual label avg | 0.451 |

## Before/After (Baseline vs LLM)
| Dimension | Baseline | LLM |
| --- | --- | --- |
| Consistency | Deterministic | Variable |
| Specificity | High (pattern-matched) | Medium (needs more domain grounding) |
| RAG Evidence | None | Provided in output |
| Confidence | Fixed | Adaptive |

## Why LLM Scores Lag (Short Analysis)
- LLM results are not captured in the latest stored evaluation run; when LLM is enabled, scores can lag for the following reasons.
- **Prompt generality**: LLM returns generic hypotheses rather than matching specific ground-truth strings.
- **RAG depth**: The RAG corpus is intentionally minimal; evidence is present but not highly specific.
- **Semantic scoring**: Evaluation uses cosine similarity via `sentence-transformers/all-MiniLM-L6-v2`. LLM paraphrases score lower than exact baseline matches but are no longer penalized as harshly as with string matching.
- **Run count**: Limited runs reduce statistical stability.

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

## Demo Video/GIF
Use the assets here until a video link is available:
`docs/demo_video_assets.md`
