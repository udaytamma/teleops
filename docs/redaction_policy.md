# Redaction and Safety Policy

## Redaction Rules
- Strip IPs and email-like tokens from LLM prompts and stored artifacts (regex-based).
- Replace tenant identifiers with stable anonymized aliases (`tenant-<sha256[:8]>`).
- Do not include full raw payloads in UI unless explicitly requested via `include_raw=true`.

## Data Minimization
- RCA artifacts store structured RCA outputs (hypotheses, confidence scores, redacted evidence summary) plus metadata (RAG query, alert count, RAG chunks retrieved).
- Raw prompt/response text is not persisted.
- Alert data sent to the LLM is redacted before transmission and only the redacted summary is stored in the artifact.

## Safety Controls
- LLM outputs must be valid JSON; reject markdown-wrapped responses.
- Remediation steps are advisory and require human approval.
- RCA hypotheses default to `pending_review` status and should be accepted or rejected via the review endpoint before being acted upon (process gate; API does not enforce acceptance by default).
