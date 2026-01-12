# TeleOps Test Plan

## Goals
- Validate core functionality across data generation, API, correlation, LLM parsing, RAG, integrations, imports, UI, evaluation, and security docs.
- Maintain >= 80% code coverage for `teleops/` and >= 90% pass rate.
- Provide deterministic, repeatable test runs.

## Scope and Coverage Targets
- Unit tests: core modules, pure functions, schema handling.
- Integration tests: FastAPI endpoints with in-memory DB, fixtures, import pipeline.
- System checks: scripts (preflight, evaluate, run_tests) and metrics outputs.
- Manual checks: Streamlit UI and RAG/LLM validation where external dependencies exist.

## Test Types and Areas
### 1) Data Plane
- Synthetic generators: alert counts, seeds, ground truth structure.
- Import pipeline: JSONL parsing, timestamp handling, database writes.

### 2) Correlation Engine
- Incident creation rules: minimum alert counts, time windows, noise filtering.
- Alert/incident relationship integrity.

### 3) API Layer
- `/generate`, `/incidents`, `/alerts`, `/rca` flows.
- Integration endpoints: fixture retrieval and webhook ingestion.
- Metrics endpoints: overview payloads and test/eval result inclusion.

### 4) LLM + RAG
- JSON parsing for LLM outputs (fenced/embedded JSON).
- RAG retrieval path: smoke-level test or local-only with skip if dependencies missing.

### 5) Evaluation
- Manual labels ingestion and scoring.
- Baseline scoring logic.

### 6) UI (Manual)
- Scenario builder creates incidents.
- Incident filters (severity/status).
- Incident context card + alert sample render.
- Observability dashboard loads metrics and test results.

### 7) Governance/Security Docs
- Presence and completeness checks (lint-like tests for required docs).

## Pass/Fail Criteria
- All automated tests pass.
- Coverage >= 80% for `teleops/`.
- Pass rate >= 90% (computed from JUnit results).

## Test Data
- `docs/data_samples/anonymized_alerts.jsonl`
- `docs/evaluation/manual_labels.jsonl`
- Integration fixtures in `docs/integrations/fixtures/`

## Execution
Recommended:
```bash
python scripts/run_tests.py
```

Manual:
```bash
pytest --cov=teleops --cov-report=term-missing
```

## Reporting
- Coverage: `storage/coverage.json` and `storage/coverage.xml`.
- Test results: `storage/junit.xml` and `storage/test_results.json`.
