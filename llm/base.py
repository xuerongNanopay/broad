from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent.tools import AgentTool


@dataclass
class ToolRequest:
    id: str
    name: str
    arguments: dict[str, Any]


class LLMProvider(str, Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"


class FinishReason(str, Enum):
    STOP = "stop"
    LENGTH = "length"
    TOOL_CALLS = "tool_calls"
    CONTENT_FILTER = "content_filter"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str | None
    tool_calls: list[ToolRequest] = field(default_factory=list)
    finish_reason: FinishReason = FinishReason.STOP
    usage: dict[str, int] = field(default_factory=dict)


class LLM(ABC):
    @abstractmethod
    async def invoke(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[AgentTool] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        reasoning: str | None = None,
    ) -> LLMResponse:
        pass


def create_llm(
    provider: LLMProvider | str,
    model: str,
    *,
    temperature: float = 0,
    base_url: str | None = None,
) -> LLM:
    provider = _parse_provider(provider)

    match provider:
        case LLMProvider.OPENAI:
            from llm.openai import OpenAILLM

            return OpenAILLM(default_model=model, default_temperature=temperature, api_url=base_url)
        case LLMProvider.OLLAMA:
            raise NotImplementedError("OLLAMA LLM implementation is not available")


def _parse_provider(provider: LLMProvider | str) -> LLMProvider:
    if isinstance(provider, LLMProvider):
        return provider

    try:
        return LLMProvider(provider.lower())
    except ValueError as exc:
        supported = ", ".join(item.value for item in LLMProvider)
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: {supported}") from exc


__all__ = [
    "FinishReason",
    "LLM",
    "LLMProvider",
    "LLMResponse",
    "ToolRequest",
    "create_llm",
]
