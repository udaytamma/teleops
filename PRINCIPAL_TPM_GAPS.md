# TeleOps — Principal TPM Gaps (Mag7 Independent Capstone)

Scope: Line‑by‑line review of TeleOps source + documentation (top‑level config, `.github/`, `teleops/`, `ui/`, `scripts/`, `docs/`, `tests/`). Generated artifacts (logs, coverage outputs, DB files, pyc) are treated as hygiene findings rather than source.

## Critical gaps
- Secrets committed to repo: `.env` contains a live Gemini API key and should be removed and rotated. (`teleops/.env:4`)
- Dockerized UI cannot start: Docker image never copies `ui/`, but docker‑compose launches Streamlit from `ui/streamlit_app/app.py`, so the file is missing in the container. (`teleops/Dockerfile:15-17`, `teleops/docker-compose.yml:28`)
- Dockerized UI cannot reach API: UI reads `TELEOPS_API_URL`, but docker‑compose provides `API_BASE_URL`, so UI defaults to localhost inside the container. (`teleops/docker-compose.yml:27`, `teleops/ui/streamlit_app/pages/1_Incident_Generator.py:23`, `teleops/ui/streamlit_app/pages/2_Observability.py:11`, `teleops/ui/streamlit_app/pages/3_LLM_Trace.py:11`)
- Access control/RBAC not implemented: only optional token gate on some write/metrics endpoints; read endpoints and RCA fetch are open despite role‑based access claims. (`teleops/teleops/api/app.py:145-153`, `teleops/teleops/api/app.py:156-158`, `teleops/teleops/api/app.py:199-208`, `teleops/teleops/api/app.py:302-307`, `teleops/docs/security_controls.md:9-11`)
- Redaction policy violated and sensitive data exposure: prompts include incident + alert samples; RCA artifacts persist full LLM request/response; UI renders raw alerts/RAG context; API returns raw_payload. Policy says strip IPs/emails and avoid raw payloads in UI. (`teleops/docs/redaction_policy.md:4-6`, `teleops/teleops/llm/rca.py:148-150`, `teleops/teleops/api/app.py:93`, `teleops/teleops/api/app.py:284-291`, `teleops/ui/streamlit_app/pages/3_LLM_Trace.py:69-106`)

## High gaps
- RAG query hard‑coded to “network degradation” for all incidents; ignores incident summary and alert content. (`teleops/teleops/api/app.py:271`)
- Evaluation methodology misaligned with success metrics: fixed incident summary + constant RAG query + string similarity scoring; doesn’t measure the defined accuracy/time‑to‑hypothesis targets. (`teleops/scripts/evaluate.py:17-44`, `teleops/docs/requirements.md:15-17`)
- Tenant isolation not enforced: tenant_id fields exist but list endpoints return all alerts/incidents without tenant scoping. (`teleops/teleops/models.py:28`, `teleops/teleops/models.py:45`, `teleops/teleops/api/app.py:199-208`)
- Audit log rotation claim not implemented: integration events appended to JSONL with no rotation/retention controls. (`teleops/docs/security_controls.md:12`, `teleops/teleops/api/app.py:123-132`)

## Medium gaps
- Gemini timeout setting defined but not applied to SDK call; risk of long/hanging requests and config drift. (`teleops/teleops/config.py:31`, `teleops/teleops/llm/client.py:88-96`)
- RAG index built/loaded per request without caching; adds latency and cost on RCA calls. (`teleops/teleops/rag/index.py:60-62`, `teleops/teleops/api/app.py:273`)
- Docker compose uses a local SQLite file without a DB volume; data is lost on container rebuilds. (`teleops/docker-compose.yml:12-15`)
- Generated artifacts committed (DB/logs/coverage/pyc) indicate hygiene gaps and potential data leakage: `teleops/teleops.db`, `teleops/storage/*`, `teleops/**/__pycache__/*`.
- Default LLM provider mismatch between docs and config (README says `gemini`, config defaults to `local_telellm`). (`teleops/README.md:147`, `teleops/teleops/config.py:21`)

## Missing Principal TPM artifacts / program‑level depth
- PRD / product strategy: `requirements.md` is MVP‑level and lacks user research, competitive analysis, and acceptance criteria traceability to tests/metrics. (`teleops/docs/requirements.md:1-21`)
- KPI/OKR instrumentation and SLOs: metrics endpoint only exposes counts and averages; no SLIs/SLOs, error budgets, or alerting strategy. (`teleops/teleops/api/app.py:352-376`)
- Reliability + scale plan: no load/perf test plan, capacity model, or latency/throughput targets for RAG/LLM paths.
- Data governance beyond redaction: no retention/deletion policy, data classification, or vendor risk review for external LLMs. (`teleops/docs/redaction_policy.md:1-11`)
- Security posture depth: threat model + controls are high‑level; no mapped controls‑to‑implementation evidence, pen‑test plan, or audit‑trail integrity design. (`teleops/docs/threat_model.md:1-17`, `teleops/docs/security_controls.md:1-16`)
- Release/rollout readiness: no staged rollout, canary strategy, or operational readiness checklist beyond a demo runbook. (`teleops/docs/deployment_runbook.md:1-26`)
- Risk register + dependency SLAs: no formal risk log, mitigations, or external dependency SLAs (Gemini/embeddings).
