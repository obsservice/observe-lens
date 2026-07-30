"""FastMCP server setup and tool registration.

Design doc §6.1 and §15.1 — the server registers tools, maintains request
context, and delegates execution to the service layer.
"""

from __future__ import annotations

import typing
from typing import Any

import structlog
from fastmcp import FastMCP
from fastmcp.tools.tool import FunctionTool
from pydantic import BaseModel

from observability_mcp_gateway.core.errors import ToolError
from observability_mcp_gateway.core.registry import ToolDefinition, registry

logger = structlog.get_logger(__name__)


def _type_str(annotation: Any) -> str:
    """Render a Python type annotation as a source-code string."""
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)

    if origin is typing.Union or (origin is type(None) and args):
        return " | ".join(_type_str(a) for a in args)
    if origin is not None:
        inner = ", ".join(_type_str(a) for a in args)
        origin_str = _type_str(origin)
        return origin_str + "[" + inner + "]" if inner else origin_str
    if annotation is type(None):
        return "None"
    if hasattr(annotation, "__name__"):
        return str(annotation.__name__)
    return str(annotation)


def _build_wrapper(definition: ToolDefinition) -> Any:
    """Dynamically create an async function whose signature mirrors the tool's
    input schema fields.

    FastMCP inspects the function signature to derive the MCP tool's parameter
    schema, so we need explicit parameters (not ``**kwargs``).
    """
    input_model = definition.input_schema
    fields = input_model.model_fields

    # Build parameter declarations and a namespace of referenced types.
    params: list[str] = []
    namespace: dict[str, Any] = {"__builtins__": __builtins__}

    for field_name, field_info in fields.items():
        type_name = f"_type_{field_name}"
        namespace[type_name] = field_info.annotation

        if field_info.is_required():
            params.append(f"{field_name}: {type_name}")
        else:
            default_repr = repr(field_info.default)
            params.append(f"{field_name}: {type_name} = {default_repr}")

    params_str = ", ".join(params) if params else ""
    field_names = list(fields.keys())

    src_lines = [
        f"async def {definition.name}({params_str}):",
    ]
    if field_names:
        construct_args = ", ".join(f"{n}={n}" for n in field_names)
        src_lines.append(f"    _input = _input_model({construct_args})")
    else:
        src_lines.append("    _input = _input_model()")
    src_lines.append("    return await _handler(_input)")

    src = "\n".join(src_lines)
    namespace["_input_model"] = input_model
    namespace["_handler"] = _wrap_handler(definition)

    exec(src, namespace)  # noqa: S102
    fn = namespace[definition.name]
    fn.__doc__ = definition.description
    return fn


def _wrap_handler(definition: ToolDefinition) -> Any:
    """Wrap the tool handler with logging, validation, and error handling."""

    async def _wrapped(request: BaseModel) -> dict[str, Any]:
        logger.info(
            "tool_call_start",
            tool_name=definition.name,
            arguments=_summarise_kwargs(request.model_dump()),
        )
        try:
            raw_result = await definition.handler(request)
            validated_output = definition.output_schema.model_validate(raw_result)
            logger.info("tool_call_success", tool_name=definition.name)
            return validated_output.model_dump()
        except ToolError as exc:
            logger.warning(
                "tool_call_error",
                tool_name=definition.name,
                error_code=exc.code.value,
                message=exc.message,
            )
            return {"error": exc.to_dict()}
        except Exception:
            logger.exception("tool_call_unexpected_error", tool_name=definition.name)
            err = ToolError.internal()
            return {"error": err.to_dict()}

    return _wrapped


def _summarise_kwargs(data: dict[str, Any]) -> dict[str, Any]:
    """Return a size-limited copy of *data* for logging."""
    summary: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str) and len(value) > 200:
            summary[key] = value[:200] + "...[truncated]"
        else:
            summary[key] = value
    return summary


def create_mcp_server() -> FastMCP:
    """Create a FastMCP server and register all tools from the registry.

    Each registered tool:
      1. Validates input against its Pydantic schema.
      2. Invokes the handler.
      3. Validates output against its output schema.
      4. Returns the structured result or a serialised :class:`ToolError`.
    """
    mcp = FastMCP("observability-mcp-gateway")

    for definition in registry.list_tools(include_disabled=False):
        wrapper_fn = _build_wrapper(definition)
        tool = FunctionTool.from_function(
            wrapper_fn,
            name=definition.name,
            description=definition.description,
            output_schema=None,
        )
        mcp.add_tool(tool)

    logger.info("mcp_server_initialised", tool_count=len(registry.list_names()))
    return mcp
