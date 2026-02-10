# Threat Model -- STRIDE Analysis

**Scope:** TeleOps Telecom NOC Incident RCA Platform
**Last Updated:** February 09, 2026

## Assets

| Asset | Storage | Sensitivity |
|-------|---------|-------------|
| Incident data (alerts, metrics, topology) | SQLite | Internal -- may contain network infrastructure details |
| RCA artifacts (hypotheses, evidence, confidence) | SQLite | Internal -- derived from incident data |
| LLM prompts and responses | Transient (not persisted) | High -- contain redacted incident context sent to Gemini API |
| RAG corpus (runbooks, knowledge base) | Local filesystem (HuggingFace index) | Internal -- operational procedures |
| Audit trail | JSONL files (`storage/audit_log.jsonl`) | Compliance -- review decisions, reviewer identity |
| Integration events | JSONL files (`storage/integration_events.jsonl`) | Internal -- webhook payloads |
| API tokens (api_token, admin_token, metrics_token) | Environment variables | Secret |
| Tenant identifiers | Request headers | Internal -- hashed in LLM-bound content via redaction; stored plaintext in DB for query performance |

---

## STRIDE Threat Analysis

### S -- Spoofing

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| Unauthenticated API access | **High** | Token auth via `X-API-Key` or `Bearer` header, but tokens are optional -- when `API_TOKEN` env var is unset, all endpoints are open | In demo mode, any network-reachable client can read/write all data | Enforce token auth in production (`API_TOKEN` and `ADMIN_TOKEN` must be set). Fail closed: reject requests when tokens are not configured. |
| No per-user identity | **Medium** | Single shared `api_token` for all read/write users; single shared `admin_token` for destructive operations. No user-level authentication. | Cannot attribute actions to individual operators. Shared token compromise affects all users. | Integrate with an identity provider (OAuth2/OIDC). Issue per-user tokens with claims. |
| Tenant spoofing via header | **Medium** | `X-Tenant-Id` header is required when `REQUIRE_TENANT_ID=true`. Tenant IDs are hashed to aliases in redacted content sent to the LLM, but stored in plaintext in the database for query filtering. | Callers can supply arbitrary tenant IDs -- no validation that the caller belongs to the claimed tenant. | Bind tenant identity to authenticated user tokens. Validate tenant membership server-side. |
| Streamlit dashboard has no auth | **Low** | Dashboard is read-only in demo mode. No login required. | Anyone with network access can view incident data and RCA results. | Add authentication to the dashboard (Streamlit auth, reverse proxy, or SSO) for non-demo deployments. |

### T -- Tampering

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| SQLite data modification | **High** | No integrity protection on the database file. Any process with filesystem access can modify incident and RCA records. | Incident data, RCA hypotheses, confidence scores, and review decisions can be silently altered. | Use a managed database (PostgreSQL) with access controls. Enable WAL checksums. Restrict filesystem permissions. |
| RCA review decision manipulation | **Medium** | Review endpoint requires `api_token`. Decisions are logged to the audit trail. | An attacker with the shared API token can accept or reject any RCA, altering the human review workflow. | Require per-user auth for review actions. Record reviewer identity from authenticated claims, not client-supplied fields. |
| JSONL audit log tampering | **Medium** | Append-only write pattern in application code. Log rotation with backups. | Logs are plain text files with no cryptographic integrity. An attacker with filesystem access can modify or delete entries. | Write audit logs to a tamper-evident store (append-only cloud storage, write-once media, or a log aggregation service with integrity verification). |
| Prompt injection via alert data | **Medium** | Input validation and JSON schema checks on LLM outputs. PII redaction applied before LLM calls. | Malicious alert payloads or RAG corpus content could inject instructions into LLM prompts, causing unexpected RCA outputs. | Add prompt injection detection heuristics. Validate LLM outputs against expected schema and domain constraints. Sandbox LLM responses before presenting to users. |
| RAG corpus poisoning | **Low** | RAG corpus is loaded from local filesystem. No write API exposed. | An attacker with filesystem access could modify runbook documents to influence RCA quality. | Checksum or sign RAG corpus files. Restrict write access to the `rag_corpus/` directory. Monitor for unexpected changes. |

### R -- Repudiation

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| Unattributable actions | **High** | Audit log records reviewer identity, decision, timestamp, and notes. Integration events are logged. | Reviewer identity is client-supplied (not derived from authenticated credentials). No per-user auth means actions cannot be reliably attributed. | Derive actor identity from authenticated tokens. Make identity a non-editable server-side field. |
| Audit log integrity | **Medium** | JSONL append-only pattern with size-based rotation (5 MB, 3 backups). | Logs are unsigned plain text. A malicious actor could alter log entries to deny actions. Rotated logs could be deleted. | Sign log entries with HMAC or ship to a centralized, tamper-proof log aggregator (e.g., SIEM). Protect rotated backup files with restricted permissions. |
| No timestamp attestation | **Low** | Timestamps are generated server-side using system clock. | Clock manipulation on the host could falsify event ordering. | Use NTP-synchronized clocks. Include monotonic sequence numbers in audit entries. |

