# TeleOps Working Agreement (Persistent)

## Communication
- Be direct and non-sugar-coated.
- Keep responses concise; use tables for comparisons when helpful.
- Provide a plan before implementation.

## Definition of Done
- "Done" means tested.
- After code changes, run relevant tests or preflight/smoke checks.
- Restart servers after backend/UI changes before validating behavior.

## Runtime Hygiene
- Verify ports are free before starting servers.
- Use preflight checks after changes.

## LLM Handling
- Use robust JSON parsing for LLM outputs.
- Avoid markdown-wrapped JSON in prompts.
- Store only structured RCA outputs and metadata; do not persist full LLM prompt/response payloads.

## Product/UX
- Prefer polished, ops-grade UI with clear hierarchy and readable typography.
- Keep incident correlation scoped to latest ingest batch for clean evaluation.
