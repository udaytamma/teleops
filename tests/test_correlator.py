from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from teleops.incident_corr.correlator import correlate_alerts
from teleops.models import Alert, Base


def setup_db():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_correlate_alerts_creates_incident():
    session = setup_db()
    now = datetime.now(timezone.utc)

    for i in range(12):
        alert = Alert(
            timestamp=now + timedelta(minutes=i % 3),
            source_system="net-snmp",
            host="core-router-1",
            service="backbone",
            severity="critical",
            alert_type="packet_loss",
            message="degraded network",
            tags={"incident": "network_degradation"},
            raw_payload={"loss_pct": 10},
            tenant_id="tenant-a",
        )
        session.add(alert)
    session.commit()

    incidents = correlate_alerts(session, window_minutes=15, min_alerts=10)
    assert len(incidents) == 1
    assert incidents[0].summary.startswith("Correlated incident")


def test_correlate_alerts_percentile_noise_filter():
    session = setup_db()
    now = datetime.now(timezone.utc)

    def add_alerts(tag: str, count: int) -> None:
        for i in range(count):
            alert = Alert(
                timestamp=now + timedelta(seconds=i),
                source_system="net-snmp",
                host="core-router-1",
                service="backbone",
                severity="critical",
                alert_type="packet_loss",
                message="degraded network",
                tags={"incident": tag},
                raw_payload={"loss_pct": 10},
                tenant_id="tenant-a",
            )
            session.add(alert)

    # Counts: [4, 10, 12, 30] => p25 ~= 8.5, so tag "low" should be dropped.
    add_alerts("low", 4)
    add_alerts("mid", 10)
    add_alerts("midh", 12)
    add_alerts("high", 30)
    session.commit()

    incidents = correlate_alerts(session, window_minutes=15, min_alerts=1)
    tags = {incident.summary.split(": ", 1)[1] for incident in incidents}

    assert tags == {"mid", "midh", "high"}
