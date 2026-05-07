from __future__ import annotations

from inspect import Parameter
from typing import Any

from .base import ParameterScheme


class BaseParameterScheme(ParameterScheme):
    type_name: str

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        default: Any = Parameter.empty,
        required: bool = True,
        enum: tuple[Any, ...] | list[Any] | None = None,
        nullable: bool = False,
    ) -> None:
        self._name = name
        self._description = description
        self._default = default
        self._required = required
        self._enum = tuple(enum) if enum is not None else None
        self._nullable = nullable

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def type(self) -> str:
        return self.type_name

    @property
    def default(self) -> Any:
        return self._default

    @property
    def required(self) -> bool:
        return self._required

    @property
    def enum(self) -> tuple[Any, ...] | None:
        return self._enum

    @property
    def nullable(self) -> bool:
        return self._nullable

    def to_tool_scheme(self) -> dict[str, Any]:
        scheme = self._base_tool_scheme()
        self._add_constraints(scheme)
        return scheme

    def _base_tool_scheme(self) -> dict[str, Any]:
        scheme: dict[str, Any] = {
            "type": self.type,
        }
        if self.description:
            scheme["description"] = self.description
        if self.default is not Parameter.empty:
            scheme["default"] = self.default
        if self.enum is not None:
            scheme["enum"] = list(self.enum)
        if self.nullable:
            scheme["nullable"] = True
        return scheme

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        pass


class StringScheme(BaseParameterScheme):
    type_name = "string"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
        default: str | None | Any = Parameter.empty,
        required: bool = True,
        enum: tuple[str, ...] | list[str] | None = None,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            enum=enum,
            nullable=nullable,
        )
        self._min_length = min_length
        self._max_length = max_length
        self._pattern = pattern

    @property
    def min_length(self) -> int | None:
        return self._min_length

    @property
    def max_length(self) -> int | None:
        return self._max_length

    @property
    def pattern(self) -> str | None:
        return self._pattern

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        if self.min_length is not None:
            scheme["minLength"] = self.min_length
        if self.max_length is not None:
            scheme["maxLength"] = self.max_length
        if self.pattern is not None:
            scheme["pattern"] = self.pattern


class IntegerScheme(BaseParameterScheme):
    type_name = "integer"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        minimum: int | None = None,
        maximum: int | None = None,
        exclusive_minimum: int | None = None,
        exclusive_maximum: int | None = None,
        multiple_of: int | None = None,
        default: int | None | Any = Parameter.empty,
        required: bool = True,
        enum: tuple[int, ...] | list[int] | None = None,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            enum=enum,
            nullable=nullable,
        )
        self._minimum = minimum
        self._maximum = maximum
        self._exclusive_minimum = exclusive_minimum
        self._exclusive_maximum = exclusive_maximum
        self._multiple_of = multiple_of

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        if self._minimum is not None:
            scheme["minimum"] = self._minimum
        if self._maximum is not None:
            scheme["maximum"] = self._maximum
        if self._exclusive_minimum is not None:
            scheme["exclusiveMinimum"] = self._exclusive_minimum
        if self._exclusive_maximum is not None:
            scheme["exclusiveMaximum"] = self._exclusive_maximum
        if self._multiple_of is not None:
            scheme["multipleOf"] = self._multiple_of


class NumberScheme(BaseParameterScheme):
    type_name = "number"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        minimum: int | float | None = None,
        maximum: int | float | None = None,
        exclusive_minimum: int | float | None = None,
        exclusive_maximum: int | float | None = None,
        multiple_of: int | float | None = None,
        default: int | float | None | Any = Parameter.empty,
        required: bool = True,
        enum: tuple[int | float, ...] | list[int | float] | None = None,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            enum=enum,
            nullable=nullable,
        )
        self._minimum = minimum
        self._maximum = maximum
        self._exclusive_minimum = exclusive_minimum
        self._exclusive_maximum = exclusive_maximum
        self._multiple_of = multiple_of

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        if self._minimum is not None:
            scheme["minimum"] = self._minimum
        if self._maximum is not None:
            scheme["maximum"] = self._maximum
        if self._exclusive_minimum is not None:
            scheme["exclusiveMinimum"] = self._exclusive_minimum
        if self._exclusive_maximum is not None:
            scheme["exclusiveMaximum"] = self._exclusive_maximum
        if self._multiple_of is not None:
            scheme["multipleOf"] = self._multiple_of


class BooleanScheme(BaseParameterScheme):
    type_name = "boolean"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        default: bool | None | Any = Parameter.empty,
        required: bool = True,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            nullable=nullable,
        )


class ArrayScheme(BaseParameterScheme):
    type_name = "array"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        items: ParameterScheme | dict[str, Any] | None = None,
        min_items: int | None = None,
        max_items: int | None = None,
        unique_items: bool | None = None,
        default: list[Any] | None | Any = Parameter.empty,
        required: bool = True,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            nullable=nullable,
        )
        self._items = items
        self._min_items = min_items
        self._max_items = max_items
        self._unique_items = unique_items

    @property
    def items(self) -> ParameterScheme | dict[str, Any] | None:
        return self._items

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        if self.items is not None:
            scheme["items"] = _nested_scheme(self.items)
        if self._min_items is not None:
            scheme["minItems"] = self._min_items
        if self._max_items is not None:
            scheme["maxItems"] = self._max_items
        if self._unique_items is not None:
            scheme["uniqueItems"] = self._unique_items


class ObjectScheme(BaseParameterScheme):
    type_name = "object"

    def __init__(
        self,
        name: str,
        description: str = "",
        *,
        properties: dict[str, ParameterScheme] | None = None,
        additional_properties: bool | ParameterScheme | dict[str, Any] | None = None,
        min_properties: int | None = None,
        max_properties: int | None = None,
        default: dict[str, Any] | None | Any = Parameter.empty,
        required: bool = True,
        nullable: bool = False,
    ) -> None:
        super().__init__(
            name,
            description,
            default=default,
            required=required,
            nullable=nullable,
        )
        self._properties = properties or {}
        self._additional_properties = additional_properties
        self._min_properties = min_properties
        self._max_properties = max_properties

    @property
    def properties(self) -> dict[str, ParameterScheme]:
        return self._properties

    def _add_constraints(self, scheme: dict[str, Any]) -> None:
        if self.properties:
            scheme["properties"] = {
                name: _nested_scheme(property_scheme)
                for name, property_scheme in self.properties.items()
            }
            required = [
                name
                for name, property_scheme in self.properties.items()
                if property_scheme.required
            ]
            if required:
                scheme["required"] = required
        if self._additional_properties is not None:
            if isinstance(self._additional_properties, bool):
                scheme["additionalProperties"] = self._additional_properties
            else:
                scheme["additionalProperties"] = _nested_scheme(self._additional_properties)
        if self._min_properties is not None:
            scheme["minProperties"] = self._min_properties
        if self._max_properties is not None:
            scheme["maxProperties"] = self._max_properties


def _nested_scheme(scheme: ParameterScheme | dict[str, Any]) -> dict[str, Any]:
    if isinstance(scheme, ParameterScheme):
        return scheme.to_tool_scheme()
    return scheme


__all__ = [
    "ArrayScheme",
    "BaseParameterScheme",
    "BooleanScheme",
    "IntegerScheme",
    "NumberScheme",
    "ObjectScheme",
    "StringScheme",
]
