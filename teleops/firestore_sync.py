"""Firestore sync layer for persistent incident storage.

Implements a dual-write + startup-restore pattern: SQLite is the primary
database for all reads/writes; Firestore receives denormalized incident
documents in background threads so data survives Railway's ephemeral
filesystem across deploys.

On startup, if SQLite is empty but Firestore has data, the restore
function hydrates SQLite from Firestore (synchronous, blocking). This
ensures the API never serves empty data after a Railway redeploy.

If Firestore is not configured or encounters errors, the API continues
to operate normally -- all sync operations log warnings but never raise.
"""

from __future__ import annotations

import base64
import json
import logging
import threading
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from teleops.config import settings

logger = logging.getLogger("teleops.firestore")

# Module-level Firestore client -- set by init_firestore()
_db = None
_collection_name: str = settings.firestore_collection


def init_firestore() -> None:
    """Initialize Firebase Admin SDK and Firestore client.

    Supports two credential sources (checked in order):
    1. FIRESTORE_CREDENTIALS_JSON -- base64-encoded service account JSON (Railway/CI)
    2. FIRESTORE_CREDENTIALS_FILE -- path to service account JSON file (local dev)

    Sets module-level ``_db`` on success. Logs a warning and returns
    gracefully if Firestore is not enabled or credentials are missing.
    """
    global _db, _collection_name

    if not settings.firestore_enabled:
        logger.info("Firestore sync disabled (FIRESTORE_ENABLED=false)")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError:
        logger.warning(
            "firebase-admin package not installed -- Firestore sync disabled. "
            "Run: pip install firebase-admin"
        )
        return

    _collection_name = settings.firestore_collection

    try:
        # Prefer base64-encoded JSON (Railway env var)
        if settings.firestore_credentials_json:
            # Strip whitespace/quotes and fix padding (env vars can mangle base64)
            raw = settings.firestore_credentials_json.strip().strip('"').strip("'")
            # Add padding if needed (base64 length must be multiple of 4)
            padding = 4 - len(raw) % 4
            if padding != 4:
                raw += "=" * padding
            cred_json = base64.b64decode(raw)
            cred_dict = json.loads(cred_json)
            cred = credentials.Certificate(cred_dict)
        elif settings.firestore_credentials_file:
            cred = credentials.Certificate(settings.firestore_credentials_file)
        else:
            logger.warning(
                "Firestore enabled but no credentials provided. "
                "Set FIRESTORE_CREDENTIALS_JSON or FIRESTORE_CREDENTIALS_FILE."
            )
            return

        # Initialize Firebase app (avoid duplicate initialization)
        app_name = "teleops-firestore"
        try:
            firebase_admin.get_app(app_name)
        except ValueError:
            firebase_admin.initialize_app(
                cred,
                options={"projectId": settings.firestore_project_id} if settings.firestore_project_id else None,
                name=app_name,
            )

        _db = firestore.client(app=firebase_admin.get_app(app_name))
        logger.info(
            f"Firestore initialized: project={settings.firestore_project_id}, "
            f"collection={_collection_name}"
        )
    except Exception:
        logger.exception("Failed to initialize Firestore -- sync disabled")
        _db = None


