# Deployment Runbook (Cloud Run)

This runbook documents deployment, operations, and cost for the TeleOps platform.

## Assumptions
- Backend is a single FastAPI service.
- LLM provider is hosted (Gemini or compatible) to avoid GPU needs.
- RAG index is built locally and bundled or rebuilt on deploy.

## Deployment Steps

### 1. Build and Push Container Image
```bash
docker build -t teleops-api .
docker tag teleops-api gcr.io/<project>/teleops-api:latest
docker push gcr.io/<project>/teleops-api:latest
```

### 2. Deploy to Cloud Run
```bash
gcloud run deploy teleops-api \
  --image gcr.io/<project>/teleops-api:latest \
  --set-env-vars LLM_PROVIDER=gemini,GEMINI_API_KEY=<key>,DATABASE_URL=<url>,ENVIRONMENT=production,API_TOKEN=<token>,ADMIN_TOKEN=<token>,METRICS_TOKEN=<token> \
  --port 8000 \
  --memory 512Mi \
  --cpu 1
```

### 3. Verify Health
```bash
curl -f https://<service-url>/health
curl -H "X-API-Key: <API_TOKEN>" -f https://<service-url>/incidents
```

### 4. Deploy Streamlit UI (Optional)
- Run as a separate Cloud Run service or local operator demo.
- Set `API_BASE_URL` to point to the deployed API.
- Export `TELEOPS_API_TOKEN` (and optionally `TELEOPS_METRICS_TOKEN`) so the UI passes `X-API-Key` headers.

## Rollback
- Redeploy the previous container image tag:
```bash
gcloud run deploy teleops-api --image gcr.io/<project>/teleops-api:<previous-tag>
```

## Observability
- Enable Cloud Run request logs in GCP Console.
- Store RCA artifacts and integration events in persistent storage.
- Monitor `/metrics/overview` endpoint for key performance indicators.

## Common Operations

### LLM Timeout/Failure
- TeleOps automatically falls back to baseline RCA when the LLM fails (timeout, invalid JSON, network error).
- No manual intervention needed for RCA availability.
- Check LLM latency in `/metrics/overview` to diagnose persistent issues.
- If LLM failures are sustained, verify `GEMINI_API_KEY` and network connectivity.

### RAG Index Rebuild
```bash
# SSH into container or run locally
python -c "from teleops.rag.index import build_index; build_index()"
```
- RAG index is built from `docs/rag_corpus/` markdown files.
- Rebuild is needed after adding new runbook documents.

### Database Reset and Recovery
```bash
# Reset all incidents and RCA artifacts (destructive)
curl -H "X-API-Key: <ADMIN_TOKEN>" -X POST https://<service-url>/reset
```
- SQLite database is at `storage/teleops.db`.
- Back up the file before any destructive operations.

### Health Check Monitoring
- `GET /health` returns HTTP 200 when the API is running.
- `GET /incidents` returns HTTP 200 with incident list.
- `GET /metrics/overview` returns dashboard KPIs.

---

## Cost Estimate (Demo Scale)

Estimates assume a demo workload with low traffic.

| Component | Monthly Cost |
|-----------|-------------|
| Cloud Run (API) - 1 vCPU / 512MB, minimal traffic | $10 - $30 |
| Hosted LLM (Gemini pay-per-token) | $20 - $60 |
| Storage (SQLite or small managed Postgres) | $5 - $20 |
| **Total (Demo Scale)** | **$35 - $110** |

Notes:
- Costs increase linearly with LLM usage and concurrent users.
- GPU hosting for local LLMs is excluded from this estimate.
