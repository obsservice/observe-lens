"""Unit tests for the tool registry."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from observability_mcp_gateway.core.registry import ToolDefinition, ToolRegistry


class _DummyInput(BaseModel):
    value: str = ""


class _DummyOutput(BaseModel):
    result: str = ""


async def _dummy_handler(**kwargs: object) -> dict[str, object]:
    return {"result": "ok"}


def test_register_and_get() -> None:
    reg = ToolRegistry()
    tool = ToolDefinition(
        name="dummy_tool",
        description="A dummy tool.",
        input_schema=_DummyInput,
        output_schema=_DummyOutput,
        handler=_dummy_handler,
    )
    reg.register(tool)
    assert reg.get("dummy_tool") is not None
    assert "dummy_tool" in reg.list_names()


def test_unregister() -> None:
    reg = ToolRegistry()
    reg.register(
        ToolDefinition(
            name="temp_tool",
            description="Temporary.",
            input_schema=_DummyInput,
            output_schema=_DummyOutput,
            handler=_dummy_handler,
        )
    )
    reg.unregister("temp_tool")
    assert reg.get("temp_tool") is None


def test_set_enabled() -> None:
    reg = ToolRegistry()
    reg.register(
        ToolDefinition(
            name="toggle_tool",
            description="Toggle me.",
            input_schema=_DummyInput,
            output_schema=_DummyOutput,
            handler=_dummy_handler,
        )
    )
    assert reg.is_enabled("toggle_tool")
    reg.set_enabled("toggle_tool", enabled=False)
    assert not reg.is_enabled("toggle_tool")
    assert "toggle_tool" not in reg.list_names()
    assert "toggle_tool" in reg.list_names(include_disabled=True)


def test_clear() -> None:
    reg = ToolRegistry()
    reg.register(
        ToolDefinition(
            name="a_tool",
            description="A.",
            input_schema=_DummyInput,
            output_schema=_DummyOutput,
            handler=_dummy_handler,
        )
    )
    reg.clear()
    assert reg.list_names() == []


def test_get_nonexistent() -> None:
    reg = ToolRegistry()
    assert reg.get("nonexistent") is None


@pytest.mark.asyncio
async def test_dummy_handler_executes() -> None:
    result = await _dummy_handler()
    assert result == {"result": "ok"}
