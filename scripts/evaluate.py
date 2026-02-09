"""Evaluation script for TeleOps MVP.

Uses semantic (embedding-based) similarity to score RCA hypotheses
against ground truth, replacing the original string-matching approach.
"""

from __future__ import annotations

import statistics
import re
import argparse
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from teleops.data_gen.generator import ScenarioConfig, generate_scenario
from teleops.llm.rca import baseline_rca, llm_rca
from teleops.rag.index import get_rag_context

# Same embedding model used by the RAG pipeline
_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Thresholds for quality metrics
CORRECT_THRESHOLD = 0.75  # Semantic similarity >= this = correct identification
WRONG_CONFIDENT_SIM = 0.5  # Below this = wrong
WRONG_CONFIDENT_CONF = 0.7  # Above this confidence + wrong = "wrong but confident"


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similarity(a: str, b: str) -> float:
    """Compute cosine similarity between two texts using sentence embeddings."""
    embeddings = _MODEL.encode([_normalize(a), _normalize(b)])
    cosine = float(np.dot(embeddings[0], embeddings[1]) / (
        np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
    ))
    return max(0.0, cosine)  # Clamp negatives to 0


def score_output(output: dict, ground_truth: str) -> float:
    hypotheses = output.get("hypotheses", [])
    if not hypotheses:
        return 0.0
    best = max(similarity(h, ground_truth) for h in hypotheses)
    return best


def _get_max_confidence(output: dict) -> float:
    """Extract the highest confidence score from an RCA output."""
    scores = output.get("confidence_scores", {})
    if not scores:
        return 0.0
    return max(scores.values())


def compute_quality_metrics(scenarios: list[dict]) -> dict:
    """Compute precision, recall, wrong-but-confident rate, and confidence calibration."""
    results = {}
    for source in ("baseline", "llm"):
        score_key = f"{source}_score"
        conf_key = f"{source}_confidence"

        attempted = [s for s in scenarios if s.get(score_key) is not None]
        if not attempted:
            results[source] = None
            continue

        correct = [s for s in attempted if s[score_key] >= CORRECT_THRESHOLD]
        incorrect = [s for s in attempted if s[score_key] < CORRECT_THRESHOLD]
        wrong_confident = [
            s for s in attempted
            if s[score_key] < WRONG_CONFIDENT_SIM and s.get(conf_key, 0) >= WRONG_CONFIDENT_CONF
        ]

        correct_confs = [s[conf_key] for s in correct if s.get(conf_key) is not None]
        incorrect_confs = [s[conf_key] for s in incorrect if s.get(conf_key) is not None]

        results[source] = {
            "precision": round(len(correct) / len(attempted), 3) if attempted else 0.0,
            "recall": round(len(correct) / len(scenarios), 3) if scenarios else 0.0,
            "wrong_but_confident_rate": round(len(wrong_confident) / len(attempted), 3) if attempted else 0.0,
            "wrong_but_confident_count": len(wrong_confident),
            "avg_confidence_correct": round(statistics.mean(correct_confs), 3) if correct_confs else None,
            "avg_confidence_incorrect": round(statistics.mean(incorrect_confs), 3) if incorrect_confs else None,
            "total_attempted": len(attempted),
            "total_correct": len(correct),
        }
    return results


def run_eval(num_runs: int = 50) -> dict:
    baseline_scores = []
    llm_scores = []
    per_scenario = []

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

    for seed in range(num_runs):
        incident_type = scenario_types[seed % len(scenario_types)]
        config = ScenarioConfig(seed=seed, incident_type=incident_type)
        alerts, ground_truth = generate_scenario(config)

        incident_summary = f"Correlated incident for tag: {ground_truth.incident_type}"
        baseline = baseline_rca(incident_summary)
        b_score = score_output(baseline, ground_truth.root_cause)
        baseline_scores.append(b_score)

        scenario_entry = {
            "scenario_type": incident_type,
            "seed": seed,
            "ground_truth": ground_truth.root_cause,
            "baseline_hypothesis": baseline["hypotheses"][0] if baseline.get("hypotheses") else None,
            "baseline_score": round(b_score, 3),
            "baseline_confidence": _get_max_confidence(baseline),
            "llm_hypothesis": None,
            "llm_score": None,
            "llm_confidence": None,
        }

        rag_context = get_rag_context(f"{ground_truth.incident_type} {ground_truth.root_cause}")
        try:
            llm_out = llm_rca({"summary": incident_summary}, alerts, rag_context)
            l_score = score_output(llm_out, ground_truth.root_cause)
            llm_scores.append(l_score)
            scenario_entry["llm_hypothesis"] = llm_out["hypotheses"][0] if llm_out.get("hypotheses") else None
            scenario_entry["llm_score"] = round(l_score, 3)
            scenario_entry["llm_confidence"] = _get_max_confidence(llm_out)
        except Exception:
            pass

        per_scenario.append(scenario_entry)

    quality_metrics = compute_quality_metrics(per_scenario)

    results = {
        "baseline_avg": round(statistics.mean(baseline_scores), 3) if baseline_scores else 0.0,
        "baseline_median": round(statistics.median(baseline_scores), 3) if baseline_scores else 0.0,
        "llm_avg": round(statistics.mean(llm_scores), 3) if llm_scores else None,
        "llm_median": round(statistics.median(llm_scores), 3) if llm_scores else None,
        "runs": num_runs,
        "scoring_method": "semantic_cosine_similarity",
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "thresholds": {
            "correct": CORRECT_THRESHOLD,
            "wrong_confident_similarity": WRONG_CONFIDENT_SIM,
            "wrong_confident_confidence": WRONG_CONFIDENT_CONF,
        },
        "quality_metrics": quality_metrics,
        "per_scenario": per_scenario,
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
        "manual_label_avg": round(statistics.mean(scores), 3) if scores else 0.0,
        "manual_label_median": round(statistics.median(scores), 3) if scores else 0.0,
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
    print(json.dumps(results, indent=2))
