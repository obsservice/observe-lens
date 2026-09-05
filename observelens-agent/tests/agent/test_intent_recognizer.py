import pytest

from observelens_agent.agent.graph import build_agent_graph
from observelens_agent.agent.intents.commands import extract_short_cmd
from observelens_agent.agent.intents.entities import extract_entity
from observelens_agent.agent.intents.llm import OpenAICompatibleIntentLLM
from observelens_agent.agent.intents.recognizer import IntentRecognizer, build_intent_recognizer
from observelens_agent.agent.intents.schemas import LLMIntentResponse
from observelens_agent.agent.state.default_config import DefaultConfig
from observelens_agent.config.settings import Settings


class FakeIntentLLM:
    def __init__(self, response: LLMIntentResponse | None) -> None:
        self._response = response
        self.calls: list[str] = []

    async def infer(self, content: str) -> LLMIntentResponse | None:
        self.calls.append(content)
        return self._response


def test_factory_always_wires_an_llm_client() -> None:
    recognizer = build_intent_recognizer(DefaultConfig.from_settings(Settings()))

    assert isinstance(recognizer._llm, OpenAICompatibleIntentLLM)


@pytest.mark.asyncio
async def test_command_has_highest_priority() -> None:
    llm = FakeIntentLLM(None)
    match = await IntentRecognizer(llm).recognize("/get_entity_info(查看实体详情) CPU 指标")

    assert match.intent_type == "cmd"
    assert match.short_cmd == "get_entity_info"
    assert match.source == "command"
    assert match.confidence == 1.0
    assert llm.calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "intent_type", "short_cmd"),
    [
        ("查询 payment-service 的实体详情", "cmd", "get_entity_info"),
        ("查看 CPU、P99 延迟和 QPS 指标", "cmd", "get_metric"),
        ("查询 payment-service 的错误日志", "cmd", "get_log"),
        ("查看 payment-service 的调用链路", "cmd", "get_tarce"),
        ("查询 payment-service 的事件", "cmd", "get_event"),
        ("生成本次故障报告", "cmd", "generate_incident_report"),
        ("分析这次告警故障的根因", "rca", None),
    ],
)
async def test_regex_rules_match_known_intents(
    content: str, intent_type: str, short_cmd: str | None
) -> None:
    match = await IntentRecognizer().recognize(content)

    assert match.intent_type == intent_type
    assert match.short_cmd == short_cmd
    assert match.source == "rule"
    assert match.confidence == 0.9


def test_keyword_extractors_return_entity_and_short_command() -> None:
    assert extract_entity("/get_entity_info @payment [entity_id=k8s.pod:prod-api-123]") == (
        "k8s.pod:prod-api-123"
    )
    assert extract_entity("查询 payment-service 的实体详情") == "payment-service"
    assert extract_short_cmd(" /get_entity_info @payment") == "get_entity_info"


@pytest.mark.parametrize(
    "command",
    [
        "get_entity_info",
        "get_metric",
        "get_log",
        "get_tarce",
        "get_event",
        "generate_incident_report",
    ],
)
def test_extract_short_cmd_supports_all_cmd_graph_commands(command: str) -> None:
    assert extract_short_cmd(f"/{command} request") == command


@pytest.mark.asyncio
async def test_llm_is_used_after_command_and_regex_miss() -> None:
    llm = FakeIntentLLM(
        LLMIntentResponse(
            intent_type="rca",
            entity="order-service",
            confidence=0.82,
            reason="用户请求定位问题",
        )
    )
    match = await IntentRecognizer(llm).recognize("为什么订单处理变慢？")

    assert match.intent_type == "rca"
    assert match.entity == "order-service"
    assert match.source == "llm"
    assert match.confidence == 0.82
    assert llm.calls == ["为什么订单处理变慢？"]


@pytest.mark.asyncio
async def test_fallback_returns_general_when_llm_is_not_configured() -> None:
    match = await IntentRecognizer().recognize("帮我写一份今天的工作总结")

    assert match.intent_type == "qa"
    assert match.source == "fallback"


@pytest.mark.asyncio
async def test_graph_keeps_the_detected_intent_in_state() -> None:
    graph = build_agent_graph(None, None, None).compile()
    state = await graph.ainvoke({"msg": "/get_metric(查看指标) payment-service"})

    assert state["intent_type"] == "cmd"
    assert state["short_cmd"] == "get_metric"
    assert state["intent_source"] == "command"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("content", "message_prefix"),
    [
        ('/get_log {app="payment-service"}', "日志查询依赖未配置"),
        ("/get_tarce trace-123", "链路追踪查询依赖未配置"),
        ("/get_event cluster=prod", "事件查询依赖未配置"),
        ("/generate_incident_report", "故障报告："),
    ],
)
async def test_cmd_graph_routes_declared_commands_to_their_nodes(
    content: str, message_prefix: str
) -> None:
    graph = build_agent_graph(None, None, None).compile()

    state = await graph.ainvoke({"msg": content})

    assert state["intent_type"] == "cmd"
    assert state["msg"].startswith(message_prefix)
