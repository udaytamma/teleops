import json

from teleops.config import settings
from teleops.models import Alert, Incident, RCAArtifact


def test_metrics_overview_includes_counts_and_files(client, db_session, tmp_path, monkeypatch):
    alert = Alert(
        source_system="net-snmp",
        host="core-router-1",
        service="backbone",
        severity="critical",
        alert_type="packet_loss",
        message="loss",
        tags={"incident": "network_degradation"},
        raw_payload={"loss_pct": 10},
        tenant_id="tenant-a",
    )
    db_session.add(alert)
    db_session.commit()

    incident = Incident(
        start_time=alert.timestamp,
        end_time=alert.timestamp,
        severity="critical",
        status="open",
        related_alert_ids=[alert.id],
        summary="Correlated incident for tag: network_degradation",
        suspected_root_cause=None,
        impact_scope="network",
        owner=None,
        created_by="test",
        tenant_id="tenant-a",
    )
    db_session.add(incident)
    db_session.commit()

    artifact = RCAArtifact(
        incident_id=incident.id,
        hypotheses=["test"],
        evidence={"alerts": "test"},
        confidence_scores={"test": 0.5},
        llm_model="baseline-rules",
    )
    db_session.add(artifact)
    db_session.commit()

    test_results_path = tmp_path / "test_results.json"
    eval_results_path = tmp_path / "evaluation_results.json"
    test_results_path.write_text(json.dumps({"status": "passed"}), encoding="utf-8")
    eval_results_path.write_text(json.dumps({"baseline_avg": 0.5}), encoding="utf-8")
    monkeypatch.setattr(settings, "test_results_path", str(test_results_path))
    monkeypatch.setattr(settings, "evaluation_results_path", str(eval_results_path))

    resp = client.get("/metrics/overview")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["counts"]["alerts"] == 1
    assert payload["counts"]["incidents"] == 1
    assert payload["counts"]["rca_artifacts"] == 1
    assert payload["test_results"]["status"] == "passed"
    assert payload["evaluation_results"]["baseline_avg"] == 0.5
