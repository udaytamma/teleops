# TeleOps / MSPOps AI Platform (MVP)

Minimal, end-to-end demo for MSP/telco incident RCA with synthetic data, RAG, and LLM-driven RCA.

## What It Does
- Generate synthetic network degradation alerts.
- Correlate alerts into incidents.
- Produce baseline (rules-only) RCA.
- Produce LLM RCA using RAG context.
- Simple Streamlit UI for incident review.

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

## Configuration
Set these environment variables as needed:

- `DATABASE_URL` (default: `sqlite:///./teleops.db`)
- `LLM_PROVIDER`: `local_telellm` | `hosted_telellm` | `gemini`
- `LLM_MODEL`: model name (e.g., `tele-llm-3b` or `gemini-1.5-flash`)
- `LLM_BASE_URL`: OpenAI-compatible base URL for Tele-LLM
- `LLM_API_KEY`: API key for Tele-LLM if required
- `GEMINI_API_KEY`: API key for Gemini provider

You can copy `.env.example` to `.env` for a starting point.

## RAG Setup
RAG uses LlamaIndex with HuggingFace embeddings and a simple in-memory vector store. The corpus lives in `docs/rag_corpus/`.

You can swap to FAISS later for scale; this MVP keeps dependencies minimal for local setup.

## Cloud Demo (GCP Cloud Run)
- Build a container that runs `uvicorn teleops.api.app:app`.
- Use a hosted LLM provider (Gemini) for Cloud Run since it is CPU-only.
- Set `LLM_PROVIDER=gemini` and `GEMINI_API_KEY`.

## Evaluation
Run the evaluation script:

```bash
python scripts/evaluate.py
```

## Preflight Checks
Run a quick sanity check for RAG, LLM config, API, and UI:

```bash
python scripts/preflight.py
```

## Project Structure
```
teleops/
  teleops/
  ui/
  docs/
  tests/
  scripts/
```