def _serialize_datetime(value: Any) -> Any:
    """Convert datetime objects to ISO strings for Firestore."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _build_incident_doc(
    incident_id: str,
    db_session: Session,
) -> dict[str, Any] | None:
    """Build a denormalized Firestore document for an incident.

    Fetches the incident, its alerts, and its RCA artifacts from SQLite
    and combines them into a single flat document.
    """
    # Import here to avoid circular imports (models -> config -> firestore_sync)
    from teleops.models import Alert, Incident, RCAArtifact

    incident = db_session.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        logger.warning(f"Incident {incident_id} not found in SQLite -- skipping sync")
        return None

    # Fetch related alerts
    alert_dicts: list[dict[str, Any]] = []
    if incident.related_alert_ids:
        alerts = db_session.query(Alert).filter(
            Alert.id.in_(incident.related_alert_ids)
        ).all()
        for alert in alerts:
            alert_dicts.append({
                "id": alert.id,
                "timestamp": _serialize_datetime(alert.timestamp),
                "source_system": alert.source_system,
                "host": alert.host,
                "service": alert.service,
                "severity": alert.severity,
                "alert_type": alert.alert_type,
                "message": alert.message,
                "tags": alert.tags or {},
            })

    # Fetch RCA artifacts
    rca_dicts: list[dict[str, Any]] = []
    rca_artifacts = db_session.query(RCAArtifact).filter(
        RCAArtifact.incident_id == incident_id
    ).order_by(RCAArtifact.timestamp.asc()).all()
    for rca in rca_artifacts:
        rca_dicts.append({
            "id": rca.id,
            "hypotheses": rca.hypotheses or [],
            "evidence": rca.evidence or {},
            "confidence_scores": rca.confidence_scores or {},
            "llm_model": rca.llm_model,
            "timestamp": _serialize_datetime(rca.timestamp),
            "duration_ms": rca.duration_ms,
            "status": rca.status,
            "reviewed_by": rca.reviewed_by,
            "reviewed_at": _serialize_datetime(rca.reviewed_at),
        })

    from google.cloud.firestore import SERVER_TIMESTAMP

    return {
        "incident_id": incident.id,
        "start_time": _serialize_datetime(incident.start_time),
        "end_time": _serialize_datetime(incident.end_time),
        "severity": incident.severity,
        "status": incident.status,
        "summary": incident.summary,
        "suspected_root_cause": incident.suspected_root_cause,
        "impact_scope": incident.impact_scope,
        "owner": incident.owner,
        "created_by": incident.created_by,
        "tenant_id": incident.tenant_id,
        "alert_count": len(alert_dicts),
        "alerts": alert_dicts,
        "rca_artifacts": rca_dicts,
        "updated_at": SERVER_TIMESTAMP,
    }


def _sync_worker(incident_id: str) -> None:
    """Background worker that syncs a single incident to Firestore.

    Opens a fresh SQLAlchemy session to avoid thread-safety issues
    with the request-scoped session.
    """
    if _db is None:
        return

    try:
        from teleops.db import SessionLocal

        db_session = SessionLocal()
        try:
            doc = _build_incident_doc(incident_id, db_session)
            if doc is None:
                return
            _db.collection(_collection_name).document(incident_id).set(doc)
            logger.info(f"Firestore sync OK: {incident_id}")
        finally:
            db_session.close()
    except Exception:
        logger.exception(f"Firestore sync failed for incident {incident_id}")


def sync_incident_to_firestore(incident_id: str) -> None:
    """Sync a single incident to Firestore in a background thread.

    Safe to call even if Firestore is not configured -- returns immediately.
    """
    if _db is None:
        return

    thread = threading.Thread(
        target=_sync_worker,
        args=(incident_id,),
        daemon=True,
        name=f"firestore-sync-{incident_id[:20]}",
    )
    thread.start()


def sync_incidents_to_firestore(incident_ids: list[str]) -> None:
    """Sync multiple incidents to Firestore.

    Each incident is synced in its own background thread.
    """
    if _db is None:
        return

    for incident_id in incident_ids:
        sync_incident_to_firestore(incident_id)


def _delete_worker() -> None:
    """Background worker that deletes all documents from the Firestore collection."""
    if _db is None:
        return

    try:
        collection_ref = _db.collection(_collection_name)
        # Firestore doesn't have a bulk delete -- iterate in batches
        batch_size = 100
        while True:
            docs = collection_ref.limit(batch_size).stream()
            deleted = 0
            for doc in docs:
                doc.reference.delete()
                deleted += 1
            if deleted < batch_size:
                break
        logger.info(f"Firestore collection '{_collection_name}' cleared")
    except Exception:
        logger.exception("Firestore delete_all failed")


def delete_all_from_firestore() -> None:
    """Delete all documents from the Firestore incidents collection.

    Runs in a background thread. Used by the /reset endpoint.
    """
    if _db is None:
        return

    thread = threading.Thread(
        target=_delete_worker,
        daemon=True,
        name="firestore-delete-all",
    )
    thread.start()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    """Parse an ISO 8601 datetime string back to a datetime object.

    Handles both timezone-aware and naive ISO strings. Returns None
    for None or unparseable values.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse datetime: {value!r}")
        return None


