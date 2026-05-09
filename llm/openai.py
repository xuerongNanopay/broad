from __future__ import annotations

from json import loads
from typing import Any

from agent.tools import AgentTool
from llm.base import FinishReason, LLM, LLMResponse, ToolRequest


class OpenAILLM(LLM):
    def __init__(
        self,
        model: str,
        *,
        client: Any | None = None,
        temperature: float = 0,
        base_url: str | None = None,
    ) -> None:
        self._model = model
        self._client = client or _create_openai_client(base_url=base_url)
        self._temperature = temperature

    @property
    def model(self) -> str:
        return self._model

    @property
    def client(self) -> Any:
        return self._client

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
        kwargs: dict[str, Any] = {
            "model": model or self.model,
            "input": messages,
            "max_output_tokens": max_tokens,
            "temperature": temperature if temperature is not None else self._temperature,
        }
        if tools:
            kwargs["tools"] = [_to_openai_tool(tool) for tool in tools]
        if reasoning:
            kwargs["reasoning"] = {"effort": reasoning}

        response = await self.client.responses.create(**kwargs)
        return _to_llm_response(response)


def create_openai_llm(
    model: str,
    *,
    temperature: float = 0,
    base_url: str | None = None,
) -> LLM:
    return OpenAILLM(
        model,
        temperature=temperature,
        base_url=base_url,
    )


def _create_openai_client(*, base_url: str | None = None) -> Any:
    from openai import AsyncOpenAI
    from utils.env import load_env

    load_env()
    kwargs: dict[str, Any] = {}
    if base_url is not None:
        kwargs["base_url"] = base_url
    return AsyncOpenAI(**kwargs)


def _to_openai_tool(tool: AgentTool) -> dict[str, Any]:
    scheme = tool.to_tool_scheme()
    return {
        "type": "function",
        "name": scheme["name"],
        "description": scheme.get("description"),
        "parameters": scheme.get("parameters"),
        "strict": False,
    }


def _to_llm_response(response: Any) -> LLMResponse:
    output = list(getattr(response, "output", None) or [])
    content = _response_text(response, output)
    tool_calls = _to_tool_requests(output)

    return LLMResponse(
        content=None if content is None else str(content),
        tool_calls=tool_calls,
        finish_reason=_to_finish_reason(response, tool_calls),
        usage=_to_usage(getattr(response, "usage", None)),
    )


def _response_text(response: Any, output: list[Any]) -> str | None:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    parts: list[str] = []
    for item in output:
        if _field(item, "type") != "message":
            continue
        for content in _field(item, "content", []) or []:
            text = _field(content, "text")
            if text is not None:
                parts.append(str(text))

    if not parts:
        return None
    return "\n".join(parts)


def _to_finish_reason(response: Any, tool_calls: list[ToolRequest]) -> FinishReason:
    if tool_calls:
        return FinishReason.TOOL_CALLS

    status = _field(response, "status")
    if status in {None, "completed"}:
        return FinishReason.STOP
    if status == "failed":
        return FinishReason.ERROR

    incomplete_details = _field(response, "incomplete_details")
    reason = _field(incomplete_details, "reason")
    if reason is None:
        return FinishReason.UNKNOWN

    normalized = str(reason).lower()
    aliases = {
        "content_filter": FinishReason.CONTENT_FILTER,
        "length": FinishReason.LENGTH,
        "max_output_tokens": FinishReason.LENGTH,
        "stop": FinishReason.STOP,
        "tool_call": FinishReason.TOOL_CALLS,
        "tool_calls": FinishReason.TOOL_CALLS,
    }
    if normalized in aliases:
        return aliases[normalized]

    try:
        return FinishReason(normalized)
    except ValueError:
        return FinishReason.UNKNOWN


def _to_usage(usage: Any) -> dict[str, int]:
    if usage is None:
        return {}
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    elif not isinstance(usage, dict):
        usage = {
            name: getattr(usage, name)
            for name in ("completion_tokens", "prompt_tokens", "total_tokens")
            if getattr(usage, name, None) is not None
        }

    return {
        key: int(value)
        for key, value in dict(usage).items()
        if isinstance(value, int)
    }


def _to_tool_requests(tool_calls: list[Any]) -> list[ToolRequest]:
    requests: list[ToolRequest] = []
    for index, call in enumerate(tool_calls):
        if _field(call, "type") != "function_call":
            continue

        call_id = _field(call, "call_id", _field(call, "id", str(index)))
        name = _field(call, "name", "")
        arguments = _field(call, "arguments", {})
        if isinstance(arguments, str):
            try:
                arguments = loads(arguments)
            except ValueError:
                arguments = {"value": arguments}

        requests.append(
            ToolRequest(
                id=str(call_id),
                name=str(name),
                arguments=dict(arguments),
            )
        )
    return requests


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


__all__ = [
    "OpenAILLM",
    "create_openai_llm",
]
