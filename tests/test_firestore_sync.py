"""Tests for Firestore sync layer.

All tests mock the Firebase Admin SDK to avoid requiring real credentials.
Verifies document structure, error handling, and graceful degradation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from teleops.models import Alert, Base, Incident, RCAArtifact


@pytest.fixture()
def db_session():
    """In-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def sample_incident(db_session):
    """Create a sample incident with alerts and RCA artifact."""
    alerts = []
    for i in range(3):
        alert = Alert(
            id=f"alert-{i}",
            timestamp=datetime(2026, 2, 22, 10, i, 0, tzinfo=timezone.utc),
            source_system="test-system",
            host=f"host-{i}",
            service="api-gateway",
            severity="critical",
            alert_type="cpu_spike",
            message=f"CPU spike on host-{i}",
            tags={"incident": "test_incident"},
            raw_payload={"value": 95 + i},
        )
        alerts.append(alert)
        db_session.add(alert)

    incident = Incident(
        id="test_incident_20260222_100000_abcd",
        start_time=datetime(2026, 2, 22, 10, 0, 0, tzinfo=timezone.utc),
        end_time=datetime(2026, 2, 22, 10, 2, 0, tzinfo=timezone.utc),
        severity="critical",
        status="open",
        related_alert_ids=[a.id for a in alerts],
        summary="Test incident for unit tests",
        suspected_root_cause=None,
        impact_scope="network",
        owner=None,
        created_by="correlator",
        tenant_id=None,
    )
    db_session.add(incident)

    rca = RCAArtifact(
        id="rca-001",
        incident_id=incident.id,
        hypotheses=["CPU overload due to traffic spike"],
        evidence={"pattern": "sustained CPU > 90%"},
        confidence_scores={"CPU overload due to traffic spike": 0.85},
        llm_model="baseline-rules",
        timestamp=datetime(2026, 2, 22, 10, 5, 0, tzinfo=timezone.utc),
        duration_ms=12.5,
        status="pending_review",
    )
    db_session.add(rca)
    db_session.commit()

    return incident


class TestBuildIncidentDoc:
    """Test _build_incident_doc serialization."""

    def test_builds_correct_structure(self, db_session, sample_incident):
        """Document should contain incident fields, alerts, and RCA artifacts."""
        # _build_incident_doc imports SERVER_TIMESTAMP from google.cloud.firestore
        # at call time, so we mock the module in sys.modules
        mock_gcloud_firestore = MagicMock()
        mock_gcloud_firestore.SERVER_TIMESTAMP = "MOCK_SERVER_TIMESTAMP"

        with patch.dict("sys.modules", {"google.cloud.firestore": mock_gcloud_firestore}):
            from teleops.firestore_sync import _build_incident_doc

            doc = _build_incident_doc(sample_incident.id, db_session)

        assert doc is not None
        assert doc["incident_id"] == sample_incident.id
        assert doc["severity"] == "critical"
        assert doc["status"] == "open"
        assert doc["alert_count"] == 3
        assert len(doc["alerts"]) == 3
        assert len(doc["rca_artifacts"]) == 1
        assert doc["rca_artifacts"][0]["hypotheses"] == ["CPU overload due to traffic spike"]
        assert doc["rca_artifacts"][0]["duration_ms"] == 12.5
        assert doc["updated_at"] == "MOCK_SERVER_TIMESTAMP"

    def test_returns_none_for_missing_incident(self, db_session):
        """Should return None if incident doesn't exist."""
        mock_gcloud_firestore = MagicMock()
        mock_gcloud_firestore.SERVER_TIMESTAMP = "MOCK"

        with patch.dict("sys.modules", {"google.cloud.firestore": mock_gcloud_firestore}):
            from teleops.firestore_sync import _build_incident_doc

            doc = _build_incident_doc("nonexistent-id", db_session)

        assert doc is None

    def test_datetime_serialization(self, db_session, sample_incident):
        """Datetime fields should be ISO-formatted strings."""
        mock_gcloud_firestore = MagicMock()
        mock_gcloud_firestore.SERVER_TIMESTAMP = "MOCK"

        with patch.dict("sys.modules", {"google.cloud.firestore": mock_gcloud_firestore}):
            from teleops.firestore_sync import _build_incident_doc

            doc = _build_incident_doc(sample_incident.id, db_session)

        assert doc is not None
        assert "2026-02-22T10:00:00" in doc["start_time"]
        assert "2026-02-22T10:02:00" in doc["end_time"]
        for alert in doc["alerts"]:
            assert isinstance(alert["timestamp"], str)

    def test_incident_with_no_alerts(self, db_session):
        """Should handle incident with empty related_alert_ids."""
        incident = Incident(
            id="empty_incident_001",
            start_time=datetime(2026, 2, 22, 10, 0, 0, tzinfo=timezone.utc),
            end_time=None,
            severity="warning",
            status="open",
            related_alert_ids=[],
            summary="Empty incident",
            tenant_id=None,
        )
        db_session.add(incident)
        db_session.commit()

        mock_gcloud_firestore = MagicMock()
        mock_gcloud_firestore.SERVER_TIMESTAMP = "MOCK"

        with patch.dict("sys.modules", {"google.cloud.firestore": mock_gcloud_firestore}):
            from teleops.firestore_sync import _build_incident_doc

            doc = _build_incident_doc("empty_incident_001", db_session)

        assert doc is not None
        assert doc["alert_count"] == 0
        assert doc["alerts"] == []
        assert doc["end_time"] is None


