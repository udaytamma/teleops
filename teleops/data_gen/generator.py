"""Synthetic alert generator for TeleOps."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Any


@dataclass
class ScenarioConfig:
    incident_type: str = "network_degradation"
    alert_rate_per_min: int = 20
    duration_min: int = 10
    noise_rate_per_min: int = 5
    seed: int | None = 42


@dataclass
class GroundTruth:
    incident_type: str
    root_cause: str
    remediation_steps: list[str]


def _build_noise_alerts(rng: Random, timestamp: datetime, count: int) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    for _ in range(count):
        alerts.append(
            {
                "timestamp": timestamp,
                "source_system": rng.choice(["k8s-node", "db", "web-app"]),
                "host": f"host-{rng.randint(10, 99)}",
                "service": rng.choice(["billing", "auth", "api-gateway"]),
                "severity": rng.choice(["warning", "info"]),
                "alert_type": rng.choice(["cpu_spike", "disk_io", "http_5xx"]),
                "message": "Unrelated transient alert",
                "tags": {"incident": "noise"},
                "raw_payload": {"value": rng.randint(1, 100)},
                "tenant_id": "tenant-a",
            }
        )
    return alerts


def _generate_scenario(
    config: ScenarioConfig,
    incident_type: str,
    hosts: list[str],
    services: list[str],
    alert_types: list[str],
    root_cause: str,
    remediation_steps: list[str],
    source_system: str = "net-snmp",
    message_template: str = "{host} reports degraded network performance",
) -> tuple[list[dict[str, Any]], GroundTruth]:
    rng = Random(config.seed)
    start_time = datetime.now(timezone.utc)
    alerts: list[dict[str, Any]] = []

    for minute in range(config.duration_min):
        timestamp = start_time + timedelta(minutes=minute)
        for _ in range(config.alert_rate_per_min):
            host = rng.choice(hosts)
            service = rng.choice(services)
            alert_type = rng.choice(alert_types)
            alert = {
                "timestamp": timestamp,
                "source_system": source_system,
                "host": host,
                "service": service,
                "severity": "critical",
                "alert_type": alert_type,
                "message": message_template.format(host=host, alert_type=alert_type),
                "tags": {"incident": incident_type},
                "raw_payload": {"value": rng.randint(1, 100)},
                "tenant_id": "tenant-a",
            }
            alerts.append(alert)

        alerts.extend(_build_noise_alerts(rng, timestamp, config.noise_rate_per_min))

    ground_truth = GroundTruth(
        incident_type=incident_type,
        root_cause=root_cause,
        remediation_steps=remediation_steps,
    )
    return alerts, ground_truth


def generate_network_degradation(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="network_degradation",
        hosts=["core-router-1", "edge-router-3", "agg-switch-2"],
        services=["backbone", "edge", "aggregation"],
        alert_types=["packet_loss", "high_latency"],
        root_cause="link congestion on core-router-1 causing packet loss",
        remediation_steps=[
            "Reroute traffic away from core-router-1",
            "Apply QoS policy to throttle non-critical traffic",
            "Inspect interface errors and clear if safe",
        ],
        message_template="{host} reports degraded network performance",
    )


def generate_dns_outage(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="dns_outage",
        hosts=["dns-auth-1", "dns-auth-2", "dns-rec-1"],
        services=["dns", "resolver"],
        alert_types=["dns_timeout", "servfail_spike", "nx_domain_spike"],
        root_cause="authoritative DNS cluster outage in region-east",
        remediation_steps=[
            "Fail over DNS traffic to secondary region",
            "Restart unhealthy DNS pods or services",
            "Verify zone file integrity and replication",
        ],
        message_template="{host} reports DNS failures",
    )


def generate_bgp_flap(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="bgp_flap",
        hosts=["core-router-1", "core-router-2"],
        services=["routing"],
        alert_types=["bgp_session_flap", "route_withdrawal"],
        root_cause="unstable BGP session with upstream AS65010",
        remediation_steps=[
            "Stabilize the affected BGP session and damp flaps",
            "Engage upstream to validate peering health",
            "Apply route dampening policy for noisy prefixes",
        ],
        message_template="{host} reports BGP instability",
    )


def generate_fiber_cut(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="fiber_cut",
        hosts=["metro-ring-1", "dwdm-2", "edge-router-3"],
        services=["transport", "backhaul"],
        alert_types=["link_down", "loss_of_signal"],
        root_cause="fiber cut on metro ring segment A",
        remediation_steps=[
            "Reroute traffic over redundant path",
            "Dispatch field team to inspect fiber segment",
            "Validate optical power levels post-repair",
        ],
        source_system="optical-nms",
        message_template="{host} reports optical link failure",
    )


def generate_router_freeze(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="router_freeze",
        hosts=["core-router-1"],
        services=["control-plane"],
        alert_types=["cpu_spike", "control_plane_hang"],
        root_cause="control plane freeze on core-router-1",
        remediation_steps=[
            "Fail over routing to standby control plane",
            "Collect core dump and reboot if required",
            "Upgrade firmware to latest stable release",
        ],
        message_template="{host} reports control plane stall",
    )


def generate_isp_peering_congestion(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="isp_peering_congestion",
        hosts=["peering-edge-1", "peering-edge-2"],
        services=["peering"],
        alert_types=["high_latency", "packet_loss"],
        root_cause="congestion on ISP peering link with AS64512",
        remediation_steps=[
            "Shift traffic to alternate peer",
            "Coordinate capacity upgrade with peer",
            "Apply traffic engineering for hot prefixes",
        ],
        message_template="{host} reports peering congestion",
    )


def generate_ddos_edge(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="ddos_edge",
        hosts=["edge-router-3", "scrubbing-1"],
        services=["edge", "security"],
        alert_types=["traffic_spike", "syn_flood"],
        root_cause="volumetric DDoS targeting edge-router-3",
        remediation_steps=[
            "Activate scrubbing center routing",
            "Apply rate limiting at edge",
            "Block offending IP ranges upstream",
        ],
        source_system="security-monitor",
        message_template="{host} reports DDoS indicators",
    )


def generate_mpls_vpn_leak(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="mpls_vpn_leak",
        hosts=["pe-core-1", "pe-core-2"],
        services=["mpls"],
        alert_types=["route_leak_detected", "vrf_mismatch"],
        root_cause="VRF misconfiguration causing MPLS/L3VPN route leak",
        remediation_steps=[
            "Rollback recent VRF policy changes",
            "Validate route targets and import/export rules",
            "Flush leaked routes and monitor reconvergence",
        ],
        message_template="{host} reports VPN route leak",
    )


def generate_cdn_cache_stampede(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="cdn_cache_stampede",
        hosts=["cdn-edge-1", "cdn-edge-2"],
        services=["cdn"],
        alert_types=["cache_miss_spike", "origin_latency"],
        root_cause="CDN cache stampede due to misconfigured TTLs",
        remediation_steps=[
            "Restore cache TTL defaults",
            "Warm cache for hot content",
            "Throttle origin requests temporarily",
        ],
        source_system="cdn-monitor",
        message_template="{host} reports cache stampede",
    )


def generate_firewall_rule_misconfig(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="firewall_rule_misconfig",
        hosts=["fw-edge-1", "fw-core-1"],
        services=["security"],
        alert_types=["blocked_port", "policy_violation"],
        root_cause="firewall rule misconfiguration blocking critical port",
        remediation_steps=[
            "Rollback recent firewall rule changes",
            "Add explicit allow rule for critical service",
            "Audit policy deployment pipeline",
        ],
        source_system="firewall",
        message_template="{host} reports blocked traffic",
    )


def generate_database_latency_spike(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    return _generate_scenario(
        config=config,
        incident_type="database_latency_spike",
        hosts=["db-primary-1", "db-replica-2"],
        services=["msp-database"],
        alert_types=["query_latency", "lock_waits"],
        root_cause="database contention causing latency spike on MSP hosted apps",
        remediation_steps=[
            "Identify top blocking queries",
            "Scale read replicas or route traffic",
            "Apply indexing or query optimization",
        ],
        source_system="db",
        message_template="{host} reports database latency",
    )


def generate_scenario(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    scenario_map = {
        "network_degradation": generate_network_degradation,
        "dns_outage": generate_dns_outage,
        "bgp_flap": generate_bgp_flap,
        "fiber_cut": generate_fiber_cut,
        "router_freeze": generate_router_freeze,
        "isp_peering_congestion": generate_isp_peering_congestion,
        "ddos_edge": generate_ddos_edge,
        "mpls_vpn_leak": generate_mpls_vpn_leak,
        "cdn_cache_stampede": generate_cdn_cache_stampede,
        "firewall_rule_misconfig": generate_firewall_rule_misconfig,
        "database_latency_spike": generate_database_latency_spike,
    }
    generator = scenario_map.get(config.incident_type)
    if not generator:
        raise ValueError(f"Unsupported incident type: {config.incident_type}")
    return generator(config)
