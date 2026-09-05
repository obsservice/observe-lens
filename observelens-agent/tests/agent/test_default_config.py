from observelens_agent.agent.state.default_config import DefaultConfig
from observelens_agent.agent.state.state import AgentState
from observelens_agent.config.settings import Settings


def test_default_config_uses_builtin_defaults() -> None:
    config = DefaultConfig()

    assert config.metric_query_default_window_minutes == 60
    assert config.metric_query_step == "60s"
    assert config.metric_query_max_definitions == 3
    assert config.incident_log_query_limit == 200


def test_default_config_uses_settings_overrides() -> None:
    config = DefaultConfig.from_settings(
        Settings(
            intent_llm_model="intent-model",
            metric_query_default_window_minutes=15,
            metric_query_step="30s",
            metric_query_max_definitions=5,
            incident_log_query_limit=75,
        )
    )

    assert config.intent_llm_model == "intent-model"
    assert config.metric_query_default_window_minutes == 15
    assert config.metric_query_step == "30s"
    assert config.metric_query_max_definitions == 5
    assert config.incident_log_query_limit == 75


def test_agent_state_accepts_default_config_overrides() -> None:
    state = AgentState(msg="查询 CPU", default_config={"metric_query_max_definitions": 1})

    assert state.default_config.metric_query_max_definitions == 1
