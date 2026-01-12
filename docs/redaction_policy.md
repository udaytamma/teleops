# Redaction and Safety Policy

## Redaction Rules
- Strip IPs and email-like tokens from LLM prompts.
- Replace tenant identifiers with stable anonymized aliases.
- Do not include full raw payloads in UI unless explicitly requested.

## Safety Controls
- LLM outputs must be valid JSON; reject markdown-wrapped responses.
- Remediation steps are advisory and require human approval.
- Store only minimal retention of LLM inputs/outputs needed for evaluation.
