# TeleOps Capstone Fixes (Critical/High/Medium)

This document records each fix applied, with rationale, alternatives, and accepted risks.

## 1) Secret Exposure (.env)
- From → To: Committed `.env` with live API key → file removed from repo.
- Why needed: Prevents accidental credential leakage.
- Why chosen over other options: Removal is the only safe remediation for leaked secrets in a capstone.
- Risk accepted: None; assumes key rotation happens outside repo.
- Docs needed: none (already in `.gitignore`).

## 2) UI Container Missing Files
- From → To: Dockerfile excluded `ui/` → `COPY ui/ ui/` added.
- Why needed: Streamlit service failed to start in container.
- Why chosen over other options: Minimal fix without separate UI image.
- Risk accepted: Larger image size.
- Docs needed: none.

## 3) UI/API Env Var Mismatch
- From → To: `API_BASE_URL` in compose, `TELEOPS_API_URL` in UI → compose updated + UI fallback to `API_BASE_URL`.
- Why needed: UI could not reach API inside Docker.
- Why chosen over other options: Backward-compatible with both env var names.
- Risk accepted: None.
- Docs needed: `teleops/README.md`.

## 4) Access Control / RBAC
- From → To: Optional token on a few endpoints → API/Admin/Metrics tokens applied across endpoints; admin required for reset/webhooks.
- Why needed: Demonstrates control plane protection for a Principal TPM capstone.
- Why chosen over other options: Simple shared tokens avoid OAuth complexity.
- Risk accepted: Shared tokens lack per-user auditability.
- Docs needed: `teleops/docs/security_controls.md`, `teleops/.env.example`, `teleops/README.md`.

## 5) Redaction Policy Enforcement
- From → To: Raw payloads and unredacted prompts → redaction of IP/email/tenant in LLM inputs, raw payloads excluded by default, `include_raw=true` opt‑in.
- Why needed: Aligns implementation with documented redaction policy.
- Why chosen over other options: Lightweight regex redaction avoids new dependencies.
- Risk accepted: Regex-based redaction can miss edge cases.
- Docs needed: `teleops/docs/redaction_policy.md`, `teleops/README.md`.

## 6) RAG Query Hard‑Coded
- From → To: Always “network degradation” → query derived from incident summary + alert types.
- Why needed: Improves relevance across all scenarios.
- Why chosen over other options: Uses existing data; no extra NLP pipeline.
- Risk accepted: Summary quality directly affects retrieval.
- Docs needed: none.

## 7) Evaluation Methodology
- From → To: Fixed incident summary + single scenario → round‑robin scenario coverage + normalized similarity scoring.
- Why needed: Matches success metrics across multiple incident types.
- Why chosen over other options: Keeps evaluation fast and deterministic.
- Risk accepted: Still text-similarity based (no embeddings).
- Docs needed: `teleops/docs/requirements.md` (optional note).

## 8) Tenant Isolation
- From → To: No tenant scoping → optional `X-Tenant-Id` enforcement + query filters.
- Why needed: Demonstrates multi‑tenant hygiene for shared datasets.
- Why chosen over other options: Header-based gating avoids auth provider setup.
- Risk accepted: Depends on caller to supply correct tenant header.
- Docs needed: `teleops/docs/security_controls.md`, `teleops/README.md`.

## 9) Integration Log Rotation
- From → To: Append-only JSONL with no rotation → size-based rotation with backups.
- Why needed: Prevents unbounded log growth.
- Why chosen over other options: Simple file rotation without log infra.
- Risk accepted: Rotation is size-based; no centralized log aggregation.
- Docs needed: `teleops/docs/security_controls.md`, `teleops/.env.example`.

## 10) Gemini Timeout Unused
- From → To: Config exists but unused → passed into SDK `request_options` with fallback.
- Why needed: Avoids long/hanging LLM calls.
- Why chosen over other options: Minimal SDK change.
- Risk accepted: Older SDKs ignore timeout (fallback path).
- Docs needed: none.

## 11) RAG Index Rebuilt Per Request
- From → To: Build/load every call → cached in module-level singleton.
- Why needed: Reduces latency and CPU.
- Why chosen over other options: No external cache required.
- Risk accepted: Cache invalidation requires restart when corpus changes.
- Docs needed: none.

## 12) SQLite Data Persistence
- From → To: Container lost `teleops.db` on rebuild → bind-mounted volume in compose.
- Why needed: Prevents data loss during demo sessions.
- Why chosen over other options: Simplest persistence for SQLite.
- Risk accepted: Single-file DB still not HA.
- Docs needed: `teleops/docker-compose.yml` (no doc change).

## 13) Generated Artifacts in Repo
- From → To: Committed `storage/`, `.coverage`, `.db`, `__pycache__`, etc. → removed from repo.
- Why needed: Avoids leaking data and keeps repo clean.
- Why chosen over other options: Deleting tracked artifacts is the only clean fix.
- Risk accepted: None.
- Docs needed: none (already in `.gitignore`).

## 14) LLM Provider Default Mismatch
- From → To: Default `local_telellm` vs README default `gemini` → config default set to `gemini`.
- Why needed: Aligns runtime with documentation and docker-compose defaults.
- Why chosen over other options: Avoids doc drift.
- Risk accepted: Requires `GEMINI_API_KEY` when LLM is invoked.
- Docs needed: `teleops/README.md`, `teleops/teleops/config.py`.

## 15) UI Token/Tenant Support
- From → To: UI only sent API token → UI now supports metrics token + tenant header.
- Why needed: Keeps UI working with new access controls.
- Why chosen over other options: Env-driven headers are simplest.
- Risk accepted: Token handling still manual.
- Docs needed: `teleops/README.md`.
