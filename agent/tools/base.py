from abc import ABC, abstractmethod
from typing import Any


class AgentTool(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        pass

    @abstractmethod
    def exec(self, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def to_tool_scheme(self) -> dict[str, Any]:
        pass


class ParameterScheme(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        pass

    @property
    @abstractmethod
    def default(self) -> Any:
        pass

    @property
    @abstractmethod
    def required(self) -> bool:
        pass

    @abstractmethod
    def to_tool_scheme(self) -> dict[str, Any]:
        pass
