"""LLM client adapters."""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from teleops.config import settings, logger


class LLMClientError(RuntimeError):
    pass


class BaseLLMClient:
    def generate(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError


def _parse_json_response(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    if fence_match:
        return json.loads(fence_match.group(1))

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
                {"role": "system", "content": "You are a telecom operations RCA assistant."},
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
        model = genai.GenerativeModel(self.model)

        # Configure timeout via generation config
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
        logger.info(f"Gemini response received, parsing JSON ({len(response.text)} chars)")
        return _parse_json_response(response.text)


def get_llm_client() -> BaseLLMClient:
    if settings.llm_provider in {"local_telellm", "hosted_telellm"}:
        return OpenAICompatibleClient(settings.llm_base_url, settings.llm_api_key, settings.llm_model)
    if settings.llm_provider == "gemini":
        if not settings.gemini_api_key:
            raise LLMClientError("GEMINI_API_KEY is required for Gemini provider")
        return GeminiClient(settings.gemini_api_key, settings.llm_model)
    raise LLMClientError(f"Unsupported LLM provider: {settings.llm_provider}")
