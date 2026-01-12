# Access Control (Minimal)

## Roles
- Ops Engineer: read incidents, run RCA, view evidence.
- SRE Manager: read + metrics dashboard.
- Platform Owner: configuration and audit review.

## Controls
- API gateway enforces role-based access in production deployments.
- Optional API token gate protects write + metrics endpoints in the demo.
- Sensitive endpoints (LLM output, audit logs) require elevated role.
- Logs are stored append-only and rotated regularly.

## Auditability
- Integration webhooks are recorded in `storage/integration_events.jsonl`.
- RCA artifacts store request/response payloads for traceability.