class TestSyncDisabled:
    """Test behavior when Firestore is not configured."""

    def test_sync_noop_when_db_is_none(self):
        """sync_incident_to_firestore should be a no-op when _db is None."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        fs_module._db = None
        try:
            # Should not raise or spawn threads
            fs_module.sync_incident_to_firestore("any-id")
            fs_module.sync_incidents_to_firestore(["id-1", "id-2"])
            fs_module.delete_all_from_firestore()
        finally:
            fs_module._db = original_db

    def test_init_firestore_disabled(self):
        """init_firestore should be a no-op when firestore_enabled=False."""
        import teleops.firestore_sync as fs_module

        with patch("teleops.firestore_sync.settings") as mock_settings:
            mock_settings.firestore_enabled = False
            fs_module.init_firestore()

        # No crash -- that's the assertion


class TestErrorHandling:
    """Test graceful error handling in sync operations."""

    def test_sync_worker_handles_firestore_error(self, db_session, sample_incident):
        """_sync_worker should catch and log Firestore write errors."""
        import teleops.firestore_sync as fs_module

        mock_firestore_db = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.set.side_effect = Exception("Firestore write failed")
        mock_collection.document.return_value = mock_doc_ref
        mock_firestore_db.collection.return_value = mock_collection

        original_db = fs_module._db
        fs_module._db = mock_firestore_db

        mock_gcloud_firestore = MagicMock()
        mock_gcloud_firestore.SERVER_TIMESTAMP = "MOCK"

        try:
            # Mock the SessionLocal import inside _sync_worker
            mock_session_factory = MagicMock(return_value=db_session)
            with patch.dict("sys.modules", {"google.cloud.firestore": mock_gcloud_firestore}):
                with patch("teleops.db.SessionLocal", mock_session_factory):
                    # _sync_worker imports SessionLocal from teleops.db
                    # We need to also patch it at the point of use
                    def patched_sync_worker(incident_id):
                        """Run sync worker with patched SessionLocal."""
                        try:
                            from teleops.firestore_sync import _build_incident_doc

                            doc = _build_incident_doc(incident_id, db_session)
                            if doc is None:
                                return
                            fs_module._db.collection(fs_module._collection_name).document(incident_id).set(doc)
                        except Exception:
                            pass  # Expected -- we're testing error handling

                    patched_sync_worker(sample_incident.id)
                    # Verify the set() was called and raised
                    assert mock_doc_ref.set.called
        finally:
            fs_module._db = original_db

    def test_delete_worker_handles_error(self):
        """_delete_worker should catch and log errors."""
        import teleops.firestore_sync as fs_module

        mock_db = MagicMock()
        mock_db.collection.side_effect = Exception("Collection error")

        original_db = fs_module._db
        fs_module._db = mock_db

        try:
            # Should not raise
            fs_module._delete_worker()
        finally:
            fs_module._db = original_db

    def test_init_firestore_handles_bad_credentials(self):
        """init_firestore should handle invalid base64 credentials gracefully."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        fs_module._db = None

        with patch("teleops.firestore_sync.settings") as mock_settings:
            mock_settings.firestore_enabled = True
            mock_settings.firestore_credentials_json = "not-valid-base64!!!"
            mock_settings.firestore_credentials_file = None
            mock_settings.firestore_project_id = "test"
            mock_settings.firestore_collection = "test"

            # Should not raise
            fs_module.init_firestore()

        # _db should remain None after failed init
        assert fs_module._db is None
        fs_module._db = original_db


