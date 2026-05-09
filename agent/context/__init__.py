from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any, TypeVar

from .base import AgentTool, ParameterScheme
from .function import FunctionAgentTool
from .scheme import (
    ArrayScheme,
    BooleanScheme,
    IntegerScheme,
    NumberScheme,
    ObjectScheme,
    StringScheme,
)

ToolHandler = Callable[..., Any]
T = TypeVar("T", bound=ToolHandler)


class ToolRegistry:
    def __init__(self, tools: list[AgentTool] | None = None):
        self._tools: dict[str, AgentTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: AgentTool) -> AgentTool:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool
        return tool

    def function_tool(
        self,
        func: T | None = None,
        *,
        name: str | None = None,
        description: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ):
        def decorator(inner: T) -> AgentTool:
            return self.register(
                FunctionAgentTool.from_function(
                    inner,
                    name=name,
                    description=description,
                    metadata=metadata,
                )
            )

        if func is None:
            return decorator
        return decorator(func)

    def get(self, name: str) -> AgentTool:
        return self._tools[name]

    def list(self) -> list[AgentTool]:
        return list(self._tools.values())

    def run(self, name: str, arguments: Mapping[str, Any] | None = None, /, **kwargs: Any) -> Any:
        call_args = dict(arguments or {})
        call_args.update(kwargs)
        return self.get(name).exec(**call_args)


global_tool_registry = ToolRegistry()


__all__ = [
    "AgentTool",
    "ArrayScheme",
    "BooleanScheme",
    "FunctionAgentTool",
    "IntegerScheme",
    "NumberScheme",
    "ObjectScheme",
    "ParameterScheme",
    "StringScheme",
    "ToolRegistry",
    "global_tool_registry",
]
