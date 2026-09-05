from pydantic import BaseModel

from observelens_agent.config.settings import Settings


class DefaultConfig(BaseModel):
    """Runtime graph configuration stored with each Agent state."""

    intent_llm_api_key: str | None = None
    intent_llm_base_url: str | None = None
    intent_llm_model: str | None = None
    intent_llm_timeout_seconds: float = 10.0
    metric_query_default_window_minutes: int = 60
    metric_query_step: str = "60s"
    metric_query_max_definitions: int = 3
    incident_log_query_limit: int = 200

    @classmethod
    def from_settings(cls, settings: Settings) -> "DefaultConfig":
        return cls(
            intent_llm_api_key=settings.intent_llm_api_key,
            intent_llm_base_url=settings.intent_llm_base_url,
            intent_llm_model=settings.intent_llm_model,
            intent_llm_timeout_seconds=settings.intent_llm_timeout_seconds,
            metric_query_default_window_minutes=settings.metric_query_default_window_minutes,
            metric_query_step=settings.metric_query_step,
            metric_query_max_definitions=settings.metric_query_max_definitions,
            incident_log_query_limit=settings.incident_log_query_limit,
        )
