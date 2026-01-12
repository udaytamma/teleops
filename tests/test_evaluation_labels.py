from pathlib import Path

from scripts.evaluate import load_manual_labels, run_manual_label_eval


def test_manual_labels_load_and_score():
    path = Path("docs/evaluation/manual_labels.jsonl")
    labels = load_manual_labels(path)
    assert len(labels) >= 10
    results = run_manual_label_eval(labels[:5])
    assert results["manual_label_cases"] == 5
