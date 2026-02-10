from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from scripts import import_logs
from teleops.models import Alert, Base


def test_import_logs_inserts_records(tmp_path, monkeypatch):
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def _session_factory():
        return testing_session_factory()

    monkeypatch.setattr(import_logs, "SessionLocal", _session_factory)

    sample_file = Path("docs/data_samples/anonymized_alerts.jsonl")
    records = import_logs._load_records(sample_file)
    inserted = import_logs._import_records(records, dry_run=False)

    session = testing_session_factory()
    try:
        count = session.query(Alert).count()
    finally:
        session.close()

    assert inserted == count
    assert count > 0
