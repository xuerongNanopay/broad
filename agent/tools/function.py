from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from inspect import Parameter, cleandoc, signature
from typing import Any, TypeVar

from .base import AgentTool, ParameterScheme
from .scheme import _scheme_from_parameter

ToolHandler = Callable[..., Any]
T = TypeVar("T", bound=ToolHandler)


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
        tool_description = description or _maybe_from_doc(func)
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
    def parameters(self) -> dict[str, ParameterScheme]:
        params: dict[str, ParameterScheme] = {}
        for parameter in signature(self.handler).parameters.values():
            if parameter.kind in {Parameter.VAR_POSITIONAL, Parameter.VAR_KEYWORD}:
                continue

            params[parameter.name] = _scheme_from_parameter(parameter)
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


def _maybe_from_doc(func: ToolHandler) -> str:
    doc = getattr(func, "__doc__", None)
    if not doc:
        return ""
    return cleandoc(doc)


__all__ = [
    "FunctionAgentTool",
    "ToolHandler",
]
