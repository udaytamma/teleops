# Redaction and Safety Policy

## Redaction Rules
- Strip IPs and email-like tokens from LLM prompts and stored artifacts (regex-based).
- Replace tenant identifiers with stable anonymized aliases (`tenant-<sha256[:8]>`).
- Do not include full raw payloads in UI unless explicitly requested via `include_raw=true`.

## Data Minimization
- RCA artifacts store only evaluation metadata (RAG query used, alert count, RAG chunks retrieved), not full LLM request/response payloads.
- Full LLM inputs/outputs are not persisted; only the resulting hypotheses, evidence summary, and confidence scores are retained.
- Alert data sent to the LLM is redacted before transmission and not stored in the artifact.

## Safety Controls
- LLM outputs must be valid JSON; reject markdown-wrapped responses.
- Remediation steps are advisory and require human approval.
- RCA hypotheses default to `pending_review` status and must be explicitly accepted or rejected via the review endpoint before being acted upon.
