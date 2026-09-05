from observelens_agent.agent.intents.commands import (
    extract_short_cmd,
    intent_type_for_short_cmd,
)
from observelens_agent.agent.intents.entities import extract_entity
from observelens_agent.agent.intents.llm import IntentLLM, OpenAICompatibleIntentLLM
from observelens_agent.agent.intents.rules import match_intent_rule
from observelens_agent.agent.intents.schemas import IntentMatch
from observelens_agent.agent.state.default_config import DefaultConfig


class IntentRecognizer:
    """Recognize requests through command, rule, and LLM stages."""

    def __init__(self, llm: IntentLLM | None = None) -> None:
        self._llm = llm

    async def recognize(self, content: str) -> IntentMatch:
        normalized_content = content.strip()
        entity = extract_entity(normalized_content)
        short_cmd = extract_short_cmd(normalized_content)

        if short_cmd:
            return IntentMatch(
                intent_type=intent_type_for_short_cmd(short_cmd),
                short_cmd=short_cmd,
                entity=entity,
                source="command",
                confidence=1.0,
                reason=f"匹配快捷命令 /{short_cmd}",
            )

        if rule_match := match_intent_rule(normalized_content):
            return IntentMatch(
                intent_type=rule_match.intent_type,
                short_cmd=rule_match.short_cmd,
                entity=entity,
                source="rule",
                confidence=0.9,
                reason=rule_match.reason,
            )

        if self._llm and (llm_result := await self._llm.infer(normalized_content)):
            return IntentMatch(
                intent_type=llm_result.intent_type,
                short_cmd=llm_result.short_cmd,
                entity=entity or llm_result.entity,
                source="llm",
                confidence=llm_result.confidence,
                reason=llm_result.reason,
            )

        return IntentMatch(
            intent_type="qa",
            short_cmd=None,
            entity=entity,
            source="fallback",
            confidence=0.0,
            reason="未命中快捷命令、关键词规则或可用的 LLM 分类结果",
        )


def build_intent_recognizer(default_config: DefaultConfig) -> IntentRecognizer:
    return IntentRecognizer(
        OpenAICompatibleIntentLLM(
            base_url=default_config.intent_llm_base_url,
            model=default_config.intent_llm_model,
            api_key=default_config.intent_llm_api_key,
            timeout_seconds=default_config.intent_llm_timeout_seconds,
        )
    )
