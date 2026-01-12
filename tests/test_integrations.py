import json

from teleops.config import settings


def test_integration_fixtures_available(client):
    resp = client.get("/integrations/servicenow/incidents")
    assert resp.status_code == 200
    payload = resp.json()
    assert "records" in payload
    assert len(payload["records"]) >= 1

    resp = client.get("/integrations/jira/issues")
    assert resp.status_code == 200
    payload = resp.json()
    assert "issues" in payload
    assert len(payload["issues"]) >= 1


def test_integration_webhook_logging(client, tmp_path, monkeypatch):
    log_path = tmp_path / "integration_events.jsonl"
    monkeypatch.setattr(settings, "integrations_log_path", str(log_path))

    # Use valid ServiceNow webhook payload with required fields
    payload = {
        "sys_id": "abc123",
        "number": "INC0001",
        "short_description": "Webhook test",
        "priority": 3,
        "state": "New",
    }
    resp = client.post("/integrations/servicenow/webhook", json=payload)
    assert resp.status_code == 200

    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["source"] == "servicenow"
    assert event["payload"]["number"] == "INC0001"


def test_api_token_enforced(client, monkeypatch):
    monkeypatch.setattr(settings, "api_token", "secret-token")
    # Use valid payload to ensure we're testing auth, not validation
    payload = {
        "sys_id": "abc123",
        "number": "INC002",
        "short_description": "Test",
    }
    resp = client.post("/integrations/servicenow/webhook", json=payload)
    assert resp.status_code == 401
