"""Preflight checks for TeleOps."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check_rag() -> tuple[bool, str]:
    try:
        from teleops.rag.index import get_rag_context

        context = get_rag_context("network degradation packet loss latency")
        if not context:
            return False, "RAG context empty"
        return True, "RAG context loaded"
    except Exception as exc:
        return False, f"RAG error: {exc}"


def check_llm_config() -> tuple[bool, str]:
    try:
        from teleops.config import settings
    except Exception as exc:
        return False, f"Settings error: {exc}"

    provider = settings.llm_provider
    if provider in {"local_telellm", "hosted_telellm"}:
        if not settings.llm_base_url:
            return False, "LLM_BASE_URL missing"
        return True, f"LLM provider {provider} configured"
    if provider == "gemini":
        if not settings.gemini_api_key:
            return False, "GEMINI_API_KEY missing"
        return True, "Gemini provider configured"
    return False, f"Unknown LLM provider: {provider}"


def check_http(url: str) -> tuple[bool, str]:
    try:
        resp = httpx.get(url, timeout=5)
        return resp.status_code < 400, f"{url} -> {resp.status_code}"
    except Exception as exc:
        return False, f"{url} error: {exc}"


def main() -> int:
    api_url = os.getenv("TELEOPS_API_URL", "http://127.0.0.1:8000")
    ui_url = os.getenv("TELEOPS_UI_URL", "http://127.0.0.1:8501")

    checks = [
        ("RAG",) + check_rag(),
        ("LLM Config",) + check_llm_config(),
        ("API",) + check_http(f"{api_url}/incidents"),
        ("UI",) + check_http(ui_url),
    ]

    failed = 0
    for name, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {name}: {detail}")
        if not ok:
            failed += 1

    if failed:
        print(f"Preflight failed: {failed} check(s) failed.")
        return 1
    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
