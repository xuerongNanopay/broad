from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from inspect import Parameter, signature
from typing import Any, TypeVar

from .base import AgentTool, ParameterScheme
from .parameter import FunctionParameter
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


class AgentToolError(Exception):
    """Base exception for agent tool failures."""


class ToolAlreadyRegisteredError(AgentToolError):
    """Raised when a registry receives two tools with the same name."""


@dataclass(frozen=True, slots=True)
class FunctionAgentTool(AgentTool):
    _name: str
    _description: str
    handler: ToolHandler
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_function(
        cls,
        func: T,
        *,
        name: str | None = None,
        description: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "FunctionAgentTool":
        tool_name = name or func.__name__
        tool_description = description or _first_doc_line(func)
        return cls(
            _name=tool_name,
            _description=tool_description,
            handler=func,
            metadata=metadata or {},
        )

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tool name cannot be empty")
        if not self.description:
            raise ValueError(f"Tool '{self.name}' needs a description")
        if not callable(self.handler):
            raise TypeError(f"Tool '{self.name}' handler must be callable")

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, FunctionParameter]:
        params: dict[str, FunctionParameter] = {}
        for parameter in signature(self.handler).parameters.values():
            if parameter.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
                continue

            params[parameter.name] = FunctionParameter.from_inspect_parameter(parameter)
        return params

    def exec(self, **kwargs: Any) -> Any:
        return self.handler(**kwargs)

    def run(self, arguments: Mapping[str, Any] | None = None, /, **kwargs: Any) -> Any:
        call_args = dict(arguments or {})
        call_args.update(kwargs)
        return self.exec(**call_args)

    def __call__(self, arguments: Mapping[str, Any] | None = None, /, **kwargs: Any) -> Any:
        return self.run(arguments, **kwargs)

    def to_tool_scheme(self) -> dict[str, Any]:
        required = [
            parameter.name
            for parameter in self.parameters.values()
            if parameter.required
        ]
        parameters_scheme: dict[str, Any] = {
            "type": "object",
            "properties": {
                name: parameter.to_tool_scheme()
                for name, parameter in self.parameters.items()
            },
        }
        if required:
            parameters_scheme["required"] = required

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters_scheme,
        }

    def as_langchain_tool(self):
        from langchain_core.tools import StructuredTool

        return StructuredTool.from_function(
            func=self.handler,
            name=self.name,
            description=self.description,
        )


class ToolRegistry:
    def __init__(self, tools: list[AgentTool] | None = None):
        self._tools: dict[str, AgentTool] = {}
        for tool in tools or []:
            self.register(tool)

    def register(self, tool: AgentTool) -> AgentTool:
        if tool.name in self._tools:
            raise ToolAlreadyRegisteredError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool
        return tool

    def tool(
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

    def as_langchain_tools(self) -> list[Any]:
        return [tool.as_langchain_tool() for tool in self.list()]


default_registry = ToolRegistry()


def tool(
    func: T | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    metadata: Mapping[str, Any] | None = None,
):
    return default_registry.tool(
        func,
        name=name,
        description=description,
        metadata=metadata,
    )


def _first_doc_line(func: ToolHandler) -> str:
    doc = getattr(func, "__doc__", None)
    if not doc:
        return ""
    return doc.strip().splitlines()[0].strip()


__all__ = [
    "AgentTool",
    "AgentToolError",
    "ArrayScheme",
    "BooleanScheme",
    "FunctionParameter",
    "FunctionAgentTool",
    "IntegerScheme",
    "NumberScheme",
    "ObjectScheme",
    "ParameterScheme",
    "StringScheme",
    "ToolAlreadyRegisteredError",
    "ToolRegistry",
    "default_registry",
    "tool",
]