### I -- Information Disclosure

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| Incident data sent to external LLM | **High** | PII redaction (regex-based) strips IP addresses and email-like tokens before LLM calls. Raw prompt/response text is not persisted. | Regex-based redaction may miss non-standard PII patterns (hostnames, IMSI/IMEI, internal URLs, custom identifiers). Redacted data is still sent to Google Gemini API externally. | Evaluate self-hosted LLM for sensitive environments. Expand redaction patterns to cover telecom-specific identifiers. Audit redaction effectiveness periodically. |
| SQLite database is unencrypted | **Medium** | Database file is on local filesystem with OS-level permissions. | If the host is compromised or the file is exfiltrated, all incident and RCA data is readable in plaintext. | Use SQLite encryption extensions (SQLCipher) or migrate to a managed database with encryption at rest. |
| Tenant data cross-contamination | **Medium** | Tenant isolation via `tenant_id` field filtering. Tenant IDs are hashed to aliases in storage. | Tenant filtering is application-level only -- no database-level row security. A bug in query logic could leak cross-tenant data. | Implement row-level security in a production database. Add integration tests that verify tenant isolation across all query paths. |
| Error messages expose internals | **Low** | FastAPI default error handling. No custom exception sanitization documented. | Stack traces or database error messages could leak schema details, file paths, or configuration values. | Configure production error handling to return generic messages. Log detailed errors server-side only. |
| RAG context leakage | **Low** | RAG chunks are included in LLM prompts. Redaction is applied to RAG context before transmission. | Operational runbooks may contain sensitive procedures or credentials embedded in documentation. | Audit RAG corpus for embedded secrets. Apply redaction to RAG content independently. |

### D -- Denial of Service

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| No API rate limiting | **High** | None. All endpoints accept unlimited requests. | An attacker can flood the API with requests, exhausting CPU, memory, or LLM API quota. | Add rate limiting middleware (e.g., `slowapi` or reverse proxy rate limits). Set per-IP and per-token request quotas. |
| LLM API timeout cascading | **Medium** | LLM calls have configurable timeouts. | Slow or unresponsive Gemini API calls can block request threads, degrading overall API responsiveness for all users. | Use async LLM calls with circuit breaker patterns. Set aggressive timeouts. Implement request queuing with backpressure. |
| SQLite single-writer bottleneck | **Medium** | SQLite with default configuration. | Concurrent write requests are serialized by SQLite's single-writer lock, causing latency spikes under load. | Migrate to PostgreSQL for production workloads. Use connection pooling. Enable WAL mode for SQLite in demo. |
| Unbounded incident generation | **Low** | Scenario generator creates synthetic incidents on demand. | Repeated calls to `/generate` can fill the database and consume disk space. | Add configurable limits on stored incidents. Implement automatic cleanup of old synthetic data. |
| Large payload attacks | **Low** | Pydantic model validation on request bodies. | No explicit payload size limits documented. Oversized alert payloads could consume memory. | Configure max request body size at the reverse proxy or ASGI server level. |

### E -- Elevation of Privilege

| Threat | Risk | Current Mitigation | Residual Risk | Production Recommendation |
|--------|------|-------------------|---------------|--------------------------|
| Admin token grants full mutation access | **High** | Separate `admin_token` for destructive operations (`/reset`, webhook ingestion). | Admin token is a single static secret with no expiration, rotation, or scope limitation. Compromise grants unrestricted destructive access. | Implement token rotation and expiration. Use scoped permissions (RBAC) rather than a single admin token. |
| No role-based access control | **Medium** | Two-tier token model: `api_token` (read/write) and `admin_token` (destructive). Roles documented but not enforced per-user. | Any holder of `api_token` can perform all non-destructive operations including RCA generation, review decisions, and data reads. No distinction between Ops Engineer, SRE Manager, and Platform Owner roles. | Implement RBAC with role assignments per user. Map documented roles (Ops Engineer, SRE Manager, Platform Owner) to permission sets. |
| Streamlit to API privilege boundary | **Low** | Streamlit reads `TELEOPS_API_TOKEN` from environment and passes it in request headers. | Streamlit runs with the same token for all dashboard users. No per-session authorization. | Run Streamlit behind an auth proxy. Pass per-user credentials to the API. |

---

## Risk Summary

| Category | High | Medium | Low |
|----------|------|--------|-----|
| Spoofing | 1 | 2 | 1 |
| Tampering | 1 | 3 | 1 |
| Repudiation | 1 | 1 | 1 |
| Information Disclosure | 1 | 2 | 2 |
| Denial of Service | 1 | 2 | 2 |
| Elevation of Privilege | 1 | 1 | 1 |
| **Total** | **6** | **11** | **8** |

## Key Findings

1. **Optional authentication is the top systemic risk.** Token auth that silently degrades to open access when env vars are unset means a misconfigured production deployment has zero access control. This affects Spoofing, Tampering, Repudiation, and Elevation of Privilege categories simultaneously.

2. **External LLM data exposure is the primary confidentiality concern.** Incident data is sent to Google Gemini API with only regex-based PII redaction, which may not catch telecom-specific identifiers (IMSI, IMEI, cell IDs, internal hostnames).

3. **Audit trail lacks tamper-proofing.** While the JSONL audit log provides an event record, it has no cryptographic integrity guarantees, making it unsuitable as a compliance artifact without additional controls.

4. **No rate limiting creates a straightforward DoS vector.** Combined with the LLM API dependency, this can cascade into quota exhaustion and service degradation.

## Accepted Risks (Demo/Portfolio Context)

The following are known risks accepted for the demo deployment and documented for transparency:

- Optional auth is intentional for frictionless demo access
- SQLite is used for simplicity; not intended for multi-user production
- Streamlit dashboard is unauthenticated by design in demo mode
- Regex-based redaction is a best-effort control for the portfolio context
