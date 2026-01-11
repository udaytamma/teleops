"""LLM Response Viewer for TeleOps."""

import os

import requests
import streamlit as st

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")

st.set_page_config(page_title="LLM Response Viewer", layout="wide")

top_left, top_right = st.columns([5, 1])
with top_right:
    st.markdown(
        "<div style='text-align:right;'>"
        "<a href='/' style='color:#9BB0BF;text-decoration:none;font-size:14px;'>"
        "Home</a></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <style>
    :root {
        --bg: #0B1318;
        --panel: #111B22;
        --ink: #E6F1F7;
        --muted: #9BB0BF;
        --border: #1C2A33;
        --chip: #0B2A33;
    }
    .main { background: var(--bg); color: var(--ink); }
    .teleops-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
    }
    .teleops-title {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 6px;
        color: var(--ink);
    }
    .teleops-muted {
        color: var(--muted);
        font-size: 13px;
    }
    .teleops-divider {
        height: 1px;
        background: var(--border);
        margin: 12px 0;
    }
    .teleops-chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: var(--chip);
        color: #A7F3E6;
        border: 1px solid rgba(39,179,158,0.35);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="teleops-card">
        <span class="teleops-chip">LLM RCA CALL TRACE</span>
        <div class="teleops-title">LLM Request / Response Viewer</div>
        <div class="teleops-muted">Inspect the prompt inputs and structured output for a selected incident.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

incidents_resp = requests.get(f"{API_URL}/incidents", timeout=30)
if incidents_resp.status_code >= 400:
    st.error(incidents_resp.text)
    st.stop()

incidents = incidents_resp.json()
if not incidents:
    st.info("No incidents available. Generate a scenario first.")
    st.stop()

selected = st.selectbox("Select incident", options=incidents, format_func=lambda i: i["id"])

artifact_resp = requests.get(
    f"{API_URL}/rca/{selected['id']}/latest",
    params={"source": "llm"},
    timeout=30,
)
if artifact_resp.status_code == 404:
    st.warning("No LLM RCA found for this incident. Run LLM RCA to generate a response.")
    if st.button("Run LLM RCA", type="primary"):
        run_resp = requests.post(f"{API_URL}/rca/{selected['id']}/llm", timeout=60)
        if run_resp.status_code >= 400:
            st.error(run_resp.text)
            st.stop()
        artifact_resp = requests.get(
            f"{API_URL}/rca/{selected['id']}/latest",
            params={"source": "llm"},
            timeout=30,
        )
        if artifact_resp.status_code >= 400:
            st.error(artifact_resp.text)
            st.stop()
    else:
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
    st.markdown('<div class="teleops-card">', unsafe_allow_html=True)
    st.markdown('<div class="teleops-title">LLM Request</div>', unsafe_allow_html=True)
    st.markdown('<div class="teleops-muted">Incident, sampled alerts, and RAG context.</div>', unsafe_allow_html=True)
    st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)

    st.markdown("**Incident**")
    st.json(llm_request.get("incident", {}))

    st.markdown("**Alerts Sample**")
    alerts_sample = llm_request.get("alerts_sample", [])
    if alerts_sample:
        st.json(alerts_sample)
    else:
        st.write("No alert sample recorded.")

    st.markdown("**RAG Context**")
    rag_context = llm_request.get("rag_context", [])
    if rag_context:
        for idx, item in enumerate(rag_context, start=1):
            st.write(f"{idx}. {item}")
    else:
        st.write("No RAG context recorded.")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="teleops-card">', unsafe_allow_html=True)
    st.markdown('<div class="teleops-title">LLM Response</div>', unsafe_allow_html=True)
    st.markdown('<div class="teleops-muted">Structured output from the LLM.</div>', unsafe_allow_html=True)
    st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)

    if llm_response:
        st.json(llm_response)
    else:
        st.write("No response recorded.")

    st.markdown("</div>", unsafe_allow_html=True)
