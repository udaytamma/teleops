"""FastAPI app for TeleOps."""

from __future__ import annotations

import hashlib
import json
import re
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from teleops.config import logger, settings
from teleops.data_gen.generator import ScenarioConfig, generate_scenario
from teleops.db import SessionLocal
from teleops.incident_corr.correlator import correlate_alerts
from teleops.init_db import init_db
from teleops.llm.rca import baseline_rca, llm_rca
from teleops.models import Alert, Incident, RCAArtifact
from teleops.rag.index import get_rag_context


# Pydantic models for request validation
class GenerateRequest(BaseModel):
    """Request payload for generating synthetic alerts and incidents."""

    incident_type: Literal[
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
    ] = Field(default="network_degradation", description="Type of incident scenario to generate")
    alert_rate_per_min: int = Field(default=20, ge=1, le=100, description="Alerts per minute to generate")
    duration_min: int = Field(default=10, ge=1, le=60, description="Duration of scenario in minutes")
    noise_rate_per_min: int = Field(default=5, ge=0, le=50, description="Noise alerts per minute")
    seed: int | None = Field(default=42, description="Random seed for reproducibility")


class ServiceNowWebhookPayload(BaseModel):
    """ServiceNow webhook payload structure."""

    sys_id: str = Field(..., description="ServiceNow record sys_id")
    number: str = Field(..., description="Incident number (e.g., INC0012345)")
    short_description: str = Field(..., description="Brief incident description")
    priority: int = Field(default=3, ge=1, le=5, description="Priority 1-5 (1=Critical)")
    state: str = Field(default="New", description="Incident state")


class JiraWebhookPayload(BaseModel):
    """Jira webhook payload structure."""

    issue_key: str = Field(..., description="Jira issue key (e.g., OPS-123)")
    summary: str = Field(..., description="Issue summary")
    priority: str = Field(default="Medium", description="Issue priority")
    status: str = Field(default="Open", description="Issue status")


class ReviewRequest(BaseModel):
    """Request payload for reviewing an RCA hypothesis."""

    decision: Literal["accepted", "rejected"] = Field(..., description="Accept or reject the RCA hypothesis")
    reviewed_by: str = Field(..., min_length=1, max_length=128, description="Name or ID of the reviewer")
    notes: str | None = Field(default=None, description="Optional review notes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized")
    yield


app = FastAPI(
    title="TeleOps API",
    description="AI-powered root cause analysis platform for MSP/Telco network operations",
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)

# CORS middleware - configurable origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _extract_token(authorization: str | None, x_api_key: str | None) -> str | None:
    if x_api_key:
        return x_api_key.strip()
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def require_api_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    if not settings.api_token:
        return
    token = _extract_token(authorization, x_api_key)
    if token != settings.api_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_admin_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    if not settings.admin_token:
        return
    token = _extract_token(authorization, x_api_key)
    if token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_metrics_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    if not settings.metrics_token:
        return
    token = _extract_token(authorization, x_api_key)
    if token != settings.metrics_token:
        raise HTTPException(status_code=401, detail="Unauthorized")


def require_tenant_id(tenant_id: str | None = Header(default=None, alias="X-Tenant-Id")) -> str | None:
    if settings.require_tenant_id and not tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-Id header required")
    return tenant_id


def _tenant_alias(tenant_id: str | None) -> str | None:
    if not tenant_id:
        return None
    digest = hashlib.sha256(tenant_id.encode("utf-8")).hexdigest()[:8]
    return f"tenant-{digest}"


def _redact_text(value: str, tenant_id: str | None = None) -> str:
    redacted = IP_RE.sub("[REDACTED_IP]", value)
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", redacted)
    if tenant_id:
        redacted = redacted.replace(tenant_id, _tenant_alias(tenant_id) or "")
    return redacted


