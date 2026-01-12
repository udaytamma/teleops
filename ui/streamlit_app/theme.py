"""Shared theme and styling for TeleOps Streamlit UI.

This module provides consistent styling across all pages with a NOC-inspired
dark theme, custom components, and utility functions.
"""

# CSS Variables and Theme Configuration
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    /* Core palette */
    --bg-deep: #070B0E;
    --bg: #0B1318;
    --bg-elevated: #101920;
    --panel: #131D24;
    --panel-hover: #182530;

    /* Text */
    --ink: #E8F4FC;
    --ink-strong: #FFFFFF;
    --ink-muted: #8BA3B5;
    --ink-dim: #5A7384;

    /* Accents */
    --accent: #00D4AA;
    --accent-glow: rgba(0, 212, 170, 0.15);
    --accent-2: #FF9F43;
    --accent-2-glow: rgba(255, 159, 67, 0.15);
    --accent-3: #6C5CE7;

    /* Semantic */
    --critical: #FF6B6B;
    --critical-glow: rgba(255, 107, 107, 0.2);
    --warning: #FECA57;
    --success: #1DD1A1;
    --info: #54A0FF;

    /* Borders & Shadows */
    --border: #1E2D38;
    --border-hover: #2A4050;
    --shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    --shadow-glow: 0 0 40px rgba(0, 212, 170, 0.1);
}

/* Base styles */
html, body, [data-testid="stAppViewContainer"], .main {
    background: var(--bg-deep) !important;
    color: var(--ink) !important;
    font-family: 'Outfit', -apple-system, sans-serif !important;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--ink-strong) !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
}

code, pre, .stCode {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--panel) 0%, var(--bg) 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: var(--ink) !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label {
    color: var(--ink-muted) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

/* Form elements */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
}

.stSelectbox > div > div:hover,
.stNumberInput > div > div > input:hover {
    border-color: var(--border-hover) !important;
}

.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px var(--accent-glow) !important;
}

/* Primary button */
.stButton > button[kind="primary"],
.stButton > button {
    background: linear-gradient(135deg, var(--accent) 0%, #00B894 100%) !important;
    color: var(--bg-deep) !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(0, 212, 170, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(0, 212, 170, 0.4) !important;
}

/* Secondary/ghost button */
.teleops-btn-secondary button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--ink-muted) !important;
    box-shadow: none !important;
}

.teleops-btn-secondary button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    background: var(--accent-glow) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 16px !important;
}

[data-testid="stMetric"] label {
    color: var(--ink-muted) !important;
    font-size: 12px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--ink-strong) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 28px !important;
    font-weight: 600 !important;
}

/* Dataframe */
.stDataFrame {
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

.stDataFrame [data-testid="stDataFrameResizable"] {
    background: var(--panel) !important;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--ink) !important;
}

.streamlit-expanderContent {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    border-radius: 0 0 8px 8px !important;
}

/* JSON viewer */
.stJson {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 12px !important;
}

/* Divider */
hr {
    border-color: var(--border) !important;
    margin: 24px 0 !important;
}

/* Info/Warning/Error boxes */
.stAlert {
    border-radius: 8px !important;
    border: none !important;
}

/* Multiselect */
.stMultiSelect > div > div {
    background: var(--bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

.stMultiSelect [data-baseweb="tag"] {
    background: var(--accent-glow) !important;
    border: 1px solid var(--accent) !important;
    color: var(--accent) !important;
}

/* Caption */
.stCaption {
    color: var(--ink-dim) !important;
}

/* === CUSTOM COMPONENT CLASSES === */

/* Hero section */
.teleops-hero {
    padding: 28px 32px;
    border-radius: 20px;
    background:
        radial-gradient(ellipse at 20% 0%, rgba(0, 212, 170, 0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 100%, rgba(255, 159, 67, 0.08) 0%, transparent 40%),
        linear-gradient(160deg, var(--panel) 0%, var(--bg) 100%);
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
}

.teleops-hero::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent), transparent);
    opacity: 0.5;
}

.teleops-hero h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--ink-strong) 0%, var(--ink) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.teleops-hero p {
    margin: 8px 0 0 0;
    color: var(--ink-muted);
    font-size: 15px;
    line-height: 1.5;
}

/* Chip/Tag */
.teleops-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-family: 'JetBrains Mono', monospace;
    background: linear-gradient(135deg, var(--accent-glow) 0%, transparent 100%);
    color: var(--accent);
    border: 1px solid rgba(0, 212, 170, 0.3);
    margin-bottom: 12px;
}

.teleops-chip::before {
    content: "";
    width: 6px;
    height: 6px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 var(--accent); }
    50% { opacity: 0.7; box-shadow: 0 0 0 4px transparent; }
}

/* Card */
.teleops-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: var(--shadow);
    transition: all 0.2s ease;
}

.teleops-card:hover {
    border-color: var(--border-hover);
}

