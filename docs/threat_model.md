# Threat Model (Minimal)

## Assets
- Alert, incident, and RCA data stored in the database.
- LLM inputs/outputs used for RCA reasoning.
- Audit logs (integration events, RCA artifacts).

## Threats
- Unauthorized access to incident data (confidentiality).
- Prompt injection via untrusted alerts or RAG content (integrity).
- Leakage of sensitive data in LLM outputs (confidentiality).
- Tampering with RCA evidence or audit logs (integrity).

## Mitigations
- Access controls on API endpoints; separate admin and read-only roles.
- Redaction policy applied to outbound LLM prompts and UI display.
- Immutable append-only logs for integration events.
- Input validation and JSON schema checks for LLM outputs.