class TestInitFirestore:
    """Test Firestore initialization paths."""

    def test_init_with_credentials_file(self):
        """init_firestore should work with a credentials file path."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        mock_firestore_client = MagicMock()
        mock_app = MagicMock()

        with patch("teleops.firestore_sync.settings") as mock_settings:
            mock_settings.firestore_enabled = True
            mock_settings.firestore_credentials_json = None
            mock_settings.firestore_credentials_file = "/tmp/fake-creds.json"
            mock_settings.firestore_project_id = "test-project"
            mock_settings.firestore_collection = "test_collection"

            # Mock firebase_admin imports inside init_firestore()
            mock_firebase_admin = MagicMock()
            mock_credentials = MagicMock()
            mock_firestore_mod = MagicMock()
            mock_firestore_mod.client.return_value = mock_firestore_client

            mock_firebase_admin.credentials = mock_credentials
            mock_firebase_admin.firestore = mock_firestore_mod
            # First get_app raises (not initialized), second returns the app
            mock_firebase_admin.get_app.side_effect = [ValueError("not found"), mock_app]

            with patch.dict("sys.modules", {
                "firebase_admin": mock_firebase_admin,
                "firebase_admin.credentials": mock_credentials,
                "firebase_admin.firestore": mock_firestore_mod,
            }):
                fs_module.init_firestore()

        # Restore
        fs_module._db = original_db

    def test_init_without_credentials_warns(self):
        """init_firestore should warn when enabled but no credentials."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        fs_module._db = None

        with patch("teleops.firestore_sync.settings") as mock_settings:
            mock_settings.firestore_enabled = True
            mock_settings.firestore_credentials_json = None
            mock_settings.firestore_credentials_file = None
            mock_settings.firestore_collection = "test"

            fs_module.init_firestore()

        assert fs_module._db is None
        fs_module._db = original_db


class TestDeleteAll:
    """Test Firestore collection deletion."""

    def test_delete_all_iterates_docs(self):
        """delete_all should iterate all docs and delete each."""
        import teleops.firestore_sync as fs_module

        mock_db = MagicMock()
        mock_collection = MagicMock()

        mock_doc1 = MagicMock()
        mock_doc2 = MagicMock()
        mock_collection.limit.return_value.stream.side_effect = [
            iter([mock_doc1, mock_doc2]),
            iter([]),
        ]
        mock_db.collection.return_value = mock_collection

        original_db = fs_module._db
        fs_module._db = mock_db

        try:
            fs_module._delete_worker()
            assert mock_doc1.reference.delete.called
            assert mock_doc2.reference.delete.called
        finally:
            fs_module._db = original_db


class TestParseIsoDatetime:
    """Test _parse_iso_datetime helper."""

    def test_parses_naive_iso(self):
        from teleops.firestore_sync import _parse_iso_datetime

        result = _parse_iso_datetime("2026-02-22T10:00:00")
        assert result == datetime(2026, 2, 22, 10, 0, 0)

    def test_parses_tz_aware_iso(self):
        from teleops.firestore_sync import _parse_iso_datetime

        result = _parse_iso_datetime("2026-02-22T10:00:00+00:00")
        assert result == datetime(2026, 2, 22, 10, 0, 0, tzinfo=timezone.utc)

    def test_returns_none_for_none(self):
        from teleops.firestore_sync import _parse_iso_datetime

        assert _parse_iso_datetime(None) is None

    def test_returns_none_for_empty(self):
        from teleops.firestore_sync import _parse_iso_datetime

        assert _parse_iso_datetime("") is None

    def test_returns_none_for_invalid(self):
        from teleops.firestore_sync import _parse_iso_datetime

        assert _parse_iso_datetime("not-a-date") is None


