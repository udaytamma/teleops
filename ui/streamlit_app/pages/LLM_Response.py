"""TeleOps LLM Response Viewer."""

import os
import requests
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, hero, card_start, card_end, card_header, divider, nav_links, badge, empty_state

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
REQUEST_HEADERS = {"X-API-Key": API_TOKEN} if API_TOKEN else {}

st.set_page_config(page_title="LLM Response Viewer", layout="wide")
inject_theme()

nav_links([
    ("Dashboard", "/", False),
    ("LLM Trace", "/LLM_Response", True),
    ("Observability", "/Observability", False),
], position="end")

st.write("")

hero(
    title="LLM Request / Response Viewer",
    subtitle="Inspect prompt inputs, RAG context, and structured output for debugging.",
    chip_text="LLM TRACE",
)

st.write("")

incidents_resp = requests.get(f"{API_URL}/incidents", headers=REQUEST_HEADERS, timeout=30)
if incidents_resp.status_code >= 400:
    st.error(incidents_resp.text)
    st.stop()

incidents = incidents_resp.json()
if not incidents:
    empty_state("No incidents available. Generate a scenario first.", "")
    st.stop()

selected = st.selectbox("Select Incident", options=incidents, format_func=lambda i: f"{i['id'][:12]}... - {i.get('summary', 'No summary')[:40]}")

artifact_resp = requests.get(
    f"{API_URL}/rca/{selected['id']}/latest",
    params={"source": "llm"},
    headers=REQUEST_HEADERS,
    timeout=30,
)

if artifact_resp.status_code == 404:
    st.warning("No LLM RCA found for this incident.")
    if st.button("Run LLM RCA", type="primary"):
        with st.spinner("Running LLM RCA..."):
            run_resp = requests.post(f"{API_URL}/rca/{selected['id']}/llm", headers=REQUEST_HEADERS, timeout=60)
        if run_resp.status_code >= 400:
            st.error(run_resp.text)
        else:
            st.rerun()
    st.stop()
elif artifact_resp.status_code >= 400:
    st.error(artifact_resp.text)
    st.stop()

artifact = artifact_resp.json()
evidence = artifact.get("evidence", {})
llm_request = evidence.get("llm_request", {})
llm_response = evidence.get("llm_response", {})

left, right = st.columns(2, gap="large")

with left:
    card_start()
    card_header("LLM Request", "Incident context, alerts, and RAG chunks sent to model")

    st.markdown("**Incident Context**")
    st.json(llm_request.get("incident", {}))

    divider()

    st.markdown("**Alerts Sample**")
    alerts = llm_request.get("alerts_sample", [])
    if alerts:
        st.json(alerts[:5])
        if len(alerts) > 5:
            st.caption(f"+ {len(alerts) - 5} more alerts")
    else:
        st.markdown("<p style='color: var(--ink-dim);'>No alerts recorded</p>", unsafe_allow_html=True)

    divider()

    st.markdown("**RAG Context**")
    rag = llm_request.get("rag_context", [])
    if rag:
        for idx, chunk in enumerate(rag, 1):
            st.markdown(f"**Chunk {idx}:**")
            st.markdown(f"<div style='background: var(--bg); padding: 12px; border-radius: 8px; font-size: 13px; color: var(--ink-muted); margin-bottom: 8px;'>{chunk[:300]}{'...' if len(chunk) > 300 else ''}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: var(--ink-dim);'>No RAG context</p>", unsafe_allow_html=True)

    card_end()

with right:
    card_start("accent")
    card_header("LLM Response", "Structured JSON output from the model")

    if llm_response:
        st.markdown(f"{badge(artifact.get('model', 'unknown'), 'accent')} &nbsp; {badge(artifact.get('generated_at', '')[:19], 'muted')}", unsafe_allow_html=True)
        st.write("")
        st.json(llm_response)
    else:
        empty_state("No response recorded", "")

    card_end()
