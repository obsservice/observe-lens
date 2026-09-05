import json
from typing import Protocol

import httpx
import structlog

from observelens_agent.agent.intents.schemas import LLMIntentResponse

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """You classify observability chat requests.
Return JSON only with keys intent_type, short_cmd, entity, confidence, reason.
Allowed intent_type values: cmd, rca, qa.
- cmd: command or common observability data lookup. Use short_cmd get_info or get_metric
  when applicable.
- rca: request root-cause or incident analysis. short_cmd must be null unless an explicit
  command is present.
- qa: documentation consultation or other general questions. short_cmd must be null.
entity must be the requested entity name or identifier when present; otherwise null.
confidence must be a number from 0 to 1. reason must be concise."""


class IntentLLM(Protocol):
    async def infer(self, content: str) -> LLMIntentResponse | None: ...


class OpenAICompatibleIntentLLM:
    def __init__(
        self, base_url: str | None, model: str | None, api_key: str | None, timeout_seconds: float
    ) -> None:
        self._endpoint = f"{base_url.rstrip('/')}/chat/completions" if base_url else None
        self._model = model
        self._api_key = api_key
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def infer(self, content: str) -> LLMIntentResponse | None:
        if self._endpoint is None or self._model is None:
            return None

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._endpoint, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("intent_llm_unavailable", error=str(exc))
            return None

        return self._parse_response(response.json())

    @staticmethod
    def _parse_response(payload: object) -> LLMIntentResponse | None:
        if not isinstance(payload, dict):
            return None
        choices = payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            return None
        message = choices[0].get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            return None
        content = message["content"].strip().removeprefix("```json").removeprefix("```")
        content = content.removesuffix("```").strip()
        try:
            return LLMIntentResponse.model_validate(json.loads(content))
        except (ValueError, TypeError):
            logger.warning("intent_llm_invalid_response")
            return None
