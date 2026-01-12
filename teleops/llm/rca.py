"""RCA generation with baseline and LLM."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from teleops.llm.client import get_llm_client


def baseline_rca(incident_summary: str) -> dict[str, Any]:
    return {
        "incident_summary": incident_summary,
        "hypotheses": ["link congestion on core-router-1 causing packet loss"],
        "confidence_scores": {"link congestion on core-router-1 causing packet loss": 0.55},
        "evidence": {"alerts": "packet_loss/high_latency burst on core-router-1"},
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "baseline-rules",
    }


def build_prompt(incident: dict[str, Any], alerts: list[dict[str, Any]], rag_context: list[str]) -> str:
    prompt = {
        "instruction": (
            "You are a telecom operations RCA assistant. "
            "Return only valid JSON following the schema below. "
            "Do not wrap the JSON in markdown or code fences."
        ),
        "schema": {
            "incident_summary": "string",
            "hypotheses": ["string"],
            "confidence_scores": {"hypothesis": 0.0},
            "evidence": {"key": "value"},
            "generated_at": "ISO-8601 timestamp",
            "model": "string",
        },
        "incident": incident,
        "alerts_sample": alerts[:20],
        "rag_context": rag_context,
        "constraints": [
            "Do not invent remediation commands.",
            "If uncertain, include lower confidence score.",
        ],
    }
    return json_dumps(prompt)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def json_dumps(payload: dict[str, Any]) -> str:
    import json

    return json.dumps(payload, indent=2, default=_json_default)


def llm_rca(incident: dict[str, Any], alerts: list[dict[str, Any]], rag_context: list[str]) -> dict[str, Any]:
    client = get_llm_client()
    prompt = build_prompt(incident, alerts, rag_context)
    return client.generate(prompt)
