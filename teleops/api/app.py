"""FastAPI app for TeleOps."""

from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

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


@app.post("/generate")
def generate_alerts(payload: dict[str, Any], db: Session = Depends(get_db)):
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


@app.post("/reset")
def reset_data(db: Session = Depends(get_db)):
    db.query(RCAArtifact).delete()
    db.query(Incident).delete()
    db.query(Alert).delete()
    db.commit()
    return {"status": "ok"}


@app.post("/rca/{incident_id}/baseline")
def generate_baseline_rca(incident_id: str, db: Session = Depends(get_db)):
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
def generate_llm_rca(incident_id: str, db: Session = Depends(get_db)):
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
