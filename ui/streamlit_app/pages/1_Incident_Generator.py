"""TeleOps Network Incident Command - Main Dashboard.

A professional NOC-style interface for incident correlation, RCA generation,
and baseline vs LLM comparison.
"""

import os

import requests
import streamlit as st

from theme import (
    inject_theme,
    hero,
    card_start,
    card_end,
    card_header,
    divider,
    severity_badge,
    badge,
    nav_links,
    confidence_gauge,
    empty_state,
)

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
REQUEST_HEADERS = {"X-API-Key": API_TOKEN} if API_TOKEN else {}

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
    panel_class = "teleops-rca-llm" if is_llm else "teleops-rca-baseline"
    st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)

    st.markdown(f"### {title}")

    summary = payload.get("incident_summary", "N/A")
    model = payload.get("model", "unknown")
    generated_at = payload.get("generated_at", "")
    hypotheses = payload.get("hypotheses", [])
    confidence = payload.get("confidence_scores", {})
    evidence = payload.get("evidence", {})

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

    st.markdown("</div>", unsafe_allow_html=True)


# Page configuration
st.set_page_config(
    page_title="TeleOps Incident Generator",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject theme
inject_theme()

# Navigation
nav_links([
    ("Incident Generator", "/1_Incident_Generator", True),
    ("LLM Trace", "/3_LLM_Trace", False),
    ("Observability", "/2_Observability", False),
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
            resp = requests.post(f"{API_URL}/generate", json=payload, headers=REQUEST_HEADERS, timeout=30)
        if resp.status_code >= 400:
            st.error(f"Error: {resp.text}")
        else:
            st.success("Scenario generated successfully")
            with st.expander("Generation details"):
                st.json(resp.json())

# Main content - Incident Queue
card_start("accent")
card_header("Incident Queue", "Active incidents from synthetic runs")

# Fetch incidents
incidents_resp = requests.get(f"{API_URL}/incidents", headers=REQUEST_HEADERS, timeout=30)
if incidents_resp.status_code >= 400:
    st.error(incidents_resp.text)
    incidents = []
else:
    incidents = incidents_resp.json()

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

    filter_cols = st.columns([1, 1, 2])
    with filter_cols[0]:
        severity_filter = st.multiselect("Severity", options=severities, default=severities, label_visibility="collapsed")
    with filter_cols[1]:
        status_filter = st.multiselect("Status", options=statuses, default=statuses, label_visibility="collapsed")

    filtered_incidents = [
        item for item in incidents
        if (not severity_filter or item.get("severity") in severity_filter)
        and (not status_filter or item.get("status") in status_filter)
    ]

    if filtered_incidents:
        divider()

        # Incident selector row
        row = st.columns([1.5, 3, 1, 1.5])
        with row[0]:
            selected = st.selectbox(
                "Select Incident",
                options=filtered_incidents,
                format_func=lambda i: i["id"][:12] + "...",
                label_visibility="collapsed",
            )
        with row[1]:
            st.markdown(f"<p style='margin: 8px 0; color: var(--ink);'>{selected.get('summary', 'No summary')}</p>", unsafe_allow_html=True)
        with row[2]:
            st.markdown(severity_badge(selected.get("severity")), unsafe_allow_html=True)
        with row[3]:
            run_rca = st.button("Run RCA", type="primary", use_container_width=True)

        # Clear button
        st.markdown('<div class="teleops-btn-secondary" style="margin-top: 12px;">', unsafe_allow_html=True)
        if st.button("Clear All Incidents", use_container_width=True):
            resp = requests.post(f"{API_URL}/reset", headers=REQUEST_HEADERS, timeout=30)
            if resp.status_code >= 400:
                st.error(resp.text)
            else:
                st.success("All incidents cleared")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        if run_rca:
            with st.spinner("Running baseline RCA..."):
                baseline_resp = requests.post(
                    f"{API_URL}/rca/{selected['id']}/baseline",
                    headers=REQUEST_HEADERS,
                    timeout=30,
                )
            if baseline_resp.status_code >= 400:
                st.error(f"Baseline RCA failed: {baseline_resp.text}")
            else:
                st.session_state["baseline_rca"] = baseline_resp.json()

            with st.spinner("Running LLM RCA..."):
                llm_resp = requests.post(
                    f"{API_URL}/rca/{selected['id']}/llm",
                    headers=REQUEST_HEADERS,
                    timeout=60,
                )
            if llm_resp.status_code >= 400:
                st.error(f"LLM RCA failed: {llm_resp.text}")
            else:
                st.session_state["llm_rca"] = llm_resp.json()
    else:
        empty_state("No incidents match filters", "")
else:
    empty_state("No incidents yet. Generate a scenario to begin.", "")

card_end()

st.write("")

# Incident Context Card
if incidents and filtered_incidents:
    card_start()
    card_header("Incident Context", "Metadata and alert sample for selected incident")

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
    alert_resp = requests.get(
        f"{API_URL}/incidents/{selected['id']}/alerts",
        headers=REQUEST_HEADERS,
        timeout=30,
    )
    if alert_resp.status_code >= 400:
        st.error(alert_resp.text)
    else:
        alert_rows = [
            {
                "timestamp": a.get("timestamp", "")[:19],
                "host": a.get("host", ""),
                "service": a.get("service", ""),
                "severity": a.get("severity", ""),
                "type": a.get("alert_type", ""),
                "message": a.get("message", "")[:60] + "..." if len(a.get("message", "")) > 60 else a.get("message", ""),
            }
            for a in alert_resp.json()[:12]
        ]
        with st.expander(f"Alert sample (showing {len(alert_rows)} of {alert_count})"):
            st.dataframe(alert_rows, use_container_width=True, hide_index=True)

    card_end()

st.write("")

# RCA Output Card
card_start()
card_header("RCA Comparison", "Baseline (rule-based) vs LLM (AI-powered) analysis")

baseline_payload = st.session_state.get("baseline_rca")
llm_payload = st.session_state.get("llm_rca")

if not baseline_payload and not llm_payload:
    empty_state("Select an incident and click 'Run RCA' to compare baseline and LLM results.", "")
else:
    left, right = st.columns(2, gap="large")
    with left:
        if baseline_payload:
            render_rca_panel("Baseline RCA", baseline_payload, is_llm=False)
        else:
            empty_state("Baseline RCA not available", "")
    with right:
        if llm_payload:
            render_rca_panel("LLM RCA", llm_payload, is_llm=True)
        else:
            empty_state("LLM RCA not available", "")

card_end()
