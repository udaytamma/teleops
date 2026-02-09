# Access Control (Minimal)

## Roles
- Ops Engineer: read incidents, run RCA, view evidence.
- SRE Manager: read + metrics dashboard.
- Platform Owner: configuration and audit review.

## Controls
- Optional API token gate protects read + write endpoints in the demo.
- Admin token is required for destructive actions (reset) and webhook writes.
- Metrics endpoints can be protected with a dedicated metrics token.
- Tenant isolation enforced when `REQUIRE_TENANT_ID=true` (via `X-Tenant-Id` header).
- Logs are stored append-only with size-based rotation in the demo.

## Auditability
- Integration webhooks are recorded in `storage/integration_events.jsonl`.
- RCA artifacts store request/response payloads for traceability.
