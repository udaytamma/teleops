from datetime import datetime, timezone

from teleops.llm import rca


class DummyClient:
    def generate(self, prompt: str):
        return {"model": "dummy", "hypotheses": ["x"], "confidence_scores": {}, "evidence": {}}


def test_baseline_rca():
    result = rca.baseline_rca("summary")
    assert result["model"] == "baseline-rules"
    assert result["hypotheses"]


def test_baseline_rca_pattern_matching():
    """Test that baseline RCA selects appropriate hypothesis based on patterns."""
    # DNS-related incident should trigger DNS hypothesis
    dns_result = rca.baseline_rca("DNS servers are reporting failures")
    assert "DNS" in dns_result["hypotheses"][0] or "dns" in dns_result["evidence"]["alerts"].lower()

    # BGP-related incident
    bgp_alerts = [{"alert_type": "bgp_session_flap", "message": "BGP route withdrawal detected"}]
    bgp_result = rca.baseline_rca("routing instability", bgp_alerts)
    assert "BGP" in bgp_result["hypotheses"][0]

    # DDoS-related incident
    ddos_alerts = [{"alert_type": "syn_flood", "message": "Traffic spike on edge"}]
    ddos_result = rca.baseline_rca("security incident", ddos_alerts)
    assert "DDoS" in ddos_result["hypotheses"][0]

    # Fiber cut incident
    fiber_alerts = [{"alert_type": "link_down", "message": "optical loss of signal"}]
    fiber_result = rca.baseline_rca("transport failure", fiber_alerts)
    assert "fiber" in fiber_result["hypotheses"][0].lower()

    # Default network degradation
    default_result = rca.baseline_rca("generic network issue")
    assert "link congestion" in default_result["hypotheses"][0].lower()


def test_build_prompt_and_llm_rca(monkeypatch):
    incident = {"summary": "test"}
    alerts = [{"id": "a", "timestamp": datetime.now(timezone.utc)}]
    rag_context = ["doc"]
    prompt = rca.build_prompt(incident, alerts, rag_context)
    assert "telecom operations RCA assistant" in prompt

    monkeypatch.setattr(rca, "get_llm_client", lambda: DummyClient())
    result = rca.llm_rca(incident, alerts, rag_context)
    assert result["model"] == "dummy"
