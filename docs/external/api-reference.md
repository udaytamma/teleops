# API Reference

> Static copy of the public TelcoOps API reference (zeroleaf.dev/docs/telcoops/api-reference), imported on 2026-02-09 and adjusted to match the current implementation.

TelcoOps exposes 16 REST endpoints for scenario generation, incident correlation, RCA generation, human review, and observability. The API is designed to be simple enough for a demo UI but structured for future automation.

## Base URL
```
http://127.0.0.1:8000
```

Interactive API documentation is available at `/docs` (Swagger) and `/redoc` (ReDoc).

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/generate` | Generate synthetic alerts and correlate incidents. |
| GET | `/alerts` | List all alerts. |
| GET | `/incidents` | List all incidents. |
| GET | `/incidents/{incident_id}/alerts` | List alerts for a specific incident. |
| POST | `/reset` | Clear alerts, incidents, and RCA artifacts. |
| POST | `/rca/{incident_id}/baseline` | Generate baseline RCA using pattern-matching rules. |
| POST | `/rca/{incident_id}/llm` | Generate LLM RCA using RAG context. |
| GET | `/rca/{incident_id}/latest` | Fetch latest RCA artifact. |
| GET | `/metrics/overview` | Counts, KPIs, test results, and evaluation summary. |
| GET | `/health` | Health check endpoint for monitoring. |
| GET | `/integrations/servicenow/incidents` | Mock ServiceNow incident payloads. |
| GET | `/integrations/jira/issues` | Mock Jira issue payloads. |
| POST | `/integrations/servicenow/webhook` | Accept ServiceNow webhook payloads. |
| POST | `/integrations/jira/webhook` | Accept Jira webhook payloads. |
| POST | `/rca/{artifact_id}/review` | Accept or reject an RCA hypothesis (human review). |
| GET | `/audit/rca` | RCA review audit log (filterable by incident, decision, reviewer). |

## Generate Scenario
Generates synthetic alerts and correlates them into incidents. All parameters are validated with Pydantic.

```json
POST /generate
Content-Type: application/json

{
  "incident_type": "dns_outage",    // Required: one of 11 scenario types
  "alert_rate_per_min": 20,         // 1-100, default: 20
  "duration_min": 10,               // 1-60, default: 10
  "noise_rate_per_min": 5,          // 0-50, default: 5
  "seed": 42                        // Optional: for reproducibility
}
```

### Supported Incident Types
`network_degradation`, `dns_outage`, `bgp_flap`, `fiber_cut`, `router_freeze`, `isp_peering_congestion`, `ddos_edge`, `mpls_vpn_leak`, `cdn_cache_stampede`, `firewall_rule_misconfig`, `database_latency_spike`

Response includes alert count, incident summary, and ground truth metadata.

## Generate Baseline RCA

```
POST /rca/{incident_id}/baseline
```

Returns hypothesis and confidence score based on pattern-matching rules. The baseline analyzes incident summary and alert types to select the most appropriate hypothesis from 11 predefined patterns.

### Example Response
```json
{
  "incident_summary": "DNS servers are reporting failures",
  "hypotheses": ["authoritative DNS cluster outage in region-east"],
  "confidence_scores": {
    "authoritative DNS cluster outage in region-east": 0.60
  },
  "evidence": {
    "alerts": "DNS-related alerts: servfail spikes, NXDOMAIN increases",
    "match_count": 3
  },
  "generated_at": "2026-01-11T10:15:32Z",
  "model": "baseline-rules",
  "artifact_id": "a1b2c3d4-...",
  "duration_ms": 12.4,
  "status": "pending_review"
}
```

## Generate LLM RCA

```
POST /rca/{incident_id}/llm
```

LLM RCA uses the incident payload, a sample of alerts (up to 20), and RAG context from the runbook corpus. If the LLM fails, the API returns a 502 with the underlying error.

## Fetch Latest RCA

```
GET /rca/{incident_id}/latest?source=llm|baseline|any
```

## Review RCA Hypothesis

```json
POST /rca/{artifact_id}/review
Content-Type: application/json

{
  "decision": "accepted",          // Required: "accepted" or "rejected"
  "reviewed_by": "noc-lead-01",    // Required: reviewer identifier (1-128 chars)
  "notes": "Confirmed via logs"    // Optional: review notes
}
```

Updates the RCA artifact status and logs the review decision to an append-only audit trail at `storage/audit_log.jsonl`. Each artifact can only be reviewed once.

## Audit Log

```
GET /audit/rca?incident_id=...&decision=accepted&reviewer=noc-lead-01
```

Returns review events from the audit log. All query parameters are optional filters.

## Integration Webhooks

### ServiceNow Webhook
```json
POST /integrations/servicenow/webhook
Content-Type: application/json

{
  "sys_id": "abc123def456",                    // Required: ServiceNow record ID
  "number": "INC0012345",                      // Required: Incident number
  "short_description": "Network outage",       // Required: Brief description
  "priority": 2,                               // Optional: 1-5 (1=Critical), default: 3
  "state": "In Progress"                       // Optional: Incident state, default: "New"
}
```

### Jira Webhook
```json
POST /integrations/jira/webhook
Content-Type: application/json

{
  "issue_key": "OPS-123",                      // Required: Jira issue key
  "summary": "DNS resolution failures",        // Required: Issue summary
  "priority": "High",                          // Optional: Priority name, default: "Medium"
  "status": "In Progress"                      // Optional: Issue status, default: "Open"
}
```

Webhook events are appended to `storage/integration_events.jsonl` for audit logging.

## Error Codes

| Code | Meaning | Common Causes |
| --- | --- | --- |
| 401 | Unauthorized | Missing or invalid API token (if configured) |
| 404 | Not Found | Incident or RCA artifact not found |
| 422 | Validation Error | Invalid request payload (missing required fields, out of range) |
| 502 | Bad Gateway | LLM or RAG failure during RCA generation |

## Authentication (Optional)
TelcoOps supports a three-tier token system. When tokens are configured via environment variables, the corresponding endpoints require an `X-API-Key` or `Authorization: Bearer` header.

| Token | Env Variable | Protects |
| --- | --- | --- |
| API Token | `API_TOKEN` | Write endpoints: `/generate`, `/rca/*`, `/review`, integration reads |
| Admin Token | `ADMIN_TOKEN` | Destructive endpoints: `/reset`, webhook ingestion |
| Metrics Token | `METRICS_TOKEN` | Observability endpoints: `/metrics/overview`, `/audit/rca` |

```
X-API-Key: your_token_here
Authorization: Bearer your_token_here
```
