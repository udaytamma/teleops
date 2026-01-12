from datetime import datetime, timezone

from teleops.llm import rca


class DummyClient:
    def generate(self, prompt: str):
        return {"model": "dummy", "hypotheses": ["x"], "confidence_scores": {}, "evidence": {}}


def test_baseline_rca():
    result = rca.baseline_rca("summary")
    assert result["model"] == "baseline-rules"
    assert result["hypotheses"]


def test_build_prompt_and_llm_rca(monkeypatch):
    incident = {"summary": "test"}
    alerts = [{"id": "a", "timestamp": datetime.now(timezone.utc)}]
    rag_context = ["doc"]
    prompt = rca.build_prompt(incident, alerts, rag_context)
    assert "telecom operations RCA assistant" in prompt

    monkeypatch.setattr(rca, "get_llm_client", lambda: DummyClient())
    result = rca.llm_rca(incident, alerts, rag_context)
    assert result["model"] == "dummy"
