import re
from typing import cast

from observelens_agent.agent.intents.schemas import IntentType, ShortCommand

_SHORT_COMMAND_INTENTS: dict[ShortCommand, IntentType] = {
    "get_info": "cmd",
    "get_metric": "cmd",
    "analysis_incident": "rca",
}
_SHORT_COMMAND_PATTERN = re.compile(
    r"^\s*/(?P<short_cmd>get_info|get_metric|analysis_incident)(?=\s|\(|$)",
    re.IGNORECASE,
)


def extract_short_cmd(content: str) -> ShortCommand | None:
    """Extract a supported slash command without its leading slash."""
    match = _SHORT_COMMAND_PATTERN.match(content)
    return cast(ShortCommand, match.group("short_cmd").lower()) if match else None


def intent_type_for_short_cmd(short_cmd: ShortCommand) -> IntentType:
    return _SHORT_COMMAND_INTENTS[short_cmd]
