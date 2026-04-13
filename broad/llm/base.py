from abc import abstractmethod, ABC
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LLM(ABC):
    """BASE LLM class."""

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str | None = None,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.default_model = default_model
    
    def _ensure_model(self, model: str | None = None) -> str:
        if model != None:
            return model
        
        if self.default_model != None:
            return self.default_model
        
        raise ValueError("miss default_model or model")

    @abstractmethod
    async def prompt(
        self,
        input: str | list[dict[str, Any]],
        model: str | None = None,
        max_token: int = 4096,
        temperature: float = 0.7
    ):
        """
        Send a prompt request.
        """

@dataclass
class LLMResponse:
    """Unify the responses from different LLM provider."""
    responseId: str | None
    text: str | None
    usage: dict[str, int] = field(default_factory=dict)
