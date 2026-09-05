import re

_ENTITY_ID_PATTERN = re.compile(r"\bentity_id\s*[=:]\s*(?P<entity>[A-Za-z0-9_.:-]+)", re.IGNORECASE)
_ENTITY_MENTION_PATTERN = re.compile(r"@(?P<entity>[A-Za-z0-9_.:-]+)")
_ENTITY_KEYWORD_PATTERN = re.compile(
    r"(?P<entity>[A-Za-z][A-Za-z0-9_.:-]*)\s*(?:的)?(?:实体|服务|应用|pod|节点|实例|资源)(?:详情|信息)?",
    re.IGNORECASE,
)


def extract_entity(content: str) -> str | None:
    """Extract an entity identifier or name using supported request keywords."""
    for pattern in (_ENTITY_ID_PATTERN, _ENTITY_MENTION_PATTERN, _ENTITY_KEYWORD_PATTERN):
        if match := pattern.search(content):
            return match.group("entity")
    return None
