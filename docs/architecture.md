# Architecture (MVP)

## Components
- Data plane: synthetic generator + alert store.
- Control plane: FastAPI endpoints.
- AI plane: RAG + LLM RCA.
- Presentation: Streamlit UI.

## Data Flow
1) Generate synthetic alerts.
2) Correlate alerts into incidents.
3) Run baseline RCA.
4) Run LLM RCA with RAG context.
5) Display results in UI.
