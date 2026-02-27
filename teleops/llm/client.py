"""LLM client adapters."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from teleops.config import logger, settings

SYSTEM_PROMPT = (
    "You are a Principal Network Operations Engineer with 15 years of experience in telecom NOCs. "
    "You specialize in IP/MPLS networks, BGP routing, DNS infrastructure, optical transport, "
    "CDN operations, firewall policy, and database performance for Tier-1 MSOs.\n\n"
    "ANALYSIS FRAMEWORK:\n"
    "1. Pattern recognition: What alert sequence or timing indicates causation vs correlation?\n"
    "2. Domain expertise: Which telecom failure modes match this alert pattern?\n"
    "3. Evidence strength: Distinguish symptoms (high latency) from root causes (fiber cut).\n\n"
    "OUTPUT REQUIREMENTS:\n"
    "- Start each hypothesis with the root cause (declarative, specific, naming components).\n"
    "- Cite 2-3 alert types from the provided sample as supporting evidence.\n"
    "- Confidence scores: commit to the most likely cause (0.6-0.8), not hedging at 0.5.\n"
    "- If a scenario_hint is provided, strongly consider it -- it comes from pattern matching.\n"
    "- Use the rag_context to ground your analysis in documented failure modes and runbooks.\n"
    "- 1-3 hypotheses maximum, ordered by confidence (highest first).\n\n"
    "Return only valid JSON matching the provided schema. No markdown fences."
)


class LLMClientError(RuntimeError):
    pass


def _safe_extract_text(response) -> str:
    """Safely extract text from a Gemini API response.

    The response.text property can raise ValueError when the response
    contains no text parts (e.g., multipart response with only tool calls).

    Args:
        response: Gemini GenerateContentResponse object.

    Returns:
        Extracted text string.

    Raises:
        LLMClientError: If no text could be extracted.
    """
    try:
        text = response.text
        if text:
            return text
    except (ValueError, AttributeError):
        pass

    # Fallback: try to extract text from response parts directly
    try:
        parts = []
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    parts.append(part.text)
        if parts:
            return "\n".join(parts)
    except Exception:
        pass

    raise LLMClientError("Gemini returned no text content")


class BaseLLMClient:
    def generate(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError


def _parse_json_response(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    if re.search(r"```", content):
        raise LLMClientError("LLM response was not valid JSON")

    brace_start = content.find("{")
    brace_end = content.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        return json.loads(content[brace_start:brace_end + 1])

    raise LLMClientError("LLM response was not valid JSON")


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self, base_url: str, api_key: str | None, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        url = f"{self.base_url}/chat/completions"
        timeout = settings.llm_timeout_seconds
        logger.info(f"LLM request to {url} with model={self.model}, timeout={timeout}s")

        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)

        if response.status_code >= 400:
            logger.error(f"LLM request failed: {response.status_code} {response.text[:200]}")
            raise LLMClientError(f"LLM request failed: {response.status_code} {response.text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        logger.info(f"LLM response received, parsing JSON ({len(content)} chars)")
        return _parse_json_response(content)


class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def generate(self, prompt: str) -> dict[str, Any]:
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise LLMClientError("Gemini SDK not installed") from exc

        logger.info(f"Gemini request with model={self.model}, timeout={settings.gemini_timeout_seconds}s")
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model, system_instruction=SYSTEM_PROMPT)

        # Configure timeout via generation config
        try:
            generation_config = genai.GenerationConfig(
                temperature=0.2,
                response_mime_type="application/json",
            )
        except TypeError:
            generation_config = genai.GenerationConfig(
                temperature=0.2,
            )
        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                request_options={"timeout": settings.gemini_timeout_seconds},
            )
        except TypeError:
            # Older SDKs may not support request_options
            response = model.generate_content(prompt, generation_config=generation_config)
        text = _safe_extract_text(response)
        logger.info(f"Gemini response received, parsing JSON ({len(text)} chars)")
        return _parse_json_response(text)


def get_llm_client() -> BaseLLMClient:
    if settings.llm_provider in {"local_telellm", "hosted_telellm"}:
        return OpenAICompatibleClient(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMClientError("GEMINI_API_KEY is required for Gemini provider")
        return GeminiClient(settings.gemini_api_key, settings.llm_model)
    raise LLMClientError(f"Unsupported LLM provider: {settings.llm_provider}")
