import json

from observelens_agent.modules.runs.router import _output_completed_event


def test_output_completed_event_uses_aesp_envelope() -> None:
    event = _output_completed_event("conversation-1", "run-1", "资源详情")

    assert event.startswith("event: output.completed\n")
    payload = json.loads(event.split("data: ", maxsplit=1)[1])
    assert payload["type"] == "output.completed"
    assert payload["data"]["content"] == "资源详情"
