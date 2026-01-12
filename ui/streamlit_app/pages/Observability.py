"""Observability dashboard for TeleOps."""

import os

import requests
import streamlit as st

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
REQUEST_HEADERS = {"X-API-Key": API_TOKEN} if API_TOKEN else {}


st.set_page_config(page_title="TeleOps Observability", layout="wide")

st.markdown("## Observability Dashboard")
st.caption("Operational metrics, KPIs, and test/evaluation results.")

resp = requests.get(f"{API_URL}/metrics/overview", headers=REQUEST_HEADERS, timeout=30)
if resp.status_code >= 400:
    st.error(resp.text)
    st.stop()

payload = resp.json()
counts = payload.get("counts", {})
kpis = payload.get("kpis", {})

cols = st.columns(4)
with cols[0]:
    st.metric("Alerts", counts.get("alerts", 0))
with cols[1]:
    st.metric("Incidents", counts.get("incidents", 0))
with cols[2]:
    st.metric("RCA Artifacts", counts.get("rca_artifacts", 0))
with cols[3]:
    st.metric("Avg Alerts/Incident", kpis.get("avg_alerts_per_incident", 0.0))

st.divider()

test_results = payload.get("test_results")
evaluation_results = payload.get("evaluation_results")

st.markdown("### Test Results")
if test_results:
    tests = test_results.get("tests", {})
    coverage = test_results.get("coverage", {})
    st.write(f"Status: {test_results.get('status', 'unknown')}")
    st.write(f"Pass rate: {tests.get('pass_rate', 0.0) * 100:.1f}%")
    st.write(f"Coverage: {coverage.get('percent_covered', 0.0)}%")
    st.json(test_results)
else:
    st.info("No test results found. Run `python scripts/run_tests.py`.")

st.markdown("### Evaluation Results")
if evaluation_results:
    st.json(evaluation_results)
else:
    st.info("No evaluation results found. Run `python scripts/evaluate.py --write-json storage/evaluation_results.json`.")
