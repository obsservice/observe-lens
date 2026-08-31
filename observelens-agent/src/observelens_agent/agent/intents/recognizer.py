import json
import re
from collections.abc import Sequence
from typing import Protocol

import httpx
import structlog

from observelens_agent.agent.intents.schemas import IntentMatch, LLMIntentResponse
from observelens_agent.agent.state.state import IntentName
from observelens_agent.config.settings import Settings

logger = structlog.get_logger(__name__)

_COMMAND_INTENTS: dict[str, IntentName] = {
    "get_info": "get_info",
    "get_metric": "get_metric",
    "analysis_incident": "analysis_incident",
}
_COMMAND_PATTERN = re.compile(
    r"^\s*/(?P<command>get_info|get_metric|analysis_incident)(?=\s|\(|$)", re.IGNORECASE
)
_REGEX_RULES: Sequence[tuple[IntentName, re.Pattern[str], str]] = (
    (
        "mock",
        re.compile(r"\b(?:mock|demo)\b|样例|演示|假数据", re.IGNORECASE),
        "匹配演示数据关键词",
    ),
    (
        "get_metric",
        re.compile(
            r"\b(?:metric|metrics|cpu|memory|qps|rps|p\d{2}|latency)\b|指标|监控|错误率|吞吐|延迟|响应时间|负载",
            re.IGNORECASE,
        ),
        "匹配指标关键词",
    ),
    (
        "analysis_incident",
        re.compile(
            r"\b(?:incident|outage)\b|故障|根因|告警|事故|宕机|不可用|异常|排障", re.IGNORECASE
        ),
        "匹配故障分析关键词",
    ),
    (
        "get_info",
        re.compile(
            r"(?:查看|查询|获取|了解).{0,16}(?:实体|服务|应用|pod|节点|实例|资源|详情|信息)|(?:实体|服务|应用|pod|节点|实例|资源).{0,8}(?:详情|信息)",
            re.IGNORECASE,
        ),
        "匹配实体详情关键词",
    ),
)
_SYSTEM_PROMPT = """You classify observability chat requests.
Return JSON only with keys intent, confidence, reason.
Allowed intent values: get_info, get_metric, analysis_incident, general.
- get_info: request entity, service, resource, or topology details.
- get_metric: request metrics, time series, latency, throughput, or resource utilization.
- analysis_incident: request root-cause or incident analysis.
- general: all other requests.
confidence must be a number from 0 to 1. reason must be concise."""


class IntentLLM(Protocol):
    async def infer(self, content: str) -> LLMIntentResponse | None: ...


class OpenAICompatibleIntentLLM:
    def __init__(
        self, base_url: str, model: str, api_key: str | None, timeout_seconds: float
    ) -> None:
        self._endpoint = f"{base_url.rstrip('/')}/chat/completions"
        self._model = model
        self._api_key = api_key
        self._timeout = httpx.Timeout(timeout_seconds, connect=min(timeout_seconds, 5.0))

    async def infer(self, content: str) -> LLMIntentResponse | None:
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


class IntentRecognizer:
    def __init__(self, llm: IntentLLM | None = None) -> None:
        self._llm = llm

    async def recognize(self, content: str) -> IntentMatch:
        normalized_content = content.strip()
        command_match = _COMMAND_PATTERN.match(normalized_content)
        if command_match:
            command = command_match.group("command").lower()
            return IntentMatch(
                intent=_COMMAND_INTENTS[command],
                source="command",
                confidence=1.0,
                reason=f"匹配快捷命令 /{command}",
            )

        for intent, pattern, reason in _REGEX_RULES:
            if pattern.search(normalized_content):
                return IntentMatch(intent=intent, source="regex", confidence=0.9, reason=reason)

        if self._llm:
            llm_result = await self._llm.infer(normalized_content)
            if llm_result:
                return IntentMatch(
                    intent=llm_result.intent,
                    source="llm",
                    confidence=llm_result.confidence,
                    reason=llm_result.reason,
                )

        return IntentMatch(
            intent="general",
            source="fallback",
            confidence=0.0,
            reason="未命中快捷命令、关键词规则或可用的 LLM 分类结果",
        )


def build_intent_recognizer(settings: Settings) -> IntentRecognizer:
    if settings.intent_llm_base_url and settings.intent_llm_model:
        return IntentRecognizer(
            OpenAICompatibleIntentLLM(
                base_url=settings.intent_llm_base_url,
                model=settings.intent_llm_model,
                api_key=settings.intent_llm_api_key,
                timeout_seconds=settings.intent_llm_timeout_seconds,
            )
        )
    return IntentRecognizer()
