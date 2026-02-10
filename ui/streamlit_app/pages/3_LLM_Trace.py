"""TeleOps LLM Response Viewer."""

import os
import requests
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, hero, divider, nav_links, badge, empty_state

API_URL = os.getenv("TELEOPS_API_URL") or os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
TENANT_ID = os.getenv("TELEOPS_TENANT_ID", "")
REQUEST_HEADERS = {}
if API_TOKEN:
    REQUEST_HEADERS["X-API-Key"] = API_TOKEN
if TENANT_ID:
    REQUEST_HEADERS["X-Tenant-Id"] = TENANT_ID

st.set_page_config(page_title="LLM Response Viewer", layout="wide")
inject_theme()

nav_links([
    ("Incident Generator", "pages/1_Incident_Generator.py", False),
    ("LLM Trace", "pages/3_LLM_Trace.py", True),
    ("Observability", "pages/2_Observability.py", False),
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

selected = st.selectbox("Select Incident", options=incidents, format_func=lambda i: f"{i['id']} - {i.get('summary', 'No summary')[:40]}")

artifact_resp = requests.get(
    f"{API_URL}/rca/{selected['id']}/latest",
    params={"source": "llm"},
    headers=REQUEST_HEADERS,
    timeout=30,
)

if artifact_resp.status_code == 404:
    st.warning("No LLM RCA found for this incident.")
    if st.button("Run LLM RCA", type="primary"):
        try:
            with st.spinner("Running LLM RCA (may take up to 2 minutes)..."):
                run_resp = requests.post(f"{API_URL}/rca/{selected['id']}/llm", headers=REQUEST_HEADERS, timeout=180)
            if run_resp.status_code >= 400:
                st.error(run_resp.text)
            else:
                st.rerun()
        except requests.exceptions.Timeout:
            st.error("LLM RCA timed out. Gemini API may be slow — please retry.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to the API. Please check that the backend is running.")
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
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--ink-strong);">LLM Request</h4>
            <span style="font-size: 12px; color: var(--ink-dim);">Input sent to model</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

with right:
    st.markdown(
        """
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--ink-strong);">LLM Response</h4>
                <span style="font-size: 12px; color: var(--ink-dim);">Structured output</span>
            </div>
            <span style="background: linear-gradient(135deg, #6C5CE7, #A29BFE); color: white; font-size: 10px; font-weight: 600; padding: 4px 10px; border-radius: 4px; letter-spacing: 0.05em;">AI-POWERED</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if llm_response:
        st.markdown(f"{badge(artifact.get('model', 'unknown'), 'accent')} &nbsp; {badge(artifact.get('generated_at', '')[:19], 'muted')}", unsafe_allow_html=True)
        st.write("")
        st.json(llm_response)
    else:
        st.markdown("<p style='color: var(--ink-dim); text-align: center; padding: 20px;'>No response recorded</p>", unsafe_allow_html=True)
