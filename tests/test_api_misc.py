def test_alerts_and_reset(client):
    resp = client.post("/generate", json={"alert_rate_per_min": 3, "duration_min": 2, "noise_rate_per_min": 1})
    assert resp.status_code == 200

    alerts = client.get("/alerts")
    assert alerts.status_code == 200
    assert len(alerts.json()) > 0

    reset = client.post("/reset")
    assert reset.status_code == 200
    assert reset.json()["status"] == "ok"

    alerts_after = client.get("/alerts")
    assert alerts_after.status_code == 200
    assert alerts_after.json() == []
