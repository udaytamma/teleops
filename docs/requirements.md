# Requirements (MVP)

## Problem
Operators face alert floods with limited context, delaying RCA and increasing MTTR.

## Users
- Ops Engineer (primary)
- SRE Manager (secondary)

## Goals
- Produce incidents from synthetic alerts.
- Generate RCA hypotheses with evidence.
- Compare baseline vs LLM RCA.

## Success Metrics
- RCA accuracy >= 0.75 on 50 seeded scenarios (baseline achieved 0.894 as of 2026-02-09).
- LLM improvement >= 0.10 vs baseline (target; latest run 0.658 vs baseline 0.894 on 2026-02-09).
- Median time-to-first-hypothesis reduced by >= 30% vs baseline (target; latest benchmark shows LLM p50 3150ms vs baseline 0.107ms; see `storage/benchmarks/rca_latency.json`).

## Non-Goals
- Real operator integrations.
- HA/DR or multi-region deployment.
