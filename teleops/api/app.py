"""FastAPI app for TeleOps."""

from __future__ import annotations

from typing import Any
from datetime import datetime, timezone
from pathlib import Path
import json

from fastapi import Depends, FastAPI, HTTPException, Query, Header
from sqlalchemy.orm import Session

from teleops.config import settings
from teleops.data_gen.generator import ScenarioConfig, generate_scenario
from teleops.db import SessionLocal
from teleops.incident_corr.correlator import correlate_alerts
from teleops.llm.rca import baseline_rca, llm_rca
from teleops.models import Alert, Incident, RCAArtifact
from teleops.rag.index import get_rag_context

app = FastAPI(title="TeleOps API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def alert_to_dict(alert: Alert) -> dict[str, Any]:
    return {
        "id": alert.id,
        "timestamp": alert.timestamp.isoformat(),
        "source_system": alert.source_system,
        "host": alert.host,
        "service": alert.service,
        "severity": alert.severity,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "tags": alert.tags,
        "raw_payload": alert.raw_payload,
        "tenant_id": alert.tenant_id,
    }


def incident_to_dict(incident: Incident) -> dict[str, Any]:
    return {
        "id": incident.id,
        "start_time": incident.start_time.isoformat(),
        "end_time": incident.end_time.isoformat() if incident.end_time else None,
        "severity": incident.severity,
        "status": incident.status,
        "related_alert_ids": incident.related_alert_ids,
        "summary": incident.summary,
        "suspected_root_cause": incident.suspected_root_cause,
        "impact_scope": incident.impact_scope,
        "owner": incident.owner,
        "created_by": incident.created_by,
        "tenant_id": incident.tenant_id,
    }


def _load_fixture(name: str) -> dict[str, Any]:
    fixture_dir = Path(settings.integrations_fixtures_dir)
    path = fixture_dir / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fixture not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _append_integration_event(source: str, payload: dict[str, Any]) -> None:
    log_path = Path(settings.integrations_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def _load_metrics_file(path_str: str) -> dict[str, Any] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def require_api_token(authorization: str | None = Header(default=None), x_api_key: str | None = Header(default=None)):
    if not settings.api_token:
        return
    token = x_api_key
    if not token and authorization:
        if authorization.lower().startswith("bearer "):
            token = authorization.split(" ", 1)[1].strip()
    if token != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/generate")
def generate_alerts(payload: dict[str, Any], db: Session = Depends(get_db), _: None = Depends(require_api_token)):
    config = ScenarioConfig(
        incident_type=payload.get("incident_type", "network_degradation"),
        alert_rate_per_min=payload.get("alert_rate_per_min", 20),
        duration_min=payload.get("duration_min", 10),
        noise_rate_per_min=payload.get("noise_rate_per_min", 5),
        seed=payload.get("seed", 42),
    )
    alerts, ground_truth = generate_scenario(config)

    alert_models = []
    for alert in alerts:
        model = Alert(
            timestamp=alert["timestamp"],
            source_system=alert["source_system"],
            host=alert["host"],
            service=alert["service"],
            severity=alert["severity"],
            alert_type=alert["alert_type"],
            message=alert["message"],
            tags=alert["tags"],
            raw_payload=alert["raw_payload"],
            tenant_id=alert.get("tenant_id"),
        )
        alert_models.append(model)
        db.add(model)
    db.commit()

    alert_ids = [model.id for model in alert_models]
    incidents = correlate_alerts(db, alert_ids=alert_ids)

    return {
        "alerts_inserted": len(alert_models),
        "incidents_created": [incident_to_dict(i) for i in incidents],
        "ground_truth": ground_truth.__dict__,
    }


@app.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return [alert_to_dict(alert) for alert in alerts]


@app.get("/incidents")
def list_incidents(db: Session = Depends(get_db)):
    incidents = db.query(Incident).all()
    return [incident_to_dict(incident) for incident in incidents]


@app.get("/incidents/{incident_id}/alerts")
def list_incident_alerts(incident_id: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not incident.related_alert_ids:
        return []
    alerts = db.query(Alert).filter(Alert.id.in_(incident.related_alert_ids)).all()
    return [alert_to_dict(alert) for alert in alerts]


@app.post("/reset")
def reset_data(db: Session = Depends(get_db), _: None = Depends(require_api_token)):
    db.query(RCAArtifact).delete()
    db.query(Incident).delete()
    db.query(Alert).delete()
    db.commit()
    return {"status": "ok"}


@app.post("/rca/{incident_id}/baseline")
def generate_baseline_rca(incident_id: str, db: Session = Depends(get_db), _: None = Depends(require_api_token)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    result = baseline_rca(incident.summary)
    artifact = RCAArtifact(
        incident_id=incident.id,
        hypotheses=result["hypotheses"],
        evidence=result["evidence"],
        confidence_scores=result["confidence_scores"],
        llm_model=result["model"],
    )
    db.add(artifact)
    db.commit()

    return result


@app.post("/rca/{incident_id}/llm")
def generate_llm_rca(incident_id: str, db: Session = Depends(get_db), _: None = Depends(require_api_token)):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    alerts = db.query(Alert).filter(Alert.id.in_(incident.related_alert_ids)).all()
    incident_dict = incident_to_dict(incident)
    alerts_dicts = [alert_to_dict(alert) for alert in alerts]

    rag_query = f"incident type: network degradation, alerts: {len(alerts)}"
    try:
        rag_context = get_rag_context(rag_query)
        request_payload = {
            "incident": incident_dict,
            "alerts_sample": alerts_dicts[:20],
            "rag_context": rag_context,
        }
        result = llm_rca(incident_dict, alerts_dicts, rag_context)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"LLM/RAG error: {exc}") from exc
    artifact = RCAArtifact(
        incident_id=incident.id,
        hypotheses=result.get("hypotheses", []),
        evidence={
            "llm_evidence": result.get("evidence", {}),
            "llm_request": request_payload,
            "llm_response": result,
        },
        confidence_scores=result.get("confidence_scores", {}),
        llm_model=result.get("model", "unknown"),
    )
    db.add(artifact)
    db.commit()

    return result


@app.get("/rca/{incident_id}/latest")
def get_latest_rca(
    incident_id: str,
    source: str = Query("llm", pattern="^(llm|baseline|any)$"),
    db: Session = Depends(get_db),
):
    query = db.query(RCAArtifact).filter(RCAArtifact.incident_id == incident_id)
    if source == "baseline":
        query = query.filter(RCAArtifact.llm_model == "baseline-rules")
    elif source == "llm":
        query = query.filter(RCAArtifact.llm_model != "baseline-rules")

    artifact = query.order_by(RCAArtifact.timestamp.desc()).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="RCA artifact not found")

    return {
        "incident_id": artifact.incident_id,
        "hypotheses": artifact.hypotheses,
        "confidence_scores": artifact.confidence_scores,
        "evidence": artifact.evidence,
        "llm_model": artifact.llm_model,
        "timestamp": artifact.timestamp.isoformat(),
    }


@app.get("/integrations/servicenow/incidents")
def get_servicenow_incidents():
    return _load_fixture("servicenow_incidents.json")


@app.get("/integrations/jira/issues")
def get_jira_issues():
    return _load_fixture("jira_issues.json")


@app.post("/integrations/servicenow/webhook")
def ingest_servicenow_webhook(payload: dict[str, Any], _: None = Depends(require_api_token)):
    _append_integration_event("servicenow", payload)
    return {"status": "received", "source": "servicenow"}


@app.post("/integrations/jira/webhook")
def ingest_jira_webhook(payload: dict[str, Any], _: None = Depends(require_api_token)):
    _append_integration_event("jira", payload)
    return {"status": "received", "source": "jira"}


@app.get("/metrics/overview")
def get_metrics_overview(db: Session = Depends(get_db), _: None = Depends(require_api_token)):
    alert_count = db.query(Alert).count()
    incident_count = db.query(Incident).count()
    rca_count = db.query(RCAArtifact).count()

    incidents = db.query(Incident).all()
    avg_alerts = (
        sum(len(item.related_alert_ids or []) for item in incidents) / len(incidents)
        if incidents
        else 0.0
    )

    return {
        "counts": {
            "alerts": alert_count,
            "incidents": incident_count,
            "rca_artifacts": rca_count,
        },
        "kpis": {
            "avg_alerts_per_incident": round(avg_alerts, 2),
        },
        "test_results": _load_metrics_file(settings.test_results_path),
        "evaluation_results": _load_metrics_file(settings.evaluation_results_path),
    }
