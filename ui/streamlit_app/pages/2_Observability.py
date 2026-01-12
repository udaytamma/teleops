"""TeleOps Observability Dashboard."""

import os
import requests
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, hero, nav_links, metric_card, progress_bar, empty_state

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
REQUEST_HEADERS = {"X-API-Key": API_TOKEN} if API_TOKEN else {}

st.set_page_config(page_title="TeleOps Observability", layout="wide")
inject_theme()

nav_links([
    ("Incident Generator", "pages/1_Incident_Generator.py", False),
    ("LLM Trace", "pages/3_LLM_Trace.py", False),
    ("Observability", "pages/2_Observability.py", True),
], position="end")

st.write("")

hero(
    title="Observability Dashboard",
    subtitle="Operational metrics, KPIs, test results, and evaluation data.",
    chip_text="METRICS",
)

st.write("")

resp = requests.get(f"{API_URL}/metrics/overview", headers=REQUEST_HEADERS, timeout=30)
if resp.status_code >= 400:
    st.error(resp.text)
    st.stop()

payload = resp.json()
counts = payload.get("counts", {})
kpis = payload.get("kpis", {})

# Metric cards
cols = st.columns(4)
with cols[0]:
    st.markdown(metric_card(counts.get("alerts", 0), "Total Alerts", "accent"), unsafe_allow_html=True)
with cols[1]:
    st.markdown(metric_card(counts.get("incidents", 0), "Incidents", "accent-2"), unsafe_allow_html=True)
with cols[2]:
    st.markdown(metric_card(counts.get("rca_artifacts", 0), "RCA Artifacts", "accent-3"), unsafe_allow_html=True)
with cols[3]:
    avg = kpis.get("avg_alerts_per_incident", 0.0)
    st.markdown(metric_card(f"{avg:.1f}", "Avg Alerts/Incident", "ink"), unsafe_allow_html=True)

st.write("")

# Test Results
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Test Results</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">pytest coverage and pass rate</span>
    </div>
    """,
    unsafe_allow_html=True,
)

test_results = payload.get("test_results")
if test_results:
    tests = test_results.get("tests", {})
    coverage = test_results.get("coverage", {})
    pass_rate = tests.get("pass_rate", 0.0) * 100
    coverage_pct = coverage.get("percent_covered", 0.0)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Pass Rate:** {pass_rate:.1f}%")
        st.markdown(progress_bar(pass_rate, "success" if pass_rate >= 90 else "warning"), unsafe_allow_html=True)
    with col2:
        st.markdown(f"**Coverage:** {coverage_pct:.1f}%")
        st.markdown(progress_bar(coverage_pct, "success" if coverage_pct >= 80 else "warning"), unsafe_allow_html=True)

    with st.expander("Raw test data"):
        st.json(test_results)
else:
    empty_state("No test results. Run: python scripts/run_tests.py", "")

st.write("")

# Evaluation Results
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Evaluation Results</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">Baseline vs LLM accuracy comparison</span>
    </div>
    """,
    unsafe_allow_html=True,
)

evaluation_results = payload.get("evaluation_results")
if evaluation_results:
    with st.expander("View evaluation data", expanded=True):
        st.json(evaluation_results)
else:
    empty_state("No evaluation results. Run: python scripts/evaluate.py --write-json storage/evaluation_results.json", "")
