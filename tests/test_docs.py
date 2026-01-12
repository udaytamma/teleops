from pathlib import Path


def test_required_docs_exist():
    required = [
        "docs/test_plan.md",
        "docs/threat_model.md",
        "docs/redaction_policy.md",
        "docs/security_controls.md",
        "docs/integrations/README.md",
        "docs/data_dictionary.md",
        "docs/deployment_runbook.md",
        "docs/cost_estimate.md",
        "docs/ux_feedback.md",
    ]
    for path in required:
        assert Path(path).exists()
