import json

import pytest

from teleops.config import settings
from teleops.llm.client import LLMClientError, OpenAICompatibleClient, get_llm_client


class DummyResponse:
    def __init__(self, status_code: int, content: str):
        self.status_code = status_code
        self._content = content
        self.text = content

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


class DummyHttpxClient:
    def __init__(self, *args, **kwargs):
        self._response = DummyResponse(
            200,
            json.dumps(
                {
                    "incident_summary": "test",
                    "hypotheses": ["a"],
                    "confidence_scores": {"a": 0.5},
                    "evidence": {},
                    "generated_at": "now",
                    "model": "dummy",
                }
            ),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, url, headers, json):
        return self._response


class DummyHttpxErrorClient(DummyHttpxClient):
    def __init__(self, *args, **kwargs):
        self._response = DummyResponse(500, "error")


def test_openai_client_generate_parses(monkeypatch):
    monkeypatch.setattr("teleops.llm.client.httpx.Client", DummyHttpxClient)
    client = OpenAICompatibleClient("http://example.com", None, "test")
    result = client.generate("prompt")
    assert result["model"] == "dummy"


def test_openai_client_generate_error(monkeypatch):
    monkeypatch.setattr("teleops.llm.client.httpx.Client", DummyHttpxErrorClient)
    client = OpenAICompatibleClient("http://example.com", None, "test")
    with pytest.raises(LLMClientError):
        client.generate("prompt")


def test_get_llm_client_unsupported(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "unknown")
    with pytest.raises(LLMClientError):
        get_llm_client()


def test_get_llm_client_gemini_requires_key(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", None)
    with pytest.raises(LLMClientError):
        get_llm_client()
