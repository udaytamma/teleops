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
- RCA accuracy >= 0.75 on 50 seeded scenarios and >= 0.10 improvement vs baseline.
- Median time-to-first-hypothesis reduced by >= 30% vs baseline.

## Non-Goals
- Real operator integrations.
- HA/DR or multi-region deployment.