.teleops-card-accent {
    border-left: 3px solid var(--accent);
    background: linear-gradient(90deg, var(--accent-glow) 0%, var(--panel) 30%);
}

.teleops-card-warning {
    border-left: 3px solid var(--accent-2);
    background: linear-gradient(90deg, var(--accent-2-glow) 0%, var(--panel) 30%);
}

.teleops-card-critical {
    border-left: 3px solid var(--critical);
    background: linear-gradient(90deg, var(--critical-glow) 0%, var(--panel) 30%);
}

/* Card header */
.teleops-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
}

.teleops-card-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--ink-strong);
    margin: 0;
}

.teleops-card-subtitle {
    font-size: 13px;
    color: var(--ink-dim);
    margin: 4px 0 0 0;
}

/* Badge */
.teleops-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
    font-family: 'JetBrains Mono', monospace;
}

.teleops-badge-accent {
    background: var(--accent-glow);
    color: var(--accent);
    border: 1px solid rgba(0, 212, 170, 0.3);
}

.teleops-badge-muted {
    background: rgba(139, 163, 181, 0.1);
    color: var(--ink-muted);
    border: 1px solid var(--border);
}

/* Severity indicators */
.teleops-severity {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 14px;
}

.teleops-severity-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.teleops-severity-critical .teleops-severity-dot {
    background: var(--critical);
    box-shadow: 0 0 12px var(--critical);
    animation: critical-pulse 1.5s infinite;
}

@keyframes critical-pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.6); }
    50% { box-shadow: 0 0 0 8px rgba(255, 107, 107, 0); }
}

.teleops-severity-critical { color: var(--critical); }
.teleops-severity-high { color: var(--accent-2); }
.teleops-severity-medium { color: var(--warning); }
.teleops-severity-low { color: var(--success); }

/* Stats bar */
.teleops-stats-bar {
    display: flex;
    gap: 24px;
    padding: 16px 20px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 20px;
}

.teleops-stat {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.teleops-stat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 24px;
    font-weight: 600;
    color: var(--ink-strong);
}

.teleops-stat-label {
    font-size: 11px;
    color: var(--ink-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* Navigation links */
.teleops-nav {
    display: flex;
    gap: 16px;
    justify-content: flex-end;
}

.teleops-nav a {
    color: var(--ink-muted);
    text-decoration: none;
    font-size: 13px;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: 6px;
    transition: all 0.2s ease;
}

.teleops-nav a:hover {
    color: var(--accent);
    background: var(--accent-glow);
}

.teleops-nav a.active {
    color: var(--accent);
    background: var(--accent-glow);
}

/* Divider */
.teleops-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 16px 0;
}

/* RCA comparison columns */
.teleops-rca-baseline {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
}

.teleops-rca-llm {
    background: linear-gradient(135deg, var(--panel) 0%, rgba(108, 92, 231, 0.05) 100%);
    border: 1px solid rgba(108, 92, 231, 0.3);
    border-radius: 16px;
    padding: 20px;
    position: relative;
}

.teleops-rca-llm::before {
    content: "AI-POWERED";
    position: absolute;
    top: -10px;
    right: 20px;
    background: linear-gradient(135deg, #6C5CE7, #A29BFE);
    color: white;
    font-size: 10px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 4px;
    letter-spacing: 0.05em;
}

/* Progress/gauge styling */
.teleops-gauge-container {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 0;
    border-bottom: 1px solid var(--border);
}

.teleops-gauge-container:last-child {
    border-bottom: none;
}

/* Page header with breadcrumb */
.teleops-page-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    margin-bottom: 20px;
}

.teleops-breadcrumb {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--ink-dim);
}

.teleops-breadcrumb a {
    color: var(--ink-muted);
    text-decoration: none;
}

.teleops-breadcrumb a:hover {
    color: var(--accent);
}

/* Metric cards for observability */
.teleops-metric-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    transition: all 0.2s ease;
}

.teleops-metric-card:hover {
    border-color: var(--accent);
    box-shadow: var(--shadow-glow);
}

.teleops-metric-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 36px;
    font-weight: 700;
    color: var(--accent);
    line-height: 1;
}

.teleops-metric-label {
    font-size: 12px;
    color: var(--ink-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 8px;
}

/* Progress bar for test results */
.teleops-progress {
    height: 8px;
    background: var(--bg);
    border-radius: 4px;
    overflow: hidden;
    margin: 8px 0;
}

.teleops-progress-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
}

.teleops-progress-success {
    background: linear-gradient(90deg, var(--success), #10B981);
}

.teleops-progress-warning {
    background: linear-gradient(90deg, var(--warning), #F59E0B);
}

/* Code block styling */
.teleops-code {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--ink);
    overflow-x: auto;
    line-height: 1.6;
}

/* Timestamp styling */
.teleops-timestamp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--ink-dim);
}

