# Progress Log

- 2025-09-24: Initialized MVP repo structure, models, generator, correlation, API, RAG, LLM adapters, UI, and evaluation script.
- 2025-09-24: Test dependency install blocked on Python 3.14 (missing wheels for Pillow/pydantic-core). Recommend Python 3.11/3.12 for local runs.
- 2026-02-07: Principal TPM Production Hardening
  - Added pyproject.toml for proper Python packaging (editable install)
  - Expanded RAG corpus to 7 MSO-oriented runbooks (HFC, CMTS, DOCSIS, VOD, OSS/BSS)
  - Created Dockerfile and docker-compose.yml for containerized deployment
  - Added GitHub Actions CI pipeline with test, lint, and Docker build
  - Documented evaluation results in README with metrics table
  - Updated .env.example with complete configuration options
  - Fixed README project structure and uvicorn command
  - Created CONTRIBUTING.md for contributor onboarding
