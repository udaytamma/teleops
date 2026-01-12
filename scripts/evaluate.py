"""Evaluation script for TeleOps MVP."""

from __future__ import annotations

import statistics
from difflib import SequenceMatcher

import argparse
import json
from pathlib import Path

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


def load_manual_labels(path: Path) -> list[dict]:
    labels: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            labels.append(json.loads(line))
    return labels


def run_manual_label_eval(labels: list[dict]) -> dict:
    scores = []
    for label in labels:
        summary = label.get("incident_summary", "")
        root_cause = label.get("root_cause", "")
        output = baseline_rca(summary)
        scores.append(score_output(output, root_cause))

    return {
        "manual_label_cases": len(labels),
        "manual_label_avg": statistics.mean(scores) if scores else 0.0,
        "manual_label_median": statistics.median(scores) if scores else 0.0,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run TeleOps evaluation.")
    parser.add_argument("--runs", type=int, default=50, help="Number of synthetic runs.")
    parser.add_argument(
        "--labels-file",
        default="docs/evaluation/manual_labels.jsonl",
        help="Optional JSONL file for manual label evaluation.",
    )
    parser.add_argument(
        "--write-json",
        default="",
        help="Optional path to write evaluation results as JSON.",
    )
    args = parser.parse_args()

    results = run_eval(num_runs=args.runs)

    labels_path = Path(args.labels_file)
    if labels_path.exists():
        labels = load_manual_labels(labels_path)
        results.update(run_manual_label_eval(labels))

    if args.write_json:
        Path(args.write_json).write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(results)