/* Empty state */
.teleops-empty {
    text-align: center;
    padding: 48px 24px;
    color: var(--ink-dim);
}

.teleops-empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
    opacity: 0.5;
}

/* Loading state */
.teleops-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 24px;
    color: var(--ink-muted);
}

.teleops-spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}
</style>
"""


def inject_theme() -> None:
    """Inject the TeleOps theme CSS into the Streamlit page."""
    import streamlit as st
    st.markdown(THEME_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str, chip_text: str = "TELEOPS") -> None:
    """Render the hero/header section."""
    import streamlit as st
    st.markdown(
        f"""
        <div class="teleops-hero">
            <span class="teleops-chip">{chip_text}</span>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start(variant: str = "") -> None:
    """Start a card container. Variants: '', 'accent', 'warning', 'critical'."""
    import streamlit as st
    cls = f"teleops-card teleops-card-{variant}" if variant else "teleops-card"
    st.markdown(f'<div class="{cls}">', unsafe_allow_html=True)


def card_end() -> None:
    """End a card container."""
    import streamlit as st
    st.markdown("</div>", unsafe_allow_html=True)


def card_header(title: str, subtitle: str = "") -> None:
    """Render a card header with title and optional subtitle."""
    import streamlit as st
    subtitle_html = f'<p class="teleops-card-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div class="teleops-card-header">
            <div>
                <h3 class="teleops-card-title">{title}</h3>
                {subtitle_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def divider() -> None:
    """Render a styled divider."""
    import streamlit as st
    st.markdown('<div class="teleops-divider"></div>', unsafe_allow_html=True)


def severity_badge(severity: str) -> str:
    """Return HTML for a severity indicator."""
    sev_lower = (severity or "unknown").lower()
    return f"""
    <span class="teleops-severity teleops-severity-{sev_lower}">
        <span class="teleops-severity-dot"></span>
        {severity.upper() if severity else "UNKNOWN"}
    </span>
    """


def badge(text: str, variant: str = "accent") -> str:
    """Return HTML for a badge. Variants: 'accent', 'muted'."""
    return f'<span class="teleops-badge teleops-badge-{variant}">{text}</span>'


def nav_links(links: list[tuple[str, str, bool]], position: str = "right") -> None:
    """Render navigation links. Each tuple is (label, url, is_active)."""
    import streamlit as st
    links_html = "".join(
        f'<a href="{url}" class="{"active" if active else ""}">{label}</a>'
        for label, url, active in links
    )
    st.markdown(
        f'<div class="teleops-nav" style="justify-content: flex-{position};">{links_html}</div>',
        unsafe_allow_html=True,
    )


def metric_card(value: str | int | float, label: str, color: str = "accent") -> str:
    """Return HTML for a large metric card."""
    color_var = f"var(--{color})" if not color.startswith("#") else color
    return f"""
    <div class="teleops-metric-card">
        <div class="teleops-metric-value" style="color: {color_var};">{value}</div>
        <div class="teleops-metric-label">{label}</div>
    </div>
    """


def progress_bar(percent: float, variant: str = "success") -> str:
    """Return HTML for a progress bar. Variants: 'success', 'warning'."""
    return f"""
    <div class="teleops-progress">
        <div class="teleops-progress-fill teleops-progress-{variant}"
             style="width: {min(max(percent, 0), 100)}%;"></div>
    </div>
    """


def confidence_gauge(value: float, label: str) -> str:
    """Return HTML for confidence gauge visualization."""
    level = min(max(float(value), 0.0), 1.0)

    if level >= 0.8:
        color = "#1DD1A1"
    elif level >= 0.6:
        color = "#00D4AA"
    elif level >= 0.4:
        color = "#FECA57"
    else:
        color = "#FF6B6B"

    arc = 157 * level

    return f"""
    <div class="teleops-gauge-container">
        <svg width="100" height="60" viewBox="0 0 100 60">
            <path d="M10,55 A40,40 0 0,1 90,55"
                  stroke="var(--border)" stroke-width="8" fill="none" stroke-linecap="round"/>
            <path d="M10,55 A40,40 0 0,1 90,55"
                  stroke="{color}" stroke-width="8" fill="none" stroke-linecap="round"
                  stroke-dasharray="{arc} 999" style="filter: drop-shadow(0 0 6px {color});"/>
            <text x="50" y="48" text-anchor="middle"
                  font-family="JetBrains Mono" font-size="18" font-weight="600"
                  fill="{color}">{level:.0%}</text>
        </svg>
        <div style="flex:1; color: var(--ink); font-size: 14px; line-height: 1.4;">
            {label}
        </div>
    </div>
    """


def empty_state(message: str, icon: str = "") -> None:
    """Render an empty state message."""
    import streamlit as st
    icon_html = f'<div class="teleops-empty-icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""
        <div class="teleops-empty">
            {icon_html}
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
