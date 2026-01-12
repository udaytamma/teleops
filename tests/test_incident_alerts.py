def test_incident_alerts_endpoint(client):
    resp = client.post("/generate", json={"alert_rate_per_min": 5, "duration_min": 3, "noise_rate_per_min": 1})
    assert resp.status_code == 200
    payload = resp.json()
    incidents = payload["incidents_created"]
    assert incidents
    incident_id = incidents[0]["id"]

    alerts_resp = client.get(f"/incidents/{incident_id}/alerts")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) >= 1
