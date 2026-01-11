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


def generate_network_degradation(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    rng = Random(config.seed)
    start_time = datetime.now(timezone.utc)
    alerts: list[dict[str, Any]] = []

    incident_hosts = ["core-router-1", "edge-router-3", "agg-switch-2"]
    services = ["backbone", "edge", "aggregation"]
    root_cause = "link congestion on core-router-1 causing packet loss"
    remediation_steps = [
        "Reroute traffic away from core-router-1",
        "Apply QoS policy to throttle non-critical traffic",
        "Inspect interface errors and clear if safe",
    ]

    total_minutes = config.duration_min
    for minute in range(total_minutes):
        timestamp = start_time + timedelta(minutes=minute)
        # Primary incident alerts
        for _ in range(config.alert_rate_per_min):
            host = rng.choice(incident_hosts)
            service = rng.choice(services)
            alert = {
                "timestamp": timestamp,
                "source_system": "net-snmp",
                "host": host,
                "service": service,
                "severity": "critical",
                "alert_type": rng.choice(["packet_loss", "high_latency"]),
                "message": f"{host} reports degraded network performance",
                "tags": {"incident": "network_degradation"},
                "raw_payload": {"latency_ms": rng.randint(200, 800), "loss_pct": rng.randint(5, 30)},
                "tenant_id": "tenant-a",
            }
            alerts.append(alert)

        # Noise alerts
        for _ in range(config.noise_rate_per_min):
            alert = {
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
            alerts.append(alert)

    ground_truth = GroundTruth(
        incident_type="network_degradation",
        root_cause=root_cause,
        remediation_steps=remediation_steps,
    )
    return alerts, ground_truth


def generate_scenario(config: ScenarioConfig) -> tuple[list[dict[str, Any]], GroundTruth]:
    if config.incident_type != "network_degradation":
        raise ValueError(f"Unsupported incident type: {config.incident_type}")
    return generate_network_degradation(config)
