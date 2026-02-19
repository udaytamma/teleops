"""TeleOps Observability Dashboard."""

import os
import streamlit as st

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import inject_theme, hero, nav_links, metric_card, progress_bar, empty_state, badge, safe_api_call

API_URL = os.getenv("TELEOPS_API_URL") or os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
TENANT_ID = os.getenv("TELEOPS_TENANT_ID", "")
METRICS_TOKEN = os.getenv("TELEOPS_METRICS_TOKEN", API_TOKEN)
REQUEST_HEADERS = {}
if METRICS_TOKEN:
    REQUEST_HEADERS["X-API-Key"] = METRICS_TOKEN
if TENANT_ID:
    REQUEST_HEADERS["X-Tenant-Id"] = TENANT_ID

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
    subtitle="Operational metrics, decision quality, and time-to-context analysis.",
    chip_text="METRICS",
)

st.write("")

resp, err = safe_api_call("GET", f"{API_URL}/metrics/overview", headers=REQUEST_HEADERS, timeout=30)
if err:
    st.error(err)
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

# --- RCA Quality Metrics ---
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">RCA Decision Quality</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">Precision, recall, and confidence calibration</span>
    </div>
    """,
    unsafe_allow_html=True,
)

evaluation_results = payload.get("evaluation_results")
if evaluation_results and evaluation_results.get("quality_metrics"):
    qm = evaluation_results["quality_metrics"]

    # Scoring method badge
    scoring = evaluation_results.get("scoring_method", "unknown")
    runs_count = evaluation_results.get("runs", 0)
    st.markdown(
        f'{badge(scoring, "accent")} &nbsp; '
        f'{badge(f"{runs_count} scenarios", "accent-2")}',
        unsafe_allow_html=True,
    )
    st.write("")

    # Baseline vs LLM comparison
    col_b, col_l = st.columns(2)

    for col, source, label in [(col_b, "baseline", "Baseline (Rules)"), (col_l, "llm", "LLM + RAG")]:
        with col:
            st.markdown(f"**{label}**")
            metrics = qm.get(source)
            if metrics is None:
                st.caption("Not evaluated (LLM not configured)")
                continue

            # Precision & Recall
            precision_pct = metrics["precision"] * 100
            recall_pct = metrics["recall"] * 100
            st.markdown(f"Precision: **{precision_pct:.1f}%** ({metrics['total_correct']}/{metrics['total_attempted']})")
            st.markdown(progress_bar(precision_pct, "success" if precision_pct >= 80 else "warning"), unsafe_allow_html=True)
            st.markdown(f"Recall: **{recall_pct:.1f}%**")
            st.markdown(progress_bar(recall_pct, "success" if recall_pct >= 80 else "warning"), unsafe_allow_html=True)

            # Wrong-but-confident rate
            wbc = metrics["wrong_but_confident_rate"] * 100
            wbc_color = "success" if wbc < 5 else ("warning" if wbc < 15 else "critical")
            st.markdown(f"Wrong-but-Confident: **{wbc:.1f}%** ({metrics['wrong_but_confident_count']} cases)")
            st.markdown(
                f'<div style="color: var(--{wbc_color}); font-size: 12px;">'
                f'{"Low risk" if wbc < 5 else "Monitor" if wbc < 15 else "High risk - review needed"}'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Confidence calibration
            st.caption("Confidence Calibration")
            conf_correct = metrics.get("avg_confidence_correct")
            conf_incorrect = metrics.get("avg_confidence_incorrect")
            if conf_correct is not None:
                st.markdown(f"Avg confidence (correct): **{conf_correct:.3f}**")
            if conf_incorrect is not None:
                st.markdown(f"Avg confidence (incorrect): **{conf_incorrect:.3f}**")
            if conf_correct and conf_incorrect:
                gap = conf_correct - conf_incorrect
                calibration = "Well-calibrated" if gap > 0.1 else "Poorly calibrated"
                st.markdown(f"Gap: **{gap:+.3f}** ({calibration})")

    st.write("")

    # Overall similarity scores
    st.markdown("**Similarity Scores (Semantic)**")
    score_cols = st.columns(4)
    with score_cols[0]:
        st.markdown(metric_card(f"{evaluation_results.get('baseline_avg', 0):.3f}", "Baseline Avg", "accent"), unsafe_allow_html=True)
    with score_cols[1]:
        st.markdown(metric_card(f"{evaluation_results.get('baseline_median', 0):.3f}", "Baseline Median", "accent"), unsafe_allow_html=True)
    with score_cols[2]:
        llm_avg = evaluation_results.get("llm_avg")
        st.markdown(metric_card(f"{llm_avg:.3f}" if llm_avg else "N/A", "LLM Avg", "accent-2"), unsafe_allow_html=True)
    with score_cols[3]:
        llm_med = evaluation_results.get("llm_median")
        st.markdown(metric_card(f"{llm_med:.3f}" if llm_med else "N/A", "LLM Median", "accent-2"), unsafe_allow_html=True)

    with st.expander("Raw evaluation data"):
        # Show without per_scenario to keep it compact
        display_data = {k: v for k, v in evaluation_results.items() if k != "per_scenario"}
        st.json(display_data)

    with st.expander("Per-scenario breakdown"):
        st.json(evaluation_results.get("per_scenario", []))

elif evaluation_results:
    # Legacy format without quality_metrics
    with st.expander("View evaluation data", expanded=True):
        st.json(evaluation_results)
else:
    empty_state("No evaluation results. Run: python scripts/evaluate.py --write-json storage/evaluation_results.json", "")

st.write("")

# --- Time-to-Context ---
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Time to Actionable Context</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">How fast operators get RCA hypotheses</span>
    </div>
    """,
    unsafe_allow_html=True,
)

