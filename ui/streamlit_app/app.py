"""Streamlit UI for TeleOps."""

import os

import requests
import streamlit as st

API_URL = os.getenv("TELEOPS_API_URL", "http://localhost:8000")
API_TOKEN = os.getenv("TELEOPS_API_TOKEN", "")
REQUEST_HEADERS = {"X-API-Key": API_TOKEN} if API_TOKEN else {}


def _confidence_color(value: float) -> str:
    if value >= 0.8:
        return "#2E7D32"
    if value >= 0.6:
        return "#558B2F"
    if value >= 0.4:
        return "#F9A825"
    return "#C62828"


def _badge(text: str, bg: str) -> str:
    return (
        f"<span style=\"display:inline-block;padding:2px 8px;border-radius:999px;"
        f"background:{bg};color:white;font-size:12px;\">{text}</span>"
    )


def render_rca(title: str, payload: dict) -> None:
    st.markdown(f"**{title}**")
    st.caption("Structured RCA output with hypotheses, evidence, and confidence.")

    summary = payload.get("incident_summary", "N/A")
    model = payload.get("model", "unknown")
    generated_at = payload.get("generated_at", "unknown")
    hypotheses = payload.get("hypotheses", [])
    confidence = payload.get("confidence_scores", {})
    evidence = payload.get("evidence", {})

    header = st.container(border=True)
    with header:
        st.markdown("**Incident Summary**")
        st.write(summary)
        st.markdown("**Run Metadata**")
        st.markdown(
            f"{_badge('Model', '#3949AB')} &nbsp; <b>{model}</b>",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"{_badge('Generated', '#546E7A')} &nbsp; <b>{generated_at}</b>",
            unsafe_allow_html=True,
        )

    st.markdown("**Hypotheses**")
    if hypotheses:
        for idx, item in enumerate(hypotheses, start=1):
            st.write(f"{idx}. {item}")
    else:
        st.write("No hypotheses returned.")

    st.markdown("**Confidence**")
    if confidence:
        for key, value in confidence.items():
            level = min(max(float(value), 0.0), 1.0)
            color = _confidence_color(level)
            arc = 157 * level
            gauge = f"""
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap;">
              <svg width="120" height="70" viewBox="0 0 120 70">
                <path d="M10,60 A50,50 0 0,1 110,60" stroke="#1C2A33" stroke-width="12" fill="none"/>
                <path d="M10,60 A50,50 0 0,1 110,60" stroke="{color}" stroke-width="12" fill="none"
                  stroke-dasharray="{arc} 999"/>
                <circle cx="60" cy="60" r="6" fill="{color}"/>
                <text x="60" y="50" text-anchor="middle" font-size="16" fill="#E6F1F7">{level:.2f}</text>
              </svg>
              <div style="color:#E6F1F7;font-size:15px;line-height:1.3;max-width:420px;">{key}</div>
            </div>
            """
            st.markdown(gauge, unsafe_allow_html=True)
    else:
        st.write("No confidence scores returned.")

    st.markdown("**Evidence**")
    if evidence:
        st.json(evidence)
    else:
        st.write("No evidence returned.")


st.set_page_config(page_title="TeleOps Console", layout="wide")

SCENARIOS = {
    "network_degradation": "Network degradation (packet loss/latency)",
    "dns_outage": "DNS outage",
    "bgp_flap": "BGP flap",
    "fiber_cut": "Fiber cut",
    "router_freeze": "Router freeze",
    "isp_peering_congestion": "ISP peering congestion",
    "ddos_edge": "DDoS attack on edge",
    "mpls_vpn_leak": "MPLS/L3VPN leak",
    "cdn_cache_stampede": "CDN cache stampede",
    "firewall_rule_misconfig": "Firewall rule misconfig / blocked port",
    "database_latency_spike": "Database latency spike (MSP hosted apps)",
}

