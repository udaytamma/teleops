"""Rule-based incident correlation."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from teleops.models import Alert, Incident


def correlate_alerts(
    session: Session,
    window_minutes: int = 15,
    min_alerts: int = 10,
    alert_ids: list[str] | None = None,
) -> list[Incident]:
    query = session.query(Alert)
    if alert_ids:
        query = query.filter(Alert.id.in_(alert_ids))
    alerts = query.all()
    if not alerts:
        return []

    alerts_by_tag: dict[str, list[Alert]] = defaultdict(list)
    for alert in alerts:
        incident_tag = alert.tags.get("incident", "unknown") if alert.tags else "unknown"
        alerts_by_tag[incident_tag].append(alert)

    incidents: list[Incident] = []
    for tag, tagged_alerts in alerts_by_tag.items():
        if tag == "noise":
            continue
        if len(tagged_alerts) < min_alerts:
            continue

        tagged_alerts.sort(key=lambda a: a.timestamp)
        start_time = tagged_alerts[0].timestamp
        end_time = tagged_alerts[-1].timestamp
        if (end_time - start_time).total_seconds() > window_minutes * 60:
            # If alerts are too spread out, skip for MVP.
            continue

        incident = Incident(
            start_time=start_time,
            end_time=end_time,
            severity="critical",
            status="open",
            related_alert_ids=[a.id for a in tagged_alerts],
            summary=f"Correlated incident for tag: {tag}",
            suspected_root_cause=None,
            impact_scope="network",
            owner=None,
            created_by="correlator",
            tenant_id=tagged_alerts[0].tenant_id,
        )
        incidents.append(incident)

    for incident in incidents:
        session.add(incident)
    session.commit()

    return incidents
