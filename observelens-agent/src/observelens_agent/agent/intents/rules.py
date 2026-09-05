import re
from collections.abc import Sequence
from dataclasses import dataclass

from observelens_agent.agent.intents.schemas import IntentType, ShortCommand


@dataclass(frozen=True)
class RuleIntentMatch:
    intent_type: IntentType
    reason: str
    short_cmd: ShortCommand | None = None


_INTENT_RULES: Sequence[tuple[IntentType, ShortCommand | None, re.Pattern[str], str]] = (
    (
        "cmd",
        "generate_incident_report",
        re.compile(r"(?:生成|输出|撰写).{0,12}(?:事故|故障|告警).{0,8}报告", re.IGNORECASE),
        "匹配故障报告关键词",
    ),
    (
        "cmd",
        "get_metric",
        re.compile(
            r"\b(?:metric|metrics|cpu|memory|qps|rps|p\d{2}|latency)\b|指标|监控|错误率|吞吐|延迟|响应时间|负载",
            re.IGNORECASE,
        ),
        "匹配指标关键词",
    ),
    (
        "rca",
        None,
        re.compile(
            r"\b(?:incident|outage)\b|故障|根因|告警|事故|宕机|不可用|异常|排障", re.IGNORECASE
        ),
        "匹配故障分析关键词",
    ),
    (
        "cmd",
        "get_log",
        re.compile(r"\b(?:log|logs)\b|日志", re.IGNORECASE),
        "匹配日志查询关键词",
    ),
    (
        "cmd",
        "get_tarce",
        re.compile(r"\b(?:trace|tracing|span)\b|链路|追踪", re.IGNORECASE),
        "匹配链路追踪关键词",
    ),
    (
        "cmd",
        "get_event",
        re.compile(r"\b(?:event|events)\b|事件", re.IGNORECASE),
        "匹配事件查询关键词",
    ),
    (
        "cmd",
        "get_entity_info",
        re.compile(
            r"(?:查看|查询|获取|了解).{0,16}(?:实体|服务|应用|pod|节点|实例|资源|详情|信息)|(?:实体|服务|应用|pod|节点|实例|资源).{0,8}(?:详情|信息)",
            re.IGNORECASE,
        ),
        "匹配实体详情关键词",
    ),
)


def match_intent_rule(content: str) -> RuleIntentMatch | None:
    """Return the first intent rule that matches the request."""
    for intent_type, short_cmd, pattern, reason in _INTENT_RULES:
        if pattern.search(content):
            return RuleIntentMatch(
                intent_type=intent_type,
                short_cmd=short_cmd,
                reason=reason,
            )
    return None