top_left, top_right = st.columns([5, 1])
with top_right:
    st.markdown(
        "<div style='text-align:right;'>"
        "<a href='LLM_Response' style='color:#9BB0BF;text-decoration:none;font-size:14px;'>"
        "View LLM Response</a>"
        " &nbsp; | &nbsp; "
        "<a href='Observability' style='color:#9BB0BF;text-decoration:none;font-size:14px;'>"
        "Observability</a></div>",
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');
    :root {
        --bg: #0B1318;
        --panel: #111B22;
        --panel-2: #0F1A20;
        --ink: #E6F1F7;
        --muted: #9BB0BF;
        --accent: #21B6A8;
        --accent-2: #D88C2B;
        --border: #1C2A33;
        --chip: #0B2A33;
        --ink-strong: #F4FBFF;
    }
    html, body, .main { font-size: 17px; font-family: 'Space Grotesk', sans-serif; }
    .main { background: var(--bg); color: var(--ink); }
    .teleops-hero {
        padding: 20px 24px;
        border-radius: 16px;
        background:
            radial-gradient(circle at 18% 15%, rgba(33,182,168,0.22), transparent 45%),
            radial-gradient(circle at 82% 25%, rgba(216,140,43,0.22), transparent 40%),
            linear-gradient(135deg, #0F1A20 0%, #101B24 100%);
        border: 1px solid var(--border);
        position: relative;
        overflow: hidden;
    }
    .teleops-hero::after {
        content: "";
        position: absolute;
        right: -40px;
        top: -40px;
        width: 180px;
        height: 180px;
        border: 1px dashed rgba(39,179,158,0.35);
        border-radius: 50%;
    }
    .teleops-hero h1 {
        margin: 0;
        font-size: 30px;
        color: var(--ink-strong);
        letter-spacing: 0.4px;
    }
    .teleops-hero p {
        margin: 6px 0 0 0;
        color: var(--muted);
    }
    .teleops-chip {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        background: var(--chip);
        color: #A7F3E6;
        border: 1px solid rgba(39,179,158,0.35);
        letter-spacing: 0.4px;
        font-family: 'IBM Plex Mono', monospace;
    }
    .teleops-card {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
    }
    .teleops-title {
        font-size: 17px;
        font-weight: 600;
        margin-bottom: 6px;
        color: var(--ink-strong);
    }
    .teleops-muted {
        color: var(--muted);
        font-size: 12px;
    }
    .teleops-divider {
        height: 1px;
        background: var(--border);
        margin: 12px 0;
    }
    .teleops-severity-critical {
        color: #FF6B6B;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .teleops-severity {
        color: #A8C7D8;
        font-size: 15px;
        font-weight: 600;
        letter-spacing: 0.2px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #27B39E 0%, #1E8A7A 100%);
        color: #0B1318;
        border: none;
        padding: 10px 18px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 14px;
        width: 100%;
    }
    .teleops-clear-btn button {
        background: transparent !important;
        border: 1px solid #1C2A33 !important;
        color: #9BB0BF !important;
        font-weight: 500 !important;
        padding: 6px 12px !important;
        width: auto !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="teleops-hero">
        <span class="teleops-chip">TELCO OPS • LIVE RCA</span>
        <h1>Network Incident Command</h1>
        <p>Correlate NOC alerts into incidents, validate hypotheses, and compare
        rules vs LLM-driven RCA with evidence.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

with st.sidebar:
    st.header("Scenario Builder")
    st.caption("Create synthetic alerts and incidents for repeatable testing.")
    scenario = st.selectbox(
        "Scenario type",
        options=list(SCENARIOS.keys()),
        format_func=lambda key: SCENARIOS[key],
    )
    st.caption(f"Selected: {SCENARIOS[scenario]}")
    alert_rate = st.number_input(
        "Alert rate per minute",
        min_value=1,
        max_value=100,
        value=20,
        help="Number of incident-related alerts generated per minute.",
    )
    duration = st.number_input(
        "Duration (minutes)",
        min_value=1,
        max_value=60,
        value=10,
        help="Total length of the simulated incident window.",
    )
    noise_rate = st.number_input(
        "Noise alerts per minute",
        min_value=0,
        max_value=50,
        value=5,
        help="Number of unrelated alerts per minute to simulate background noise.",
    )
    seed = st.number_input(
        "Seed",
        min_value=0,
        max_value=9999,
        value=42,
        help="Deterministic seed for repeatable scenarios.",
    )

    if st.button("Generate Scenario", help="Generate alerts, correlate incidents, and store ground truth."):
        payload = {
            "incident_type": scenario,
            "alert_rate_per_min": alert_rate,
            "duration_min": duration,
            "noise_rate_per_min": noise_rate,
            "seed": seed,
        }
        resp = requests.post(f"{API_URL}/generate", json=payload, headers=REQUEST_HEADERS, timeout=30)
        if resp.status_code >= 400:
            st.error(resp.text)
        else:
            st.success("Scenario generated")
            with st.expander("Show generation details", expanded=False):
                st.json(resp.json())

st.markdown('<div class="teleops-card">', unsafe_allow_html=True)
st.markdown('<div class="teleops-title">Incident Queue</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="teleops-muted">Latest correlated incidents from synthetic runs.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)

incidents_resp = requests.get(f"{API_URL}/incidents", headers=REQUEST_HEADERS, timeout=30)
if incidents_resp.status_code >= 400:
    st.error(incidents_resp.text)
    incidents = []
else:
    incidents = incidents_resp.json()

if incidents:
    severities = sorted({(item.get("severity") or "unknown") for item in incidents})
    statuses = sorted({(item.get("status") or "unknown") for item in incidents})
else:
    severities = []
    statuses = []

filters = st.container()
with filters:
    filter_cols = st.columns(2)
    with filter_cols[0]:
        severity_filter = st.multiselect("Severity filter", options=severities, default=severities)
    with filter_cols[1]:
        status_filter = st.multiselect("Status filter", options=statuses, default=statuses)

filtered_incidents = [
    item
    for item in incidents
    if (not severity_filter or item.get("severity") in severity_filter)
    and (not status_filter or item.get("status") in status_filter)
]

if not filtered_incidents:
    st.info("No incidents yet. Generate a scenario.")
else:
    row = st.columns([1.2, 2.2, 0.8, 1.1])
    with row[0]:
        selected = st.selectbox(
            "Incident",
            options=filtered_incidents,
            format_func=lambda i: i["id"],
            label_visibility="collapsed",
        )
        st.markdown("<div class='teleops-clear-btn'>", unsafe_allow_html=True)
        if st.button("Clear Incidents", help="Delete all alerts, incidents, and RCA artifacts."):
            resp = requests.post(f"{API_URL}/reset", headers=REQUEST_HEADERS, timeout=30)
            if resp.status_code >= 400:
                st.error(resp.text)
            else:
                st.success("All incidents cleared.")
        st.markdown("</div>", unsafe_allow_html=True)
    with row[1]:
        st.markdown("**Summary**")
        st.write(selected.get("summary"))
    with row[2]:
        st.markdown("**Severity**")
        severity = (selected.get("severity") or "").lower()
        severity_class = "teleops-severity-critical" if severity == "critical" else "teleops-severity"
        st.markdown(
            f"<span class='{severity_class}'>{selected.get('severity')}</span>",
            unsafe_allow_html=True,
        )
    with row[3]:
        st.markdown("**Actions**")
        if st.button(
            "Run RCA",
            help="Run baseline and LLM RCA for side-by-side comparison.",
            type="primary",
        ):
            baseline_resp = requests.post(
                f"{API_URL}/rca/{selected['id']}/baseline",
                headers=REQUEST_HEADERS,
                timeout=30,
            )
            if baseline_resp.status_code >= 400:
                st.error(f"Baseline RCA failed: {baseline_resp.text}")
            else:
                st.session_state["baseline_rca"] = baseline_resp.json()

            llm_resp = requests.post(
                f"{API_URL}/rca/{selected['id']}/llm",
                headers=REQUEST_HEADERS,
                timeout=60,
            )
            if llm_resp.status_code >= 400:
                st.error(f"LLM RCA failed: {llm_resp.text}")
            else:
                st.session_state["llm_rca"] = llm_resp.json()

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="teleops-card">', unsafe_allow_html=True)
st.markdown('<div class="teleops-title">Incident Context</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="teleops-muted">Key metadata and alert sample for the selected incident.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)

if filtered_incidents:
    context_cols = st.columns(4)
    with context_cols[0]:
        st.markdown("**Status**")
        st.write(selected.get("status", "unknown"))
    with context_cols[1]:
        st.markdown("**Impact**")
        st.write(selected.get("impact_scope", "unknown"))
    with context_cols[2]:
        st.markdown("**Owner**")
        st.write(selected.get("owner") or "unassigned")
    with context_cols[3]:
        st.markdown("**Alerts**")
        st.write(len(selected.get("related_alert_ids", [])))

    alert_resp = requests.get(
        f"{API_URL}/incidents/{selected['id']}/alerts",
        headers=REQUEST_HEADERS,
        timeout=30,
    )
    if alert_resp.status_code >= 400:
        st.error(alert_resp.text)
    else:
        alert_rows = []
        for alert in alert_resp.json():
            alert_rows.append(
                {
                    "timestamp": alert.get("timestamp"),
                    "host": alert.get("host"),
                    "service": alert.get("service"),
                    "severity": alert.get("severity"),
                    "type": alert.get("alert_type"),
                    "message": alert.get("message"),
                }
            )
        with st.expander("Alert sample (first 12)", expanded=False):
            st.dataframe(alert_rows[:12], use_container_width=True)

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown('<div class="teleops-card">', unsafe_allow_html=True)
st.markdown('<div class="teleops-title">RCA Output</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="teleops-muted">Compare baseline vs LLM results with confidence and evidence.</div>',
    unsafe_allow_html=True,
)
st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)

baseline_payload = st.session_state.get("baseline_rca")
llm_payload = st.session_state.get("llm_rca")

if not baseline_payload and not llm_payload:
    st.info("Run RCA to view baseline and LLM results.")
else:
    left, right = st.columns(2)
    with left:
        if baseline_payload:
            render_rca("Baseline RCA", baseline_payload)
    with right:
        if llm_payload:
            render_rca("LLM RCA", llm_payload)

st.markdown("</div>", unsafe_allow_html=True)
