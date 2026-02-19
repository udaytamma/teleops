"""TeleOps Network Incident Command - Main Dashboard.

A professional NOC-style interface for incident correlation, RCA generation,
and baseline vs LLM comparison.
"""

import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from theme import (
    inject_theme,
    hero,
    divider,
    severity_badge,
    badge,
    nav_links,
    confidence_gauge,
    empty_state,
    safe_api_call,
    safe_json,
    check_api_connection,
)

API_URL = os.getenv("TELEOPS_API_URL") or os.getenv("API_BASE_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
TENANT_ID = os.getenv("TELEOPS_TENANT_ID", "")
REQUEST_HEADERS = {}
if API_TOKEN:
    REQUEST_HEADERS["X-API-Key"] = API_TOKEN
if TENANT_ID:
    REQUEST_HEADERS["X-Tenant-Id"] = TENANT_ID

SCENARIOS = {
    "network_degradation": ("Network Degradation", "Packet loss and latency issues"),
    "dns_outage": ("DNS Outage", "DNS resolution failures"),
    "bgp_flap": ("BGP Flap", "Route instability and withdrawals"),
    "fiber_cut": ("Fiber Cut", "Physical transport failure"),
    "router_freeze": ("Router Freeze", "Control plane lockup"),
    "isp_peering_congestion": ("ISP Peering Congestion", "Inter-carrier bottleneck"),
    "ddos_edge": ("DDoS Attack", "Volumetric attack on edge"),
    "mpls_vpn_leak": ("MPLS/VPN Leak", "Label stack misconfiguration"),
    "cdn_cache_stampede": ("CDN Stampede", "Cache invalidation cascade"),
    "firewall_rule_misconfig": ("Firewall Misconfig", "Blocked ports/ACL error"),
    "database_latency_spike": ("Database Latency", "MSP app backend slowdown"),
}


def render_rca_panel(title: str, payload: dict, is_llm: bool = False) -> None:
    """Render an RCA result panel with hypotheses, confidence, and evidence."""
    summary = payload.get("incident_summary", "N/A")
    model = payload.get("model", "unknown")
    generated_at = payload.get("generated_at", "")
    hypotheses = payload.get("hypotheses", [])
    confidence = payload.get("confidence_scores", {})
    evidence = payload.get("evidence", {})

    # Panel header with title and badge
    if is_llm:
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
                <h4 style="margin: 0; font-size: 16px; font-weight: 600; color: var(--ink-strong);">{title}</h4>
                <span style="background: linear-gradient(135deg, #6C5CE7, #A29BFE); color: white; font-size: 10px; font-weight: 600; padding: 4px 10px; border-radius: 4px; letter-spacing: 0.05em;">AI-POWERED</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<h4 style='margin: 0 0 12px 0; font-size: 16px; font-weight: 600; color: var(--ink-strong);'>{title}</h4>", unsafe_allow_html=True)

    # Metadata badges
    st.markdown(
        f'{badge(model, "accent")} &nbsp; {badge(generated_at[:19] if generated_at else "N/A", "muted")}',
        unsafe_allow_html=True,
    )

    st.markdown("**Incident Summary**")
    st.markdown(f"<p style='color: var(--ink-muted); font-size: 14px;'>{summary}</p>", unsafe_allow_html=True)

    divider()

    st.markdown("**Hypotheses**")
    if hypotheses:
        for idx, item in enumerate(hypotheses, start=1):
            st.markdown(
                f"<div style='display: flex; gap: 12px; margin-bottom: 8px;'>"
                f"<span style='color: var(--accent); font-weight: 600; font-family: JetBrains Mono;'>{idx}.</span>"
                f"<span style='color: var(--ink);'>{item}</span></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown("<p style='color: var(--ink-dim);'>No hypotheses returned.</p>", unsafe_allow_html=True)

    divider()

    st.markdown("**Confidence Scores**")
    if confidence:
        for key, value in confidence.items():
            st.markdown(confidence_gauge(value, key), unsafe_allow_html=True)
    else:
        st.markdown("<p style='color: var(--ink-dim);'>No confidence data.</p>", unsafe_allow_html=True)

    divider()

    st.markdown("**Evidence**")
    if evidence:
        with st.expander("View evidence details", expanded=False):
            st.json(evidence)
    else:
        st.markdown("<p style='color: var(--ink-dim);'>No evidence recorded.</p>", unsafe_allow_html=True)


# Page configuration
st.set_page_config(
    page_title="TeleOps Incident Generator",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme
inject_theme()

# Check API connectivity before rendering the page
check_api_connection(API_URL, REQUEST_HEADERS)

# Navigation
nav_links([
    ("Incident Generator", "pages/1_Incident_Generator.py", True),
    ("LLM Trace", "pages/3_LLM_Trace.py", False),
    ("Observability", "pages/2_Observability.py", False),
], position="end")

st.write("")

# Hero section
hero(
    title="Network Incident Command",
    subtitle="Correlate NOC alerts into incidents, validate hypotheses, and compare baseline vs LLM-driven RCA with evidence.",
    chip_text="TELEOPS LIVE",
)

st.write("")

# Sidebar - Scenario Builder
with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 24px;">
            <h2 style="font-size: 18px; font-weight: 600; color: var(--ink-strong); margin: 0;">
                Scenario Builder
            </h2>
            <p style="font-size: 13px; color: var(--ink-dim); margin: 4px 0 0 0;">
                Generate synthetic incidents for testing
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    scenario = st.selectbox(
        "Incident Type",
        options=list(SCENARIOS.keys()),
        format_func=lambda key: SCENARIOS[key][0],
    )

    st.caption(SCENARIOS[scenario][1])

    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        alert_rate = st.number_input(
            "Alert/min",
            min_value=1,
            max_value=100,
            value=20,
            help="Alerts generated per minute",
        )
    with col2:
        duration = st.number_input(
            "Duration",
            min_value=1,
            max_value=60,
            value=10,
            help="Incident duration in minutes",
        )

    col3, col4 = st.columns(2)
    with col3:
        noise_rate = st.number_input(
            "Noise/min",
            min_value=0,
            max_value=50,
            value=5,
            help="Background noise alerts",
        )
    with col4:
        seed = st.number_input(
            "Seed",
            min_value=0,
            max_value=9999,
            value=42,
            help="Random seed for reproducibility",
        )

    st.markdown('<div style="height: 16px;"></div>', unsafe_allow_html=True)

    if st.button("Generate Scenario", use_container_width=True):
        payload = {
            "incident_type": scenario,
            "alert_rate_per_min": alert_rate,
            "duration_min": duration,
            "noise_rate_per_min": noise_rate,
            "seed": seed,
        }
        with st.spinner("Generating..."):
            resp, err = safe_api_call("POST", f"{API_URL}/generate", json=payload, headers=REQUEST_HEADERS, timeout=30)
        if err:
            st.error(err)
        else:
            st.success("Scenario generated successfully")
            data = safe_json(resp, {})
            if data:
                with st.expander("Generation details"):
                    st.json(data)

# Main content - Incident Queue
st.markdown(
    """
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
        <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Incident Queue</h3>
        <span style="font-size: 13px; color: var(--ink-dim);">Active incidents from synthetic runs</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Fetch incidents
incidents_resp, incidents_err = safe_api_call("GET", f"{API_URL}/incidents", headers=REQUEST_HEADERS, timeout=30)
if incidents_err:
    st.error(incidents_err)
    incidents = []
else:
    incidents = safe_json(incidents_resp, [])
    if not isinstance(incidents, list):
        incidents = []

if incidents:
    # Stats bar
    critical_count = sum(1 for i in incidents if (i.get("severity") or "").lower() == "critical")
    high_count = sum(1 for i in incidents if (i.get("severity") or "").lower() == "high")
    open_count = sum(1 for i in incidents if (i.get("status") or "").lower() != "resolved")

    st.markdown(
        f"""
        <div class="teleops-stats-bar">
            <div class="teleops-stat">
                <span class="teleops-stat-value" style="color: var(--critical);">{critical_count}</span>
                <span class="teleops-stat-label">Critical</span>
            </div>
            <div class="teleops-stat">
                <span class="teleops-stat-value" style="color: var(--accent-2);">{high_count}</span>
                <span class="teleops-stat-label">High</span>
            </div>
            <div class="teleops-stat">
                <span class="teleops-stat-value">{open_count}</span>
                <span class="teleops-stat-label">Open</span>
            </div>
            <div class="teleops-stat">
                <span class="teleops-stat-value" style="color: var(--accent);">{len(incidents)}</span>
                <span class="teleops-stat-label">Total</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Filters
    severities = sorted({(item.get("severity") or "unknown") for item in incidents})
    statuses = sorted({(item.get("status") or "unknown") for item in incidents})

    filter_cols = st.columns([1, 1, 2, 1])
    with filter_cols[0]:
        severity_filter = st.multiselect("Severity", options=severities, default=severities)
    with filter_cols[1]:
        status_filter = st.multiselect("Status", options=statuses, default=statuses)
    with filter_cols[3]:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Clear All", help="Remove all incidents from the queue"):
            resp, err = safe_api_call("POST", f"{API_URL}/reset", headers=REQUEST_HEADERS, timeout=30)
            if err:
                st.error(err)
            else:
                st.rerun()

    filtered_incidents = [
        item for item in incidents
        if (not severity_filter or item.get("severity") in severity_filter)
        and (not status_filter or item.get("status") in status_filter)
    ]

    if filtered_incidents:
        divider()

        # Incident selector row
        row = st.columns([3, 2, 0.8, 1.2])
        with row[0]:
            selected = st.selectbox(
                "Select Incident",
                options=filtered_incidents,
                format_func=lambda i: f"{i['id']} - {i.get('summary', 'No summary')[:30]}",
                label_visibility="collapsed",
            )
        with row[1]:
            st.markdown(f"<p style='margin: 8px 0; color: var(--ink-muted); font-size: 13px;'>{selected.get('summary', '')[:50]}</p>", unsafe_allow_html=True)
        with row[2]:
            st.markdown(severity_badge(selected.get("severity")), unsafe_allow_html=True)
        with row[3]:
            run_rca = st.button("Run RCA", type="primary", use_container_width=True)

        if run_rca:
            with st.spinner("Running baseline RCA..."):
                baseline_resp, baseline_err = safe_api_call(
                    "POST",
                    f"{API_URL}/rca/{selected['id']}/baseline",
                    headers=REQUEST_HEADERS,
                    timeout=60,
                )
            if baseline_err:
                st.error(f"Baseline RCA failed: {baseline_err}")
            else:
                st.session_state["baseline_rca"] = safe_json(baseline_resp, {})

            with st.spinner("Running LLM RCA (may take up to 2 minutes)..."):
                llm_resp, llm_err = safe_api_call(
                    "POST",
                    f"{API_URL}/rca/{selected['id']}/llm",
                    headers=REQUEST_HEADERS,
                    timeout=180,
                )
            if llm_err:
                st.error(f"LLM RCA failed: {llm_err}")
            else:
                st.session_state["llm_rca"] = safe_json(llm_resp, {})
    else:
        empty_state("No incidents match filters", "")
else:
    empty_state("No incidents yet. Generate a scenario to begin.", "")

st.write("")

# Incident Context
if incidents and filtered_incidents:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Incident Context</h3>
            <span style="font-size: 13px; color: var(--ink-dim);">Metadata and alert sample</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    context_cols = st.columns(4)
    with context_cols[0]:
        st.markdown("**Status**")
        status = selected.get("status", "unknown")
        status_color = "var(--success)" if status.lower() == "resolved" else "var(--info)"
        st.markdown(f"<span style='color: {status_color}; font-weight: 500;'>{status}</span>", unsafe_allow_html=True)
    with context_cols[1]:
        st.markdown("**Impact**")
        st.markdown(f"<span style='color: var(--ink-muted);'>{selected.get('impact_scope', 'unknown')}</span>", unsafe_allow_html=True)
    with context_cols[2]:
        st.markdown("**Owner**")
        st.markdown(f"<span style='color: var(--ink-muted);'>{selected.get('owner') or 'Unassigned'}</span>", unsafe_allow_html=True)
    with context_cols[3]:
        st.markdown("**Alerts**")
        alert_count = len(selected.get("related_alert_ids", []))
        st.markdown(f"<span style='color: var(--accent); font-family: JetBrains Mono; font-weight: 600;'>{alert_count}</span>", unsafe_allow_html=True)

    # Fetch and display alerts
    alert_resp, alert_err = safe_api_call(
        "GET",
        f"{API_URL}/incidents/{selected['id']}/alerts",
        headers=REQUEST_HEADERS,
        timeout=30,
    )
    if alert_err:
        st.error(alert_err)
    else:
        alerts_data = safe_json(alert_resp, [])
        if not isinstance(alerts_data, list):
            alerts_data = []
        alert_rows = [
            {
                "timestamp": a.get("timestamp", "")[:19],
                "host": a.get("host", ""),
                "service": a.get("service", ""),
                "severity": a.get("severity", ""),
                "type": a.get("alert_type", ""),
                "message": a.get("message", "")[:60] + "..." if len(a.get("message", "")) > 60 else a.get("message", ""),
            }
            for a in alerts_data[:12]
        ]
        with st.expander(f"Alert sample (showing {len(alert_rows)} of {alert_count})"):
            st.dataframe(alert_rows, use_container_width=True, hide_index=True)

st.write("")

# RCA Output Section
baseline_payload = st.session_state.get("baseline_rca")
llm_payload = st.session_state.get("llm_rca")

if baseline_payload or llm_payload:
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">RCA Comparison</h3>
            <span style="font-size: 13px; color: var(--ink-dim);">Baseline (rule-based) vs LLM (AI-powered)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns(2, gap="large")
    with left:
        if baseline_payload:
            render_rca_panel("Baseline RCA", baseline_payload, is_llm=False)
        else:
            st.markdown("<p style='color: var(--ink-dim); padding: 20px; text-align: center;'>Baseline RCA not available</p>", unsafe_allow_html=True)
    with right:
        if llm_payload:
            render_rca_panel("LLM RCA", llm_payload, is_llm=True)
        else:
            st.markdown("<p style='color: var(--ink-dim); padding: 20px; text-align: center;'>LLM RCA not available</p>", unsafe_allow_html=True)

    # --- Human Review Section ---
    divider()
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
            <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: var(--ink-strong);">Hypothesis Review</h3>
            <span style="font-size: 13px; color: var(--ink-dim);">Accept or reject RCA hypotheses (human-in-the-loop gate)</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Determine which artifacts to review
    reviewable = []
    if baseline_payload and baseline_payload.get("artifact_id"):
        reviewable.append(("Baseline", baseline_payload))
    if llm_payload and llm_payload.get("artifact_id"):
        reviewable.append(("LLM", llm_payload))

    if reviewable:
        reviewer_name = st.text_input("Reviewer Name", value="", placeholder="Enter your name or operator ID")
        review_notes = st.text_area("Notes (optional)", value="", placeholder="Observations, corrections, or context", height=80)

        review_cols = st.columns(len(reviewable))
        for idx, (label, rca_payload) in enumerate(reviewable):
            with review_cols[idx]:
                artifact_id = rca_payload["artifact_id"]
                hypothesis = rca_payload.get("hypotheses", ["N/A"])[0][:60]
                st.markdown(f"**{label}:** {hypothesis}...")

                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button(f"Accept", key=f"accept_{label}", use_container_width=True):
                        if not reviewer_name.strip():
                            st.error("Reviewer name required")
                        else:
                            resp, err = safe_api_call(
                                "POST",
                                f"{API_URL}/rca/{artifact_id}/review",
                                json={"decision": "accepted", "reviewed_by": reviewer_name.strip(), "notes": review_notes or None},
                                headers=REQUEST_HEADERS,
                                timeout=10,
                            )
                            if err:
                                st.error(f"Review failed: {err}")
                            else:
                                st.success(f"{label} hypothesis accepted")
                with btn_col2:
                    if st.button(f"Reject", key=f"reject_{label}", use_container_width=True):
                        if not reviewer_name.strip():
                            st.error("Reviewer name required")
                        else:
                            resp, err = safe_api_call(
                                "POST",
                                f"{API_URL}/rca/{artifact_id}/review",
                                json={"decision": "rejected", "reviewed_by": reviewer_name.strip(), "notes": review_notes or None},
                                headers=REQUEST_HEADERS,
                                timeout=10,
                            )
                            if err:
                                st.error(f"Review failed: {err}")
                            else:
                                st.warning(f"{label} hypothesis rejected")
    else:
        st.caption("Run RCA above to generate hypotheses for review.")
