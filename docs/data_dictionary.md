# Data Dictionary (Alerts)

This dictionary describes the alert fields used across synthetic generation and anonymized log imports.

| Field | Type | Description |
| --- | --- | --- |
| `timestamp` | ISO-8601 string | Event time in UTC. |
| `source_system` | string | Source emitter (e.g., `net-snmp`, `k8s-node`). |
| `host` | string | Anonymized host or device identifier. |
| `service` | string | Service or subsystem name. |
| `severity` | string | Severity label (`critical`, `warning`, `info`). |
| `alert_type` | string | Alert category (`packet_loss`, `high_latency`, etc.). |
| `message` | string | Human-readable description. |
| `tags` | object | Key-value tags for grouping (e.g., `incident`). |
| `raw_payload` | object | Raw metrics or structured fields. |
| `tenant_id` | string | Anonymized tenant identifier. |

## Notes
- All examples are synthetic or anonymized for demo use.
- PII is excluded by design; host and tenant identifiers are non-real.
