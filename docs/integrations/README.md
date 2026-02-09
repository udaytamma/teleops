# Mock Integrations

This folder provides recorded JSON payloads and lightweight endpoints to simulate
ServiceNow and Jira integrations.

## Fixtures
- `fixtures/servicenow_incidents.json`
- `fixtures/jira_issues.json`

## API Endpoints (FastAPI)
- `GET /integrations/servicenow/incidents`
- `GET /integrations/jira/issues`
- `POST /integrations/servicenow/webhook`
- `POST /integrations/jira/webhook`

Inbound webhook payloads are appended to `storage/integration_events.jsonl`
with a receive timestamp for audit-style review.

If `REQUIRE_TENANT_ID=true`, include `X-Tenant-Id` on these endpoints.

## Example
```bash
curl -X POST http://localhost:8000/integrations/servicenow/webhook \
  -H "Content-Type: application/json" \
  -d '{"number":"INC009999","short_description":"Synthetic webhook test"}'
```