def restore_from_firestore() -> int:
    """Restore incidents, alerts, and RCA artifacts from Firestore into SQLite.

    Called synchronously on startup. Only runs when:
    1. Firestore client is initialized (_db is not None)
    2. SQLite has zero incidents (fresh deploy / wiped filesystem)

    Returns the number of incidents restored (0 if skipped or failed).
    """
    if _db is None:
        return 0

    try:
        from teleops.db import SessionLocal
        from teleops.models import Alert, Incident, RCAArtifact

        db_session = SessionLocal()
        try:
            # Check if SQLite already has data -- skip restore if so
            existing_count = db_session.query(Incident).count()
            if existing_count > 0:
                logger.info(
                    f"SQLite has {existing_count} incidents -- skipping Firestore restore"
                )
                return 0

            # Fetch all documents from Firestore
            docs = _db.collection(_collection_name).stream()
            doc_list = list(docs)

            if not doc_list:
                logger.info("Firestore collection is empty -- nothing to restore")
                return 0

            logger.info(f"Restoring {len(doc_list)} incidents from Firestore...")
            restored = 0

            for doc in doc_list:
                try:
                    data = doc.to_dict()

                    # Restore alerts first (incidents reference them by ID)
                    alert_ids = []
                    for alert_data in data.get("alerts", []):
                        alert = Alert(
                            id=alert_data["id"],
                            timestamp=_parse_iso_datetime(alert_data.get("timestamp")),
                            source_system=alert_data.get("source_system", ""),
                            host=alert_data.get("host", ""),
                            service=alert_data.get("service", ""),
                            severity=alert_data.get("severity", "info"),
                            alert_type=alert_data.get("alert_type", ""),
                            message=alert_data.get("message", ""),
                            tags=alert_data.get("tags", {}),
                            raw_payload={},
                            tenant_id=data.get("tenant_id"),
                        )
                        db_session.merge(alert)  # merge avoids duplicate key errors
                        alert_ids.append(alert_data["id"])

                    # Restore incident
                    incident = Incident(
                        id=data["incident_id"],
                        start_time=_parse_iso_datetime(data.get("start_time")),
                        end_time=_parse_iso_datetime(data.get("end_time")),
                        severity=data.get("severity", "info"),
                        status=data.get("status", "open"),
                        related_alert_ids=alert_ids,
                        summary=data.get("summary", ""),
                        suspected_root_cause=data.get("suspected_root_cause"),
                        impact_scope=data.get("impact_scope"),
                        owner=data.get("owner"),
                        created_by=data.get("created_by", "system"),
                        tenant_id=data.get("tenant_id"),
                    )
                    db_session.merge(incident)

                    # Restore RCA artifacts
                    for rca_data in data.get("rca_artifacts", []):
                        rca = RCAArtifact(
                            id=rca_data["id"],
                            incident_id=data["incident_id"],
                            hypotheses=rca_data.get("hypotheses", []),
                            evidence=rca_data.get("evidence", {}),
                            confidence_scores=rca_data.get("confidence_scores", {}),
                            llm_model=rca_data.get("llm_model", "unknown"),
                            timestamp=_parse_iso_datetime(rca_data.get("timestamp")),
                            duration_ms=rca_data.get("duration_ms"),
                            status=rca_data.get("status", "pending_review"),
                            reviewed_by=rca_data.get("reviewed_by"),
                            reviewed_at=_parse_iso_datetime(rca_data.get("reviewed_at")),
                        )
                        db_session.merge(rca)

                    restored += 1

                except Exception:
                    logger.exception(
                        f"Failed to restore incident {doc.id} -- skipping"
                    )
                    continue

            db_session.commit()
            logger.info(
                f"Firestore restore complete: {restored}/{len(doc_list)} incidents restored"
            )
            return restored

        finally:
            db_session.close()

    except Exception:
        logger.exception("Firestore restore failed -- API will start with empty data")
        return 0
