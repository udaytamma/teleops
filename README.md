# TeleOps / MSPOps AI Platform (MVP)

Minimal, end-to-end demo for MSP/telco incident RCA with synthetic data, RAG, and LLM-driven RCA.

## What It Does
- Generate synthetic network degradation alerts (11 scenario types).
- Correlate alerts into incidents using time-window rules.
- Produce baseline RCA using pattern-matching rules (11 patterns).
- Produce LLM RCA using RAG context from runbook corpus.
- Simple Streamlit UI for incident review and RCA comparison.
- OpenAPI documentation at `/docs` and `/redoc`.

## Quick Start (Local)

Recommended Python: 3.11 or 3.12. (Some dependencies do not yet ship wheels for 3.14.)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m teleops.init_db
uvicorn teleops.api.app:app --reload
```

In a second terminal:

```bash
streamlit run ui/streamlit_app/app.py
```

API docs available at http://127.0.0.1:8000/docs

## Configuration
Set these environment variables as needed:

### Core Settings
- `DATABASE_URL` (default: `sqlite:///./teleops.db`)
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `LOG_FORMAT`: `json` or `text` (default: `json`)

### LLM Provider
- `LLM_PROVIDER`: `local_telellm` | `hosted_telellm` | `gemini`
- `LLM_MODEL`: model name (e.g., `tele-llm-3b` or `gemini-1.5-flash`)
- `LLM_BASE_URL`: OpenAI-compatible base URL for Tele-LLM
- `LLM_API_KEY`: API key for Tele-LLM if required
- `LLM_TIMEOUT_SECONDS`: Timeout for LLM requests (default: `60`)
- `GEMINI_API_KEY`: API key for Gemini provider
- `GEMINI_TIMEOUT_SECONDS`: Timeout for Gemini requests (default: `120`)

### RAG Settings
- `RAG_CORPUS_DIR`: Directory for runbook markdown files (default: `./docs/rag_corpus`)
- `RAG_TOP_K`: Number of RAG nodes to retrieve (default: `4`)

### Security
- `API_TOKEN`: optional API token for write endpoints and metrics
- `TELEOPS_API_TOKEN`: optional UI token for API calls

You can copy `.env.example` to `.env` for a starting point.

## Scenario Types

The platform supports 11 incident scenario types:

| Scenario | Description |
|----------|-------------|
| `network_degradation` | Packet loss and latency on core routers |
| `dns_outage` | Authoritative DNS cluster failures |
| `bgp_flap` | BGP session instability with upstream peers |
| `fiber_cut` | Optical transport link failures |
| `router_freeze` | Control plane freeze on core routers |
| `isp_peering_congestion` | Congestion on ISP peering links |
| `ddos_edge` | Volumetric DDoS attacks on edge infrastructure |
| `mpls_vpn_leak` | MPLS/L3VPN route leaks from VRF misconfiguration |
| `cdn_cache_stampede` | CDN cache stampede from TTL misconfiguration |
| `firewall_rule_misconfig` | Firewall rules blocking critical traffic |
| `database_latency_spike` | Database contention affecting MSP-hosted apps |

## RAG Setup
RAG uses LlamaIndex with HuggingFace embeddings (MiniLM) and a simple in-memory vector store. The corpus lives in `docs/rag_corpus/`.

Expected corpus structure:
```
docs/rag_corpus/
├── backbone-troubleshooting.md
├── dns-operations.md
├── bgp-peering.md
├── optical-transport.md
├── security-incidents.md
├── database-performance.md
└── cdn-caching.md
```

You can swap to FAISS later for scale; this MVP keeps dependencies minimal for local setup.

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/generate` | Generate synthetic alerts and correlate incidents |
| GET | `/alerts` | List all alerts |
| GET | `/incidents` | List all incidents |
| POST | `/rca/{id}/baseline` | Generate baseline RCA (pattern-matching) |
| POST | `/rca/{id}/llm` | Generate LLM RCA with RAG context |
| GET | `/health` | Health check for monitoring |
| GET | `/docs` | OpenAPI documentation (Swagger) |
| GET | `/redoc` | OpenAPI documentation (ReDoc) |

All POST endpoints use Pydantic validation for request payloads.

## Cloud Demo (GCP Cloud Run)
- Build a container that runs `uvicorn teleops.api.app:app`.
- Use a hosted LLM provider (Gemini) for Cloud Run since it is CPU-only.
- Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`.

## Evaluation
Run the evaluation script:

```bash
python scripts/evaluate.py
```

You can also score against the manual labels set:

```bash
python scripts/evaluate.py --labels-file docs/evaluation/manual_labels.jsonl
```

To write evaluation results for the dashboard:

```bash
python scripts/evaluate.py --write-json storage/evaluation_results.json
```

## Data Import
Load anonymized sample alerts into the database:

```bash
python scripts/import_logs.py --file docs/data_samples/anonymized_alerts.jsonl
```

## Tests
Run tests with coverage and dashboard artifacts:

```bash
python scripts/run_tests.py
```

Test coverage includes:
- API endpoints (generation, listing, RCA)
- Pattern-matching baseline RCA
- LLM client adapters and JSON parsing
- Correlation logic
- Integration webhooks (ServiceNow, Jira)

## Preflight Checks
Run a quick sanity check for RAG, LLM config, API, and UI:

```bash
python scripts/preflight.py
```

## Project Structure
```
teleops/
  teleops/
    api/app.py          # FastAPI REST API with Pydantic validation
    config.py           # Pydantic settings + structured logging
    llm/client.py       # LLM adapters (OpenAI-compatible, Gemini)
    llm/rca.py          # Baseline + LLM RCA generation
    data_gen/generator.py # 11 scenario type generators
    incident_corr/correlator.py
    rag/index.py        # LlamaIndex RAG
    models.py           # SQLAlchemy ORM models
  ui/
  docs/
  tests/
  scripts/
```

## Docs
- `docs/integrations/README.md`
- `docs/data_dictionary.md`
- `docs/test_plan.md`
- `docs/scenario_catalog.md`
- `docs/demo_results.md`
- `docs/demo_script.md`
- `docs/demo_video_assets.md`
- `docs/evaluation/labeling_rubric.md`
- `docs/threat_model.md`
- `docs/redaction_policy.md`
- `docs/deployment_runbook.md`
