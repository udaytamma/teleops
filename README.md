# TeleOps - AI-Powered Telecom Incident RCA Platform

Intelligent root cause analysis for telecom/MSP network incidents using synthetic data, RAG pipelines, and LLM-driven diagnostics.

[![CI](https://github.com/udaytamma/teleops/actions/workflows/ci.yml/badge.svg)](https://github.com/udaytamma/teleops/actions)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.112-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38-ff4b4b.svg)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Overview

TeleOps demonstrates AI-augmented incident management for telecom Network Operations Centers (NOC). It generates realistic network incidents, correlates alerts, and produces root cause analyses using both pattern-matching baselines and LLM-powered RAG pipelines.

## Features

### Incident Generation
- **11 Scenario Types** - Network degradation, DNS outage, BGP flap, fiber cut, and more
- **Realistic Alerts** - Time-correlated alert sequences with proper severity escalation
- **Configurable Parameters** - Alert count, time windows, scenario weights

### RCA Generation
- **Baseline RCA** - Deterministic pattern-matching with 11 scenario-specific rules
- **LLM RCA** - RAG-enhanced analysis using runbook corpus
- **Side-by-Side Comparison** - Evaluate baseline vs. LLM quality

### Observability
- **Structured JSON Logging** - Production-ready log format
- **OpenAPI Documentation** - Swagger UI and ReDoc
- **Metrics Dashboard** - Incident statistics and RCA comparison

## Tech Stack

| Layer | Technology |
|-------|------------|
| **API** | FastAPI with Pydantic validation |
| **LLM** | Google Gemini 2.0 Flash |
| **RAG** | LlamaIndex + HuggingFace embeddings |
| **Dashboard** | Streamlit with NOC-style theme |
| **Database** | SQLite (MVP) |

## Quick Start

### Prerequisites
- Python 3.11 or 3.12 (recommended)
- Google Gemini API key

### Installation

```bash
# Clone repository
git clone https://github.com/udaytamma/teleops.git
cd teleops

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Initialize database
python -m teleops.init_db

# Start API server
uvicorn teleops.api.app:app --reload --port 8000
```

### Running the Dashboard

```bash
# In a separate terminal
streamlit run ui/streamlit_app/app.py --server.port 8501
```

- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Dashboard**: [http://localhost:8501](http://localhost:8501)

## Scenario Types

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

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| POST | `/generate` | Generate synthetic alerts and correlate incidents |
| GET | `/incidents` | List all incidents |
| POST | `/rca/{id}/baseline` | Generate pattern-matching RCA |
| POST | `/rca/{id}/llm` | Generate LLM RCA with RAG context |
| GET | `/metrics/overview` | Dashboard metrics |
| POST | `/reset` | Clear all incidents |
| GET | `/health` | Health check |

Notes:
- If `REQUIRE_TENANT_ID=true`, include `X-Tenant-Id` on requests.
- Raw alert payloads are excluded by default; use `include_raw=true` when needed.

## Project Structure

```
teleops/
├── teleops/                      # Main Python package
│   ├── api/
│   │   └── app.py                # FastAPI application
│   ├── data_gen/
│   │   └── generator.py          # Synthetic incident generation
│   ├── incident_corr/
│   │   └── correlator.py         # Alert correlation
│   ├── llm/
│   │   ├── client.py             # LLM adapter
│   │   └── rca.py                # RCA generation (baseline + LLM)
│   ├── rag/
│   │   └── index.py              # RAG pipeline
│   ├── config.py                 # Settings management
│   ├── models.py                 # SQLAlchemy models
│   └── db.py                     # Database setup
├── ui/
│   └── streamlit_app/            # Dashboard
│       ├── app.py                # Entry point
│       ├── theme.py              # NOC-style theme
│       └── pages/                # Multi-page app
├── docs/                         # Documentation & RAG corpus
├── storage/                      # Persistent data
└── tests/                        # Test suite (17 files)
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `LLM_PROVIDER` | `gemini` or `local_telellm` | `gemini` |
| `LLM_TIMEOUT_SECONDS` | LLM request timeout | `60` |
| `RAG_CORPUS_DIR` | Runbook directory | `./docs/rag_corpus` |
| `RAG_TOP_K` | Retrieved context chunks | `4` |
| `LOG_FORMAT` | `json` or `text` | `json` |
| `API_TOKEN` | API token for read/write endpoints | optional |
| `ADMIN_TOKEN` | Admin token for destructive actions | optional |
| `METRICS_TOKEN` | Token for `/metrics/overview` | optional |
| `REQUIRE_TENANT_ID` | Enforce `X-Tenant-Id` header | `false` |
| `TELEOPS_TENANT_ID` | UI header value for tenant | optional |

### RAG Corpus

12 MSO-oriented runbooks in `docs/rag_corpus/` (~1200 lines):

```
docs/rag_corpus/
├── hfc-network-troubleshooting.md   # CMTS, DOCSIS, HFC plant
├── dns-resolver-operations.md       # Residential DNS, CDN steering
├── bgp-peering-transit.md           # IX peering, transit providers
├── optical-transport-headend.md     # Fiber rings, DWDM, headend
├── security-edge-incidents.md       # DDoS, CPE exploits
├── oss-bss-performance.md           # Provisioning, billing systems
├── video-cdn-delivery.md            # VOD, cache, ABR streaming
├── mpls-vpn-enterprise.md           # L3VPN, Metro-E, VRF leaks
├── voip-telephony.md                # SIP, E911, MTA, call quality
├── iptv-linear-channels.md          # QAM, multicast, STB, EPG
├── wifi-managed-services.md         # xFi pods, hotspots, RADIUS
└── weather-disaster-recovery.md     # Ice storms, floods, hurricanes
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
python scripts/run_tests.py

# Preflight checks
python scripts/preflight.py
```

## Documentation

- **Architecture**: [zeroleaf.dev/docs/telcoops/architecture](https://zeroleaf.dev/docs/telcoops/architecture)
- **API Reference**: [zeroleaf.dev/docs/telcoops/api-reference](https://zeroleaf.dev/docs/telcoops/api-reference)
- **Design Rationale**: [zeroleaf.dev/nebula/tops-redundant/design-rationale](https://zeroleaf.dev/nebula/tops-redundant/design-rationale)

## Evaluation

Run the evaluation script to score RCA quality:

```bash
# Basic evaluation
python scripts/evaluate.py

# Against manual labels
python scripts/evaluate.py --labels-file docs/evaluation/manual_labels.jsonl

# Export results for dashboard
python scripts/evaluate.py --write-json storage/evaluation_results.json
```

### Evaluation Results (February 2026)

| Metric | Baseline | LLM (Gemini) | Notes |
|--------|----------|--------------|-------|
| Accuracy (50 scenarios) | 100%* | 44% | String similarity scoring |
| P50 Latency | &lt;10ms | ~2s | LLM adds network round-trip |
| JSON Validity | 100% | 95%+ | Structured output parsing |
| Test Coverage | 87.1% | - | 45 tests, 100% pass rate |

*Baseline achieves 100% because rules are tuned to match ground truth phrasing exactly.

**Interpretation:** The LLM accuracy appears lower due to string similarity scoring, which penalizes semantically correct but differently-phrased hypotheses. Semantic evaluation (embedding similarity) would show higher LLM performance.

**Future Improvements:**
- Add semantic similarity scoring (embedding-based)
- Fine-tune prompts for more concise output
- Expand RAG corpus with additional MSO scenarios

## Deployment

### Cloud Run (GCP)

```bash
# Build container
docker build -t teleops .

# Deploy with Gemini (CPU-only)
gcloud run deploy teleops \
  --image teleops \
  --set-env-vars LLM_PROVIDER=gemini,GEMINI_API_KEY=$GEMINI_API_KEY
```

## License

This project is licensed under the MIT License.

## Author

**Uday Tamma**
- Portfolio: [zeroleaf.dev](https://zeroleaf.dev)
- GitHub: [@udaytamma](https://github.com/udaytamma)

## Acknowledgments

- Built as a Principal TPM capstone project
- Demonstrates AI/ML ops for telecom domain
- Uses Google Gemini for LLM capabilities