def _redact_obj(value: Any, tenant_id: str | None = None) -> Any:
    if isinstance(value, str):
        return _redact_text(value, tenant_id=tenant_id)
    if isinstance(value, list):
        return [_redact_obj(item, tenant_id=tenant_id) for item in value]
    if isinstance(value, dict):
        return {k: _redact_obj(v, tenant_id=tenant_id) for k, v in value.items()}
    return value


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def alert_to_dict(alert: Alert, include_raw: bool = False, redact: bool = False) -> dict[str, Any]:
    data = {
        "id": alert.id,
        "timestamp": alert.timestamp.isoformat(),
        "source_system": alert.source_system,
        "host": alert.host,
        "service": alert.service,
        "severity": alert.severity,
        "alert_type": alert.alert_type,
        "message": alert.message,
        "tags": alert.tags,
        "tenant_id": alert.tenant_id,
    }
    if include_raw:
        data["raw_payload"] = alert.raw_payload
    if redact:
        data = _redact_obj(data, tenant_id=alert.tenant_id)
    return data


def incident_to_dict(incident: Incident, redact: bool = False) -> dict[str, Any]:
    data = {
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
    if redact:
        data = _redact_obj(data, tenant_id=incident.tenant_id)
    return data


def _load_fixture(name: str) -> dict[str, Any]:
    fixture_dir = Path(settings.integrations_fixtures_dir)
    path = fixture_dir / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fixture not found")
    return json.loads(path.read_text(encoding="utf-8"))


def _rotate_log_if_needed(log_path: Path, max_bytes: int, backup_count: int) -> None:
    """Size-based log rotation shared by integration and audit logs."""
    if not log_path.exists():
        return
    if log_path.stat().st_size < max_bytes:
        return

    for idx in range(backup_count, 0, -1):
        rotated = log_path.with_name(f"{log_path.name}.{idx}")
        if rotated.exists():
            if idx == backup_count:
                rotated.unlink(missing_ok=True)
            else:
                rotated.rename(log_path.with_name(f"{log_path.name}.{idx + 1}"))

    log_path.rename(log_path.with_name(f"{log_path.name}.1"))


def _append_integration_event(source: str, payload: dict[str, Any]) -> None:
    log_path = Path(settings.integrations_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_log_if_needed(
        log_path,
        max_bytes=settings.integration_log_max_bytes,
        backup_count=settings.integration_log_backup_count,
    )
    event = {
        "received_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "payload": payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


AUDIT_LOG_PATH = Path(settings.audit_log_path)


def _append_audit_event(event: dict[str, Any]) -> None:
    """Append a review event to the audit log with size-based rotation."""
    log_path = AUDIT_LOG_PATH
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _rotate_log_if_needed(
        log_path,
        max_bytes=settings.audit_log_max_bytes,
        backup_count=settings.audit_log_backup_count,
    )
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def _load_audit_events(
    incident_id: str | None = None,
    decision: str | None = None,
    reviewer: str | None = None,
) -> list[dict[str, Any]]:
    """Load audit events with optional filters."""
    log_path = AUDIT_LOG_PATH
    if not log_path.exists():
        return []
    events = []
    with log_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            if incident_id and event.get("incident_id") != incident_id:
                continue
            if decision and event.get("decision") != decision:
                continue
            if reviewer and event.get("reviewed_by") != reviewer:
                continue
            events.append(event)
    return events


def _load_metrics_file(path_str: str) -> dict[str, Any] | None:
    path = Path(path_str)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


@app.post("/generate")
def generate_alerts(
    payload: GenerateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    logger.info(f"Generating scenario: type={payload.incident_type}, duration={payload.duration_min}min")

    config = ScenarioConfig(
        incident_type=payload.incident_type,
        alert_rate_per_min=payload.alert_rate_per_min,
        duration_min=payload.duration_min,
        noise_rate_per_min=payload.noise_rate_per_min,
        seed=payload.seed,
    )
    alerts, ground_truth = generate_scenario(config)

    alert_models = []
    for alert in alerts:
        if tenant_id:
            alert["tenant_id"] = tenant_id
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

    logger.info(f"Generated {len(alert_models)} alerts, {len(incidents)} incidents")

    return {
        "alerts_inserted": len(alert_models),
        "incidents_created": [incident_to_dict(i) for i in incidents],
        "ground_truth": ground_truth.__dict__,
    }


@app.get("/alerts")
def list_alerts(
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
    include_raw: bool = Query(False),
):
    query = db.query(Alert)
    if tenant_id:
        query = query.filter(Alert.tenant_id == tenant_id)
    alerts = query.all()
    return [alert_to_dict(alert, include_raw=include_raw) for alert in alerts]


@app.get("/incidents")
def list_incidents(
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    query = db.query(Incident)
    if tenant_id:
        query = query.filter(Incident.tenant_id == tenant_id)
    incidents = query.all()
    return [incident_to_dict(incident) for incident in incidents]


@app.get("/incidents/{incident_id}/alerts")
def list_incident_alerts(
    incident_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
    include_raw: bool = Query(False),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if tenant_id and incident.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not incident.related_alert_ids:
        return []
    alerts = db.query(Alert).filter(Alert.id.in_(incident.related_alert_ids)).all()
    return [alert_to_dict(alert, include_raw=include_raw) for alert in alerts]


@app.post("/reset")
def reset_data(
    db: Session = Depends(get_db),
    _: None = Depends(require_admin_token),
):
    logger.info("Resetting all data")
    db.query(RCAArtifact).delete()
    db.query(Incident).delete()
    db.query(Alert).delete()
    db.commit()
    return {"status": "ok"}


@app.post("/rca/{incident_id}/baseline")
def generate_baseline_rca(
    incident_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if tenant_id and incident.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Incident not found")

    logger.info(f"Generating baseline RCA for incident {incident_id}")

    # Fetch alerts for pattern matching
    alerts = db.query(Alert).filter(Alert.id.in_(incident.related_alert_ids or [])).all()
    alerts_dicts = [alert_to_dict(alert, redact=True) for alert in alerts]

    t0 = time.perf_counter()
    result = baseline_rca(incident.summary, alerts_dicts)
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)

    artifact = RCAArtifact(
        incident_id=incident.id,
        hypotheses=result["hypotheses"],
        evidence=_redact_obj(result["evidence"], tenant_id=incident.tenant_id),
        confidence_scores=result["confidence_scores"],
        llm_model=result["model"],
        duration_ms=duration_ms,
    )
    db.add(artifact)
    db.commit()

    result["duration_ms"] = duration_ms
    result["artifact_id"] = artifact.id
    logger.info(f"Baseline RCA complete in {duration_ms}ms: hypothesis={result['hypotheses'][0][:50]}...")
    return result


@app.post("/rca/{incident_id}/llm")
def generate_llm_rca(
    incident_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    if tenant_id and incident.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Incident not found")

    logger.info(f"Generating LLM RCA for incident {incident_id}")

    alerts = db.query(Alert).filter(Alert.id.in_(incident.related_alert_ids)).all()
    incident_dict = incident_to_dict(incident, redact=True)
    alerts_dicts = [alert_to_dict(alert, redact=True) for alert in alerts]

    alert_types = sorted({alert.alert_type for alert in alerts if alert.alert_type})
    hosts = sorted({alert.host for alert in alerts if alert.host})
    severities = sorted({alert.severity for alert in alerts if alert.severity})
    rag_query = (
        f"{incident.summary} | "
        f"alerts: {', '.join(alert_types[:8])} | "
        f"hosts: {', '.join(hosts[:5])} | "
        f"severity: {', '.join(severities)} | "
        f"count: {len(alerts)}"
    )
    redacted_rag_query = _redact_obj(rag_query, tenant_id=incident.tenant_id)
    try:
        t0 = time.perf_counter()
        rag_context = get_rag_context(rag_query)
        redacted_rag_context = _redact_obj(rag_context, tenant_id=incident.tenant_id)
        result = llm_rca(incident_dict, alerts_dicts, redacted_rag_context)
        duration_ms = round((time.perf_counter() - t0) * 1000, 2)
    except Exception as exc:
        logger.error(f"LLM/RAG error for incident {incident_id}: {exc}")
        raise HTTPException(status_code=502, detail=f"LLM/RAG error: {exc}") from exc

    # Store evidence for evaluation, traceability, and LLM Trace UI
    artifact = RCAArtifact(
        incident_id=incident.id,
        hypotheses=result.get("hypotheses", []),
        evidence=_redact_obj(
            {
                "llm_request": {
                    "incident": incident_dict,
                    "alerts_sample": alerts_dicts[:20],
                    "rag_context": redacted_rag_context,
                },
                "llm_response": result,
                "llm_evidence": result.get("evidence", {}),
                "rag_query": redacted_rag_query,
                "alerts_count": len(alerts_dicts),
                "rag_chunks_used": len(redacted_rag_context) if isinstance(redacted_rag_context, list) else 1,
            },
            tenant_id=incident.tenant_id,
        ),
        confidence_scores=result.get("confidence_scores", {}),
        llm_model=result.get("model", "unknown"),
        duration_ms=duration_ms,
    )
    db.add(artifact)
    db.commit()

    result["duration_ms"] = duration_ms
    result["artifact_id"] = artifact.id
    logger.info(f"LLM RCA complete for incident {incident_id} in {duration_ms}ms")
    return result


@app.get("/rca/{incident_id}/latest")
def get_latest_rca(
    incident_id: str,
    source: str = Query("llm", pattern="^(llm|baseline|any)$"),
    status_filter: str | None = Query(None, alias="status", pattern="^(pending_review|accepted|rejected)$"),
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    query = db.query(RCAArtifact).filter(RCAArtifact.incident_id == incident_id)
    if source == "baseline":
        query = query.filter(RCAArtifact.llm_model == "baseline-rules")
    elif source == "llm":
        query = query.filter(RCAArtifact.llm_model != "baseline-rules")
    if status_filter:
        query = query.filter(RCAArtifact.status == status_filter)

    artifact = query.order_by(RCAArtifact.timestamp.desc()).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="RCA artifact not found")

    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if tenant_id and incident and incident.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="RCA artifact not found")

    return {
        "incident_id": artifact.incident_id,
        "hypotheses": artifact.hypotheses,
        "confidence_scores": artifact.confidence_scores,
        "evidence": artifact.evidence,
        "llm_model": artifact.llm_model,
        "timestamp": artifact.timestamp.isoformat(),
        "duration_ms": artifact.duration_ms,
        "status": artifact.status,
        "reviewed_by": artifact.reviewed_by,
        "reviewed_at": artifact.reviewed_at.isoformat() if artifact.reviewed_at else None,
    }


@app.get("/integrations/servicenow/incidents")
def get_servicenow_incidents(
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    return _load_fixture("servicenow_incidents.json")


@app.get("/integrations/jira/issues")
def get_jira_issues(
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    return _load_fixture("jira_issues.json")


@app.post("/integrations/servicenow/webhook")
def ingest_servicenow_webhook(
    payload: ServiceNowWebhookPayload,
    _: None = Depends(require_admin_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    logger.info(f"ServiceNow webhook received: {payload.number}")
    _append_integration_event("servicenow", payload.model_dump())
    return {"status": "received", "source": "servicenow"}


@app.post("/integrations/jira/webhook")
def ingest_jira_webhook(
    payload: JiraWebhookPayload,
    _: None = Depends(require_admin_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    logger.info(f"Jira webhook received: {payload.issue_key}")
    _append_integration_event("jira", payload.model_dump())
    return {"status": "received", "source": "jira"}


@app.get("/metrics/overview")
def get_metrics_overview(
    db: Session = Depends(get_db),
    _: None = Depends(require_metrics_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    alert_query = db.query(Alert)
    incident_query = db.query(Incident)
    rca_query = db.query(RCAArtifact)
    if tenant_id:
        alert_query = alert_query.filter(Alert.tenant_id == tenant_id)
        incident_query = incident_query.filter(Incident.tenant_id == tenant_id)
        rca_query = rca_query.join(Incident, RCAArtifact.incident_id == Incident.id).filter(
            Incident.tenant_id == tenant_id
        )

    alert_count = alert_query.count()
    incident_count = incident_query.count()
    rca_count = rca_query.count()

    incidents = incident_query.all()
    avg_alerts = (
        sum(len(item.related_alert_ids or []) for item in incidents) / len(incidents)
        if incidents
        else 0.0
    )

    # Human review KPIs
    all_artifacts = rca_query.all()
    pending = sum(1 for a in all_artifacts if getattr(a, "status", None) == "pending_review")
    accepted = sum(1 for a in all_artifacts if getattr(a, "status", None) == "accepted")
    rejected = sum(1 for a in all_artifacts if getattr(a, "status", None) == "rejected")
    reviewed_total = accepted + rejected

    # Time-to-context metrics
    manual_triage_estimate_min = 25  # Industry benchmark for telecom NOC
    baseline_durations = [
        a.duration_ms for a in all_artifacts
        if getattr(a, "duration_ms", None) is not None and a.llm_model == "baseline-rules"
    ]
    llm_durations = [
        a.duration_ms for a in all_artifacts
        if getattr(a, "duration_ms", None) is not None and a.llm_model != "baseline-rules"
    ]
    baseline_median_ms = round(sorted(baseline_durations)[len(baseline_durations) // 2], 1) if baseline_durations else None
    llm_median_ms = round(sorted(llm_durations)[len(llm_durations) // 2], 1) if llm_durations else None

    # Improvement factor: manual minutes -> LLM milliseconds
    improvement_factor = None
    compare_ms = llm_median_ms or baseline_median_ms
    if compare_ms and compare_ms > 0:
        improvement_factor = round((manual_triage_estimate_min * 60 * 1000) / compare_ms)

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
        "human_review": {
            "total_artifacts": len(all_artifacts),
            "pending_review": pending,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": round(accepted / reviewed_total, 3) if reviewed_total > 0 else None,
        },
        "time_to_context": {
            "baseline_median_ms": baseline_median_ms,
            "llm_median_ms": llm_median_ms,
            "manual_estimate_min": manual_triage_estimate_min,
            "improvement_factor": improvement_factor,
        },
    }


@app.post("/rca/{artifact_id}/review")
def review_rca_artifact(
    artifact_id: str,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_api_token),
    tenant_id: str | None = Depends(require_tenant_id),
):
    """Accept or reject an RCA hypothesis with audit trail."""
    artifact = db.query(RCAArtifact).filter(RCAArtifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="RCA artifact not found")

    # Prevent re-review: each artifact can only be reviewed once
    if artifact.status != "pending_review":
        raise HTTPException(
            status_code=409,
            detail=f"Artifact already reviewed with decision: {artifact.status}",
        )

    # Enforce tenant isolation via the artifact's parent incident
    if tenant_id:
        incident = db.query(Incident).filter(Incident.id == artifact.incident_id).first()
        if not incident or incident.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="RCA artifact not found")

    now = datetime.now(timezone.utc)
    artifact.status = payload.decision
    artifact.reviewed_by = payload.reviewed_by
    artifact.reviewed_at = now
    db.commit()

    _append_audit_event({
        "action": "rca_review",
        "artifact_id": artifact_id,
        "incident_id": artifact.incident_id,
        "decision": payload.decision,
        "reviewed_by": payload.reviewed_by,
        "notes": payload.notes,
        "llm_model": artifact.llm_model,
        "hypotheses": artifact.hypotheses,
    })

    logger.info(f"RCA artifact {artifact_id} {payload.decision} by {payload.reviewed_by}")
    return {
        "artifact_id": artifact_id,
        "status": payload.decision,
        "reviewed_by": payload.reviewed_by,
        "reviewed_at": now.isoformat(),
    }


@app.get("/audit/rca")
def get_rca_audit_log(
    incident_id: str | None = Query(None),
    decision: str | None = Query(None, pattern="^(accepted|rejected)$"),
    reviewer: str | None = Query(None),
    _: None = Depends(require_metrics_token),
    tenant_id: str | None = Depends(require_tenant_id),
    db: Session = Depends(get_db),
):
    """Retrieve RCA review audit trail with optional filters."""
    events = _load_audit_events(
        incident_id=incident_id,
        decision=decision,
        reviewer=reviewer,
    )

    # Enforce tenant isolation: filter audit events to incidents belonging to this tenant
    if tenant_id:
        tenant_incident_ids = {
            i.id for i in db.query(Incident.id).filter(Incident.tenant_id == tenant_id).all()
        }
        events = [e for e in events if e.get("incident_id") in tenant_incident_ids]

    return {"events": events, "total": len(events)}


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "app": settings.app_name, "environment": settings.environment}
