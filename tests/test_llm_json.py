import json

import pytest

from teleops.llm.client import LLMClientError, _parse_json_response


def test_parse_json_response_raw():
    payload = {"hypotheses": ["a"], "model": "test"}
    result = _parse_json_response(json.dumps(payload))
    assert result["model"] == "test"


def test_parse_json_response_fenced():
    payload = {"hypotheses": ["b"], "model": "test"}
    content = f"```json\n{json.dumps(payload)}\n```"
    with pytest.raises(LLMClientError):
        _parse_json_response(content)


def test_parse_json_response_embedded():
    payload = {"hypotheses": ["c"], "model": "test"}
    content = f"Header text {json.dumps(payload)} trailing"
    result = _parse_json_response(content)
    assert result["model"] == "test"
