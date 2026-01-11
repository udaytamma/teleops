"""Evaluation script for TeleOps MVP."""

from __future__ import annotations

import statistics
from difflib import SequenceMatcher

from teleops.data_gen.generator import ScenarioConfig, generate_scenario
from teleops.llm.rca import baseline_rca, llm_rca
from teleops.rag.index import get_rag_context


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def score_output(output: dict, ground_truth: str) -> float:
    hypotheses = output.get("hypotheses", [])
    if not hypotheses:
        return 0.0
    best = max(similarity(h, ground_truth) for h in hypotheses)
    return best


def run_eval(num_runs: int = 50) -> dict:
    baseline_scores = []
    llm_scores = []

    for seed in range(num_runs):
        config = ScenarioConfig(seed=seed)
        alerts, ground_truth = generate_scenario(config)

        incident_summary = "Correlated incident for tag: network_degradation"
        baseline = baseline_rca(incident_summary)
        baseline_scores.append(score_output(baseline, ground_truth.root_cause))

        rag_context = get_rag_context("network degradation packet loss latency")
        try:
            llm_out = llm_rca({"summary": incident_summary}, alerts, rag_context)
            llm_scores.append(score_output(llm_out, ground_truth.root_cause))
        except Exception:
            # If LLM not configured, skip scoring.
            pass

    results = {
        "baseline_avg": statistics.mean(baseline_scores) if baseline_scores else 0.0,
        "baseline_median": statistics.median(baseline_scores) if baseline_scores else 0.0,
        "llm_avg": statistics.mean(llm_scores) if llm_scores else None,
        "llm_median": statistics.median(llm_scores) if llm_scores else None,
        "runs": num_runs,
    }
    return results


if __name__ == "__main__":
    print(run_eval())