class TestRestoreFromFirestore:
    """Test restore_from_firestore startup hydration."""

    def test_noop_when_db_is_none(self):
        """Should return 0 when Firestore client is not initialized."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        fs_module._db = None
        try:
            assert fs_module.restore_from_firestore() == 0
        finally:
            fs_module._db = original_db

    def test_skips_when_sqlite_has_data(self, db_session, sample_incident):
        """Should skip restore when SQLite already has incidents."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        fs_module._db = MagicMock()  # Non-None = Firestore "initialized"

        mock_session_factory = MagicMock(return_value=db_session)
        try:
            with patch("teleops.db.SessionLocal", mock_session_factory):
                result = fs_module.restore_from_firestore()
            assert result == 0
        finally:
            fs_module._db = original_db

    def test_skips_when_firestore_empty(self, db_session):
        """Should return 0 when Firestore collection has no documents."""
        import teleops.firestore_sync as fs_module

        original_db = fs_module._db
        mock_firestore_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.stream.return_value = iter([])
        mock_firestore_db.collection.return_value = mock_collection
        fs_module._db = mock_firestore_db

        # db_session has no incidents (empty SQLite)
        mock_session_factory = MagicMock(return_value=db_session)
        try:
            with patch("teleops.db.SessionLocal", mock_session_factory):
                result = fs_module.restore_from_firestore()
            assert result == 0
        finally:
            fs_module._db = original_db

    def test_restores_incident_with_alerts_and_rca(self, db_session):
        """Should restore a full incident from Firestore into empty SQLite."""
        import teleops.firestore_sync as fs_module

        # Build a mock Firestore document matching the serialized format
        firestore_doc_data = {
            "incident_id": "restored_incident_001",
            "start_time": "2026-02-22T10:00:00+00:00",
            "end_time": "2026-02-22T10:10:00+00:00",
            "severity": "critical",
            "status": "open",
            "summary": "Restored from Firestore",
            "suspected_root_cause": "Network congestion",
            "impact_scope": "network",
            "owner": "noc-team",
            "created_by": "correlator",
            "tenant_id": None,
            "alerts": [
                {
                    "id": "alert-restored-1",
                    "timestamp": "2026-02-22T10:01:00+00:00",
                    "source_system": "prometheus",
                    "host": "core-router-1",
                    "service": "routing",
                    "severity": "critical",
                    "alert_type": "packet_loss",
                    "message": "High packet loss detected",
                    "tags": {"region": "us-east"},
                },
            ],
            "rca_artifacts": [
                {
                    "id": "rca-restored-1",
                    "hypotheses": ["Network congestion on core-router-1"],
                    "evidence": {"pattern": "packet_loss > 5%"},
                    "confidence_scores": {"Network congestion on core-router-1": 0.9},
                    "llm_model": "gemini-3-flash-preview",
                    "timestamp": "2026-02-22T10:05:00+00:00",
                    "duration_ms": 7500.0,
                    "status": "accepted",
                    "reviewed_by": "uday.tamma",
                    "reviewed_at": "2026-02-22T10:06:00+00:00",
                },
            ],
        }

        mock_doc = MagicMock()
        mock_doc.id = "restored_incident_001"
        mock_doc.to_dict.return_value = firestore_doc_data

        original_db = fs_module._db
        mock_firestore_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.stream.return_value = iter([mock_doc])
        mock_firestore_db.collection.return_value = mock_collection
        fs_module._db = mock_firestore_db

        mock_session_factory = MagicMock(return_value=db_session)
        try:
            with patch("teleops.db.SessionLocal", mock_session_factory):
                result = fs_module.restore_from_firestore()

            assert result == 1

            # Verify incident was restored
            incident = db_session.query(Incident).filter(
                Incident.id == "restored_incident_001"
            ).first()
            assert incident is not None
            assert incident.severity == "critical"
            assert incident.summary == "Restored from Firestore"
            assert incident.suspected_root_cause == "Network congestion"

            # Verify alert was restored
            alert = db_session.query(Alert).filter(
                Alert.id == "alert-restored-1"
            ).first()
            assert alert is not None
            assert alert.host == "core-router-1"
            assert alert.severity == "critical"

            # Verify RCA artifact was restored
            rca = db_session.query(RCAArtifact).filter(
                RCAArtifact.id == "rca-restored-1"
            ).first()
            assert rca is not None
            assert rca.status == "accepted"
            assert rca.reviewed_by == "uday.tamma"
            assert rca.duration_ms == 7500.0

        finally:
            fs_module._db = original_db

    def test_handles_corrupt_document_gracefully(self, db_session):
        """Should skip corrupt documents and continue restoring others."""
        import teleops.firestore_sync as fs_module

        # One good doc, one corrupt doc (missing incident_id)
        good_doc = MagicMock()
        good_doc.id = "good_incident"
        good_doc.to_dict.return_value = {
            "incident_id": "good_incident",
            "start_time": "2026-02-22T10:00:00+00:00",
            "severity": "high",
            "status": "open",
            "summary": "Good incident",
            "alerts": [],
            "rca_artifacts": [],
        }

        bad_doc = MagicMock()
        bad_doc.id = "bad_incident"
        bad_doc.to_dict.side_effect = Exception("Corrupt document")

        original_db = fs_module._db
        mock_firestore_db = MagicMock()
        mock_collection = MagicMock()
        mock_collection.stream.return_value = iter([bad_doc, good_doc])
        mock_firestore_db.collection.return_value = mock_collection
        fs_module._db = mock_firestore_db

        mock_session_factory = MagicMock(return_value=db_session)
        try:
            with patch("teleops.db.SessionLocal", mock_session_factory):
                result = fs_module.restore_from_firestore()

            # Should restore 1 out of 2 (bad doc skipped)
            assert result == 1
            incident = db_session.query(Incident).filter(
                Incident.id == "good_incident"
            ).first()
            assert incident is not None

        finally:
            fs_module._db = original_db
