import json
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx
import structlog
from langgraph.config import get_stream_writer

from observelens_agent.agent.state.default_config import DefaultConfig
from observelens_agent.agent.state.state import AgentState

logger = structlog.get_logger(__name__)

_ANSWER_SYSTEM_PROMPT = """You are an internal observability knowledge assistant.
Answer the user's question using the supplied internal knowledge context when relevant.
Do not invent facts that are not supported by the context. If the context is insufficient,
say so clearly and provide the most useful next step. Answer in the user's language."""


class AnswerLLM(Protocol):
    """Language-model dependency used by answer nodes."""

    async def answer(self, question: str, contexts: Sequence[dict[str, Any]]) -> str | None: ...


AnswerNode = Callable[[AgentState], Awaitable[AgentState]]


class OpenAICompatibleAnswerLLM:
    """Answer client for OpenAI-compatible chat-completions APIs."""

    def __init__(self, default_config: DefaultConfig) -> None:
        self._endpoint = (
            f"{default_config.intent_llm_base_url.rstrip('/')}/chat/completions"
            if default_config.intent_llm_base_url
            else None
        )
        self._model = default_config.intent_llm_model
        self._api_key = default_config.intent_llm_api_key
        self._timeout = httpx.Timeout(
            default_config.intent_llm_timeout_seconds,
            connect=min(default_config.intent_llm_timeout_seconds, 5.0),
        )

    async def answer(self, question: str, contexts: Sequence[dict[str, Any]]) -> str | None:
        if self._endpoint is None or self._model is None:
            return None

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": _ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": _build_answer_prompt(question, contexts)},
            ],
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._endpoint, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("answer_llm_unavailable", error=str(exc))
            return None
        return _extract_message_content(response.json())


class _EventEmitter:
    def __init__(self, conversation_id: str, run_id: str) -> None:
        try:
            self._writer: Callable[[dict[str, str]], None] | None = get_stream_writer()
        except RuntimeError:
            self._writer = None
        self._conversation_id = conversation_id
        self._run_id = run_id
        self._sequence = 0

    def emit(self, event_type: str, data: dict[str, object]) -> None:
        if self._writer is None:
            return
        self._sequence += 1
        payload = {
            "id": f"answer-{self._run_id}-{self._sequence}",
            "type": event_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "conversation_id": self._conversation_id,
            "run_id": self._run_id,
            "sequence": self._sequence,
            "data": data,
        }
        self._writer(
            {
                "sse": (
                    f"event: {event_type}\nid: {payload['id']}\n"
                    f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                )
            }
        )


def _build_answer_prompt(question: str, contexts: Sequence[dict[str, Any]]) -> str:
    documents: list[str] = []
    for index, context in enumerate(contexts, start=1):
        content = context.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        citation = context.get("citation")
        source = ""
        if isinstance(citation, dict) and isinstance(citation.get("document_name"), str):
            source = f"（来源：{citation['document_name']}）"
        documents.append(f"[{index}] {content.strip()} {source}".strip())
    context_text = "\n\n".join(documents) or "（未检索到内部知识）"
    return f"问题：{question}\n\n内部知识：\n{context_text}"


def _extract_message_content(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message")
    if not isinstance(message, dict):
        return None
    content = message.get("content")
    return content.strip() if isinstance(content, str) and content.strip() else None


def create_answer_node(answer_llm: AnswerLLM | None = None) -> AnswerNode:
    """Create a reusable node that answers with RAG contexts from the current state."""

    async def answer_node(state: AgentState) -> AgentState:
        llm = answer_llm or OpenAICompatibleAnswerLLM(state.default_config)
        response = await llm.answer(state.msg, state.rag_contexts)
        state.msg = response or "暂时无法生成回答，请检查 LLM 配置或稍后重试。"

        emitter = _EventEmitter(state.conversation_id or "conversation", state.run_id or "run")
        emitter.emit("output.started", {"format": "markdown"})
        emitter.emit("output.progress", {"format": "markdown", "content": state.msg})
        emitter.emit("output.completed", {"format": "markdown", "content": state.msg})
        return state

    return answer_node
