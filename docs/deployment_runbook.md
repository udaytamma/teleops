# Deployment Runbook (Cloud Run)

This runbook documents a lightweight deployment path for demo purposes.

## Assumptions
- Backend is a single FastAPI service.
- LLM provider is hosted (Gemini or compatible) to avoid GPU needs.
- RAG index is built locally and bundled or rebuilt on deploy.

## Steps
1) Build container image
   - `docker build -t teleops-api .`
2) Push image to artifact registry
3) Deploy to Cloud Run
   - Set env vars: `LLM_PROVIDER`, `GEMINI_API_KEY`, `DATABASE_URL`
4) Verify health
   - `GET /incidents` returns HTTP 200
5) Deploy Streamlit UI (optional)
   - Run as a separate Cloud Run service or local operator demo

## Rollback
- Redeploy the previous container image tag.

## Observability
- Enable Cloud Run request logs.
- Store RCA artifacts and integration events in persistent storage.
