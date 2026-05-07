from inspect import Parameter

import pytest

from agent.tools import (
    AgentTool,
    FunctionAgentTool,
    FunctionParameter,
    ParameterScheme,
    ToolAlreadyRegisteredError,
    ToolRegistry,
)


def test_agent_tool_wraps_function_and_exposes_parameters():
    def add(left: int, right: int = 1) -> int:
        """Add two numbers."""
        return left + right

    tool = FunctionAgentTool.from_function(add)

    assert isinstance(tool, AgentTool)
    assert tool.name == "add"
    assert tool.description == "Add two numbers."
    assert tool.run({"left": 2}, right=3) == 5
    assert list(tool.parameters) == ["left", "right"]
    assert [parameter.required for parameter in tool.parameters.values()] == [True, False]
    assert all(isinstance(parameter, ParameterScheme) for parameter in tool.parameters.values())


def test_function_parameter_implements_parameter_scheme():
    parameter = FunctionParameter(
        _name="limit",
        annotation=int,
        _description="Maximum item count.",
        _default=10,
        _required=False,
    )

    assert isinstance(parameter, ParameterScheme)
    assert parameter.name == "limit"
    assert parameter.type == "integer"
    assert parameter.default == 10
    assert parameter.required is False
    assert parameter.to_tool_scheme() == {
        "type": "integer",
        "description": "Maximum item count.",
        "default": 10,
    }


def test_registry_registers_and_runs_tools():
    registry = ToolRegistry()

    @registry.tool(name="greet", description="Create a greeting.")
    def greet(name: str) -> str:
        return f"Hello, {name}"

    assert registry.get("greet") is greet
    assert registry.run("greet", {"name": "Ada"}) == "Hello, Ada"
    assert registry.list() == [greet]


def test_registry_runs_custom_agent_tool_subclass():
    class UppercaseTool(AgentTool):
        @property
        def name(self) -> str:
            return "uppercase"

        @property
        def description(self) -> str:
            return "Uppercase text."

        @property
        def parameters(self) -> dict:
            return {"text": {"type": "string"}}

        def exec(self, **kwargs):
            return kwargs["text"].upper()

        def to_tool_scheme(self) -> dict:
            return {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": ["text"],
                },
            }

    registry = ToolRegistry([UppercaseTool()])

    assert registry.run("uppercase", {"text": "hello"}) == "HELLO"


def test_registry_rejects_duplicate_names():
    registry = ToolRegistry()

    @registry.tool(description="First tool.")
    def sample() -> str:
        return "first"

    with pytest.raises(ToolAlreadyRegisteredError):
        @registry.tool(name="sample", description="Second tool.")
        def duplicate() -> str:
            return "second"


def test_langchain_adapter_uses_tool_metadata():
    def echo(text: str) -> str:
        """Echo the provided text."""
        return text

    tool = FunctionAgentTool.from_function(echo, name="echo_text")
    langchain_tool = tool.as_langchain_tool()

    assert langchain_tool.name == "echo_text"
    assert langchain_tool.description == "Echo the provided text."
    assert langchain_tool.invoke({"text": "hello"}) == "hello"


def test_function_tool_scheme_uses_function_parameters():
    def search(query: str, limit: int = 5, include_archived: bool = False) -> list[str]:
        """Search indexed documents."""
        return [query] * limit if include_archived else [query]

    tool = FunctionAgentTool.from_function(search)

    assert tool.to_tool_scheme() == {
        "name": "search",
        "description": "Search indexed documents.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5},
                "include_archived": {"type": "boolean", "default": False},
            },
            "required": ["query"],
        },
    }


def test_function_parameter_without_default_reports_empty_default():
    def echo(text: str) -> str:
        """Echo text."""
        return text

    parameter = FunctionAgentTool.from_function(echo).parameters["text"]

    assert parameter.default is Parameter.empty
