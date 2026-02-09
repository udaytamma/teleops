# Access Control (Minimal)

## Roles
- Ops Engineer: read incidents, run RCA, review hypotheses, view evidence.
- SRE Manager: read + metrics dashboard + audit trail.
- Platform Owner: configuration, reset, and audit review.

## Controls
- Optional API token gate protects read + write endpoints in the demo.
- Admin token is required for destructive actions (reset) and webhook writes.
- Metrics endpoints can be protected with a dedicated metrics token.
- Tenant isolation enforced when `REQUIRE_TENANT_ID=true` (via `X-Tenant-Id` header) on all data endpoints including review and audit.
- RCA artifacts carry a `status` field (`pending_review`, `accepted`, `rejected`); retrieval can be filtered by status.

## Log Rotation
- Integration events (`storage/integration_events.jsonl`): size-based rotation at 5 MB with 3 backups.
- Audit log (`storage/audit_log.jsonl`): size-based rotation at 5 MB with 3 backups.
- Rotation thresholds are configurable via `INTEGRATION_LOG_MAX_BYTES`, `AUDIT_LOG_MAX_BYTES`, and corresponding `*_BACKUP_COUNT` env vars.

## Auditability
- Integration webhooks are recorded in `storage/integration_events.jsonl`.
- RCA review decisions are logged to `storage/audit_log.jsonl` with reviewer identity, decision, timestamp, and notes.
- RCA artifacts store minimal evaluation metadata (RAG query, alert count, chunk count) rather than full request/response payloads.
