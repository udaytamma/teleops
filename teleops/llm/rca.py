"""RCA generation with baseline and LLM."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from teleops.llm.client import get_llm_client


# Pattern-matching rules for baseline RCA
# Maps keywords in incident summary/alerts to hypotheses
BASELINE_RULES: list[dict[str, Any]] = [
    {
        "patterns": ["dns", "servfail", "nx_domain", "resolver"],
        "hypothesis": "authoritative DNS cluster outage in region-east",
        "confidence": 0.60,
        "evidence": "DNS-related alerts: servfail spikes, NXDOMAIN increases, resolver timeouts",
    },
    {
        "patterns": ["bgp", "route_withdrawal", "session_flap", "as65", "peering"],
        "hypothesis": "unstable BGP session with upstream AS causing route flaps",
        "confidence": 0.58,
        "evidence": "BGP session state changes, route withdrawals, prefix instability",
    },
    {
        "patterns": ["fiber", "optical", "dwdm", "loss_of_signal", "link_down"],
        "hypothesis": "fiber cut on metro ring segment causing optical link failure",
        "confidence": 0.65,
        "evidence": "Optical NMS alerts: loss of signal, link down events on transport layer",
    },
    {
        "patterns": ["control_plane", "cpu_spike", "freeze", "hang", "router"],
        "hypothesis": "control plane freeze on core router causing forwarding issues",
        "confidence": 0.55,
        "evidence": "Router CPU spikes, control plane unresponsive, routing updates stalled",
    },
    {
        "patterns": ["ddos", "syn_flood", "traffic_spike", "scrubbing", "volumetric"],
        "hypothesis": "volumetric DDoS attack targeting edge infrastructure",
        "confidence": 0.70,
        "evidence": "Security monitor alerts: traffic spike, SYN flood indicators, scrubbing triggered",
    },
    {
        "patterns": ["mpls", "vpn", "vrf", "route_leak", "l3vpn"],
        "hypothesis": "VRF misconfiguration causing MPLS/L3VPN route leak",
        "confidence": 0.52,
        "evidence": "MPLS alerts: route leak detected, VRF mismatch, unexpected prefix propagation",
    },
    {
        "patterns": ["cdn", "cache", "stampede", "origin", "ttl"],
        "hypothesis": "CDN cache stampede due to TTL misconfiguration",
        "confidence": 0.58,
        "evidence": "CDN alerts: cache miss spike, origin latency increase, TTL-related errors",
    },
    {
        "patterns": ["firewall", "blocked", "policy_violation", "rule"],
        "hypothesis": "firewall rule misconfiguration blocking critical traffic",
        "confidence": 0.62,
        "evidence": "Firewall alerts: blocked port events, policy violation logs",
    },
    {
        "patterns": ["database", "db", "query_latency", "lock_waits", "contention"],
        "hypothesis": "database contention causing latency spike on hosted applications",
        "confidence": 0.55,
        "evidence": "Database alerts: query latency spikes, lock waits, connection pool exhaustion",
    },
    {
        "patterns": ["peering", "congestion", "isp", "as64"],
        "hypothesis": "congestion on ISP peering link causing packet loss",
        "confidence": 0.57,
        "evidence": "Peering alerts: high latency, packet loss on ISP interconnect",
    },
    # Default fallback for network_degradation
    {
        "patterns": ["packet_loss", "latency", "degradation", "network"],
        "hypothesis": "link congestion on core-router-1 causing packet loss",
        "confidence": 0.55,
        "evidence": "Network alerts: packet_loss/high_latency burst on core-router-1",
    },
]


def baseline_rca(incident_summary: str, alerts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Generate baseline RCA using pattern-matching rules.

    Analyzes incident summary and alert data to select the most appropriate
    hypothesis from predefined rules. Falls back to network degradation if
    no patterns match.

    Args:
        incident_summary: Text summary of the incident
        alerts: Optional list of alert dictionaries for additional context

    Returns:
        RCA result with hypotheses, confidence scores, and evidence
    """
    # Build search text from incident summary and alerts
    search_text = incident_summary.lower()
    if alerts:
        for alert in alerts[:20]:  # Check first 20 alerts
            search_text += f" {alert.get('alert_type', '')} {alert.get('message', '')}".lower()

    # Find matching rule
    matched_rule = None
    match_count = 0

    for rule in BASELINE_RULES:
        current_matches = sum(1 for pattern in rule["patterns"] if pattern in search_text)
        if current_matches > match_count:
            match_count = current_matches
            matched_rule = rule

    # Use matched rule or default to last rule (network_degradation)
    if matched_rule is None:
        matched_rule = BASELINE_RULES[-1]

    hypothesis = matched_rule["hypothesis"]
    confidence = matched_rule["confidence"]
    evidence = matched_rule["evidence"]

    return {
        "incident_summary": incident_summary,
        "hypotheses": [hypothesis],
        "confidence_scores": {hypothesis: confidence},
        "evidence": {"alerts": evidence, "match_count": match_count},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "baseline-rules",
    }