ttc = payload.get("time_to_context")
if ttc:
    col_manual, col_baseline, col_llm = st.columns(3)

    manual_min = ttc.get("manual_estimate_min", 25)
    baseline_ms = ttc.get("baseline_median_ms")
    llm_ms = ttc.get("llm_median_ms")
    improvement = ttc.get("improvement_factor")

    with col_manual:
        st.markdown(metric_card(f"{manual_min} min", "Manual Triage (est.)", "critical"), unsafe_allow_html=True)
    with col_baseline:
        if baseline_ms is not None:
            st.markdown(metric_card(f"{baseline_ms:.0f} ms", "Baseline RCA", "accent"), unsafe_allow_html=True)
        else:
            st.markdown(metric_card("N/A", "Baseline RCA", "ink"), unsafe_allow_html=True)
    with col_llm:
        if llm_ms is not None:
            st.markdown(metric_card(f"{llm_ms:.0f} ms", "LLM RCA", "accent-2"), unsafe_allow_html=True)
        else:
            st.markdown(metric_card("N/A", "LLM RCA", "ink"), unsafe_allow_html=True)

    if improvement:
        st.markdown(
            f'<div style="text-align: center; margin-top: 12px; padding: 12px; '
            f'background: var(--accent-glow); border-radius: 8px; border: 1px solid var(--accent);">'
            f'<span style="font-size: 24px; font-weight: 700; color: var(--accent);">'
            f'{improvement:.0f}x faster</span>'
            f'<span style="color: var(--ink-muted); margin-left: 8px;">than manual triage</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.caption("Manual estimate based on industry benchmarks for telecom NOC triage (15-30 min median).")
else:
    empty_state("No timing data. Generate incidents and run RCA to collect latency metrics.", "")

st.write("")

# --- Human Review KPIs ---
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Human Review Status</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">RCA hypothesis acceptance and review rates</span>
    </div>
    """,
    unsafe_allow_html=True,
)

review = payload.get("human_review")
if review:
    review_cols = st.columns(4)
    with review_cols[0]:
        st.markdown(metric_card(review.get("total_artifacts", 0), "Total RCAs", "ink"), unsafe_allow_html=True)
    with review_cols[1]:
        st.markdown(metric_card(review.get("pending_review", 0), "Pending Review", "accent-2"), unsafe_allow_html=True)
    with review_cols[2]:
        st.markdown(metric_card(review.get("accepted", 0), "Accepted", "accent"), unsafe_allow_html=True)
    with review_cols[3]:
        rate = review.get("acceptance_rate", 0)
        st.markdown(metric_card(f"{rate:.0%}" if isinstance(rate, float) else "N/A", "Acceptance Rate", "accent"), unsafe_allow_html=True)
else:
    empty_state("No review data. Review RCA hypotheses from the Incident Generator page.", "")
