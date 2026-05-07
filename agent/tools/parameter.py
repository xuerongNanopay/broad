from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin

from .base import ParameterScheme


@dataclass(frozen=True, slots=True)
class FunctionParameter(ParameterScheme):
    _name: str
    annotation: Any = Parameter.empty
    _description: str = ""
    _default: Any = Parameter.empty
    _required: bool = True

    @classmethod
    def from_inspect_parameter(cls, parameter: Parameter) -> "FunctionParameter":
        return cls(
            _name=parameter.name,
            annotation=parameter.annotation,
            _default=parameter.default,
            _required=parameter.default is Parameter.empty,
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def type(self) -> str:
        return annotation_to_tool_type(self.annotation)

    @property
    def default(self) -> Any:
        return self._default

    @property
    def required(self) -> bool:
        return self._required

    def to_tool_scheme(self) -> dict[str, Any]:
        scheme = {
            "type": self.type,
        }
        if self.description:
            scheme["description"] = self.description
        if self.default is not Parameter.empty:
            scheme["default"] = self.default
        return scheme


def annotation_to_tool_type(annotation: Any) -> str:
    if annotation is Parameter.empty or annotation is Any:
        return "string"

    if isinstance(annotation, str):
        return _string_annotation_to_tool_type(annotation)

    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin in {Union, UnionType}:
        non_none_args = [arg for arg in args if arg is not NoneType]
        if len(non_none_args) == 1:
            return annotation_to_tool_type(non_none_args[0])
        return "string"

    annotation = origin or annotation
    if annotation is str:
        return "string"
    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "integer"
    if annotation is float:
        return "number"
    if annotation in {list, tuple, set}:
        return "array"
    if annotation is dict:
        return "object"
    return "string"


def _string_annotation_to_tool_type(annotation: str) -> str:
    type_name = annotation.removeprefix("typing.").split("[", maxsplit=1)[0]
    return {
        "str": "string",
        "string": "string",
        "bool": "boolean",
        "boolean": "boolean",
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "number": "number",
        "list": "array",
        "tuple": "array",
        "set": "array",
        "dict": "object",
    }.get(type_name, "string")


__all__ = [
    "FunctionParameter",
    "annotation_to_tool_type",
]
