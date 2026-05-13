from __future__ import annotations

from json import loads
from typing import Any

from agent.tools import AgentTool
from llm.base import FinishReason, LLM, LLMResponse, ToolRequest

from openai import AsyncOpenAI


class OpenAILLM(LLM):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_url: str | None = None,
        default_model: str = "gpt-5-mini",
        default_temperature: float = 0.7,
    ) -> None:
        self._default_model = default_model
        self._default_temperature = default_temperature

        self._client = AsyncOpenAI(
            api_key = api_key,
            base_url = api_url or None,
            max_retries = 0,
        )

    async def invoke(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[AgentTool] | None = None,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float  | None = None,
        reasoning: str | None = None,
    ) -> LLMResponse:
        model = model or self._default_model
        kwargs: dict[str, Any] = {
            "model": model,
            "input": messages,
            "max_output_tokens": max_tokens,
        }

        if _is_model_support_temperature(model, reasoning):
            kwargs["temperature"] = temperature or self._default_temperature

        if tools:
            kwargs["tools"] = [_to_openai_tool(tool) for tool in tools]
        if reasoning:
            kwargs["reasoning"] = {"effort": reasoning}

        response = await self._client.responses.create(**kwargs)
        return _to_llm_response(response)


def _is_model_support_temperature(
    model_name: str,
    reasoning_effort: str | None = None,
) -> bool:
    if reasoning_effort and reasoning_effort.lower() != "none":
        return False
    name = model_name.lower()
    return not any(token in name for token in ("gpt-5", "o1", "o3", "o4"))

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
]