def _detect_scenario_hint(incident: dict[str, Any], alerts: list[dict[str, Any]]) -> str:
    """Detect likely scenario type from alerts to provide a hint to the LLM.

    Uses the same pattern-matching rules as the baseline RCA to identify the
    most likely scenario type. Returns a short hint string for the LLM prompt.
    """
    search_text = (incident.get("summary", "") or "").lower()
    for alert in alerts[:20]:
        search_text += f" {alert.get('alert_type', '')} {alert.get('message', '')}".lower()

    best_rule = None
    best_matches = 0
    for rule in BASELINE_RULES:
        matches = sum(1 for p in rule["patterns"] if p in search_text)
        if matches > best_matches:
            best_matches = matches
            best_rule = rule

    if best_rule and best_matches >= 2:
        return best_rule["hypothesis"]

    return ""


def build_prompt(incident: dict[str, Any], alerts: list[dict[str, Any]], rag_context: list[str]) -> str:
    # Extract alert types and detect scenario hint from baseline pattern matching
    alert_types = sorted({a.get("alert_type", "") for a in alerts[:20] if a.get("alert_type")})
    hosts = sorted({a.get("host", "") for a in alerts[:20] if a.get("host")})
    scenario_hint = _detect_scenario_hint(incident, alerts)

    prompt = {
        "instruction": (
            "Analyze the incident below and produce a root cause analysis. "
            "Return only valid JSON following the schema below. "
            "Do not wrap the JSON in markdown or code fences. "
            "Output must start with '{' and end with '}' with no surrounding text."
        ),
        "schema": {
            "incident_summary": "string - restate the incident in your own words",
            "hypotheses": ["string - specific root cause naming components and failure mode"],
            "confidence_scores": {"hypothesis_text": "float 0.0-1.0"},
            "evidence": {
                "alert_signals": "string - which alert types support this hypothesis",
                "affected_components": "string - specific hosts/links/services affected",
                "rag_references": "string - relevant context from runbooks",
            },
            "generated_at": "ISO-8601 timestamp",
            "model": "string - your model identifier",
        },
        "few_shot_examples": [
            {
                "incident_summary": "DNS resolution failures across region-east",
                "hypotheses": ["authoritative DNS cluster outage in region-east"],
                "confidence_scores": {"authoritative DNS cluster outage in region-east": 0.75},
                "evidence": {
                    "alert_signals": "dns_timeout (12 alerts), servfail_spike (8 alerts), nx_domain_spike (5 alerts)",
                    "affected_components": "dns-auth-1, dns-rec-1",
                    "rag_references": "DNS outage runbook: check SOA records, verify zone transfer status",
                },
            },
            {
                "incident_summary": "High packet loss on core backbone links",
                "hypotheses": [
                    "fiber cut on metro ring segment causing optical link failure",
                    "link congestion on core-router-1 due to traffic rerouting",
                ],
                "confidence_scores": {
                    "fiber cut on metro ring segment causing optical link failure": 0.65,
                    "link congestion on core-router-1 due to traffic rerouting": 0.30,
                },
                "evidence": {
                    "alert_signals": "link_down (6 alerts), loss_of_signal (4 alerts), packet_loss (15 alerts)",
                    "affected_components": "core-router-1, core-router-2, agg-switch-2",
                    "rag_references": "Fiber cut runbook: check optical power levels, verify DWDM transponder status",
                },
            },
        ],
        "scenario_hint": scenario_hint if scenario_hint else "No strong pattern match -- analyze alerts independently",
        "incident": incident,
        "alerts_sample": alerts[:20],
        "alert_type_summary": alert_types,
        "affected_hosts": hosts,
        "rag_context": rag_context,
        "constraints": [
            "Do not invent remediation commands.",
            "If uncertain, include lower confidence score.",
            "Hypotheses must name specific infrastructure components (routers, links, services).",
            "Evidence must reference specific alert types from the alerts_sample.",
            "Limit to 1-3 hypotheses, ordered by confidence (highest first).",
            "Confidence scores must reflect genuine uncertainty -- do not default to 0.5.",
            "Use the rag_context to ground your analysis in domain-specific knowledge.",
        ],
    }
    return json_dumps(prompt)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, default=_json_default)


def llm_rca(incident: dict[str, Any], alerts: list[dict[str, Any]], rag_context: list[str]) -> dict[str, Any]:
    client = get_llm_client()
    prompt = build_prompt(incident, alerts, rag_context)
    return client.generate(prompt)
