"""Benchmark baseline and LLM RCA latency for TeleOps."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from teleops.config import settings
from teleops.data_gen.generator import ScenarioConfig, generate_scenario
from teleops.llm.rca import baseline_rca, llm_rca
from teleops.rag.index import get_rag_context


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    if pct <= 0:
        return values[0]
    if pct >= 100:
        return values[-1]
    k = (len(values) - 1) * (pct / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return d0 + d1


def _summarize(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {
            "count": 0,
            "avg_ms": None,
            "min_ms": None,
            "p50_ms": None,
            "p90_ms": None,
            "p99_ms": None,
            "max_ms": None,
        }
    values_sorted = sorted(values)
    return {
        "count": len(values_sorted),
        "avg_ms": round(statistics.mean(values_sorted), 3),
        "min_ms": round(values_sorted[0], 3),
        "p50_ms": round(_percentile(values_sorted, 50) or 0.0, 3),
        "p90_ms": round(_percentile(values_sorted, 90) or 0.0, 3),
        "p99_ms": round(_percentile(values_sorted, 99) or 0.0, 3),
        "max_ms": round(values_sorted[-1], 3),
    }


def run_benchmark(runs: int) -> dict[str, object]:
    baseline_times: list[float] = []
    rag_times: list[float] = []
    llm_times: list[float] = []
    llm_errors = 0

    scenario_types = [
        "network_degradation",
        "dns_outage",
        "bgp_flap",
        "fiber_cut",
        "router_freeze",
        "isp_peering_congestion",
        "ddos_edge",
        "mpls_vpn_leak",
        "cdn_cache_stampede",
        "firewall_rule_misconfig",
        "database_latency_spike",
    ]

    for seed in range(runs):
        incident_type = scenario_types[seed % len(scenario_types)]
        config = ScenarioConfig(seed=seed, incident_type=incident_type)
        alerts, ground_truth = generate_scenario(config)
        incident_summary = f"Correlated incident for tag: {ground_truth.incident_type}"

        start = perf_counter()
        baseline_rca(incident_summary, alerts)
        baseline_times.append((perf_counter() - start) * 1000)

        start = perf_counter()
        rag_context = get_rag_context(f"{ground_truth.incident_type} {ground_truth.root_cause}")
        rag_times.append((perf_counter() - start) * 1000)

        start = perf_counter()
        try:
            llm_rca({"summary": incident_summary}, alerts, rag_context)
            llm_times.append((perf_counter() - start) * 1000)
        except Exception:
            llm_errors += 1

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "runs": runs,
        "llm_errors": llm_errors,
        "baseline_ms": _summarize(baseline_times),
        "rag_ms": _summarize(rag_times),
        "llm_ms": _summarize(llm_times),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark RCA latency.")
    parser.add_argument("--runs", type=int, default=20, help="Number of scenarios to benchmark.")
    parser.add_argument(
        "--write-json",
        default="storage/benchmarks/rca_latency.json",
        help="Path to write JSON benchmark results.",
    )
    args = parser.parse_args()

    results = run_benchmark(args.runs)
    output_path = Path(args.write_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
