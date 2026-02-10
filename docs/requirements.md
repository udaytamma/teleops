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
- LLM provides complementary evidence and context not available in baseline rules (RAG-grounded hypotheses with cited runbook references).
- Time-to-first-hypothesis: LLM ~3.2s vs manual triage ~25 min (475x improvement over human operator workflow; baseline rules are sub-millisecond but lack evidence depth).

## Non-Goals
- Real operator integrations.
- HA/DR or multi-region deployment.
