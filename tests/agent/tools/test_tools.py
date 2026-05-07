from inspect import Parameter

import pytest

from agent.tools import (
    AgentTool,
    ArrayScheme,
    BooleanScheme,
    FunctionAgentTool,
    FunctionParameter,
    IntegerScheme,
    NumberScheme,
    ObjectScheme,
    ParameterScheme,
    StringScheme,
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


def test_string_scheme_renders_constraints():
    scheme = StringScheme(
        "query",
        "Search query.",
        min_length=2,
        max_length=120,
        pattern="^[a-z]+$",
        enum=["code", "docs"],
        nullable=True,
    )

    assert isinstance(scheme, ParameterScheme)
    assert scheme.name == "query"
    assert scheme.type == "string"
    assert scheme.required is True
    assert scheme.to_tool_scheme() == {
        "type": "string",
        "description": "Search query.",
        "enum": ["code", "docs"],
        "nullable": True,
        "minLength": 2,
        "maxLength": 120,
        "pattern": "^[a-z]+$",
    }


def test_scalar_schemes_render_tool_schemes():
    integer = IntegerScheme("limit", "Maximum results.", minimum=1, maximum=100, default=10, required=False)
    number = NumberScheme("temperature", minimum=0, maximum=2, multiple_of=0.1)
    boolean = BooleanScheme("include_archived", default=False)

    assert integer.to_tool_scheme() == {
        "type": "integer",
        "description": "Maximum results.",
        "default": 10,
        "minimum": 1,
        "maximum": 100,
    }
    assert number.to_tool_scheme() == {
        "type": "number",
        "minimum": 0,
        "maximum": 2,
        "multipleOf": 0.1,
    }
    assert boolean.to_tool_scheme() == {
        "type": "boolean",
        "default": False,
    }


def test_array_and_object_schemes_render_nested_tool_schemes():
    tags = ArrayScheme(
        "tags",
        "Labels to filter by.",
        items=StringScheme("tag"),
        min_items=1,
        unique_items=True,
        required=False,
    )
    options = ObjectScheme(
        "options",
        properties={
            "limit": IntegerScheme("limit", minimum=1, maximum=50, default=10, required=False),
            "include_archived": BooleanScheme("include_archived"),
        },
        additional_properties=False,
    )

    assert all(isinstance(scheme, ParameterScheme) for scheme in options.properties.values())
    assert tags.to_tool_scheme() == {
        "type": "array",
        "description": "Labels to filter by.",
        "items": {"type": "string"},
        "minItems": 1,
        "uniqueItems": True,
    }
    assert options.to_tool_scheme() == {
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 50,
            },
            "include_archived": {"type": "boolean"},
        },
        "required": ["include_archived"],
        "additionalProperties": False,
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
