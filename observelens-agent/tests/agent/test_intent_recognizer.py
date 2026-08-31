import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.agent.intents.recognizer import IntentRecognizer
from observelens_agent.agent.intents.schemas import LLMIntentResponse


class FakeIntentLLM:
    def __init__(self, response: LLMIntentResponse | None) -> None:
        self._response = response
        self.calls: list[str] = []

    async def infer(self, content: str) -> LLMIntentResponse | None:
        self.calls.append(content)
        return self._response


@pytest.mark.asyncio
async def test_command_has_highest_priority() -> None:
    llm = FakeIntentLLM(None)
    match = await IntentRecognizer(llm).recognize("/get_info(查看实体详情) CPU 指标")

    assert match.intent == "get_info"
    assert match.source == "command"
    assert match.confidence == 1.0
    assert llm.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "intent"),
    [
        ("查询 payment-service 的实体详情", "get_info"),
        ("查看 CPU、P99 延迟和 QPS 指标", "get_metric"),
        ("分析这次告警故障的根因", "analysis_incident"),
        ("给我演示一段 mock 数据", "mock"),
    ],
)
async def test_regex_rules_match_known_intents(content: str, intent: str) -> None:
    match = await IntentRecognizer().recognize(content)

    assert match.intent == intent
    assert match.source == "regex"
    assert match.confidence == 0.9


@pytest.mark.asyncio
async def test_llm_is_used_after_command_and_regex_miss() -> None:
    llm = FakeIntentLLM(
        LLMIntentResponse(intent="analysis_incident", confidence=0.82, reason="用户请求定位问题")
    )
    match = await IntentRecognizer(llm).recognize("为什么订单处理变慢？")

    assert match.intent == "analysis_incident"
    assert match.source == "llm"
    assert match.confidence == 0.82
    assert llm.calls == ["为什么订单处理变慢？"]


@pytest.mark.asyncio
async def test_fallback_returns_general_when_llm_is_not_configured() -> None:
    match = await IntentRecognizer().recognize("帮我写一份今天的工作总结")

    assert match.intent == "general"
    assert match.source == "fallback"


@pytest.mark.asyncio
async def test_graph_keeps_the_detected_intent_in_state() -> None:
    graph = build_agent_graph(IntentRecognizer()).compile()
    state = await graph.ainvoke({"msg": "/get_metric(查看指标) payment-service"})

    assert state["intent"] == "get_metric"
    assert state["intent_source"] == "command"
