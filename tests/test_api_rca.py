def test_rca_endpoints(client, monkeypatch):
    resp = client.post("/generate", json={"alert_rate_per_min": 5, "duration_min": 3, "noise_rate_per_min": 1})
    assert resp.status_code == 200
    incident_id = resp.json()["incidents_created"][0]["id"]

    baseline = client.post(f"/rca/{incident_id}/baseline")
    assert baseline.status_code == 200
    assert baseline.json()["model"] == "baseline-rules"

    def fake_rag(query):
        return ["context"]

    def fake_llm(incident, alerts, rag_context):
        return {
            "incident_summary": incident["summary"],
            "hypotheses": ["fake"],
            "confidence_scores": {"fake": 0.7},
            "evidence": {"source": "test"},
            "generated_at": "now",
            "model": "fake-llm",
        }

    monkeypatch.setattr("teleops.api.app.get_rag_context", fake_rag)
    monkeypatch.setattr("teleops.api.app.llm_rca", fake_llm)

    llm = client.post(f"/rca/{incident_id}/llm")
    assert llm.status_code == 200
    assert llm.json()["model"] == "fake-llm"

    latest = client.get(f"/rca/{incident_id}/latest?source=any")
    assert latest.status_code == 200
    assert latest.json()["incident_id"] == incident_id
