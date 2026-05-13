import asyncio
from typing import Annotated

import pytest

from agent.tools import FunctionAgentTool
from llm import FinishReason, LLMProvider, OpenAILLM, ToolRequest, create_llm
from llm.base import _parse_provider


def _run(coro):
    return asyncio.run(coro)


class FakeOpenAIResponses:
    def __init__(self, response):
        self.response = response
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return self.response


class FakeOpenAIClient:
    def __init__(self, response):
        self.responses = FakeOpenAIResponses(response)


class FakeOpenAIResponse:
    def __init__(self, output_text=None, output=None, status="completed", usage=None, incomplete_details=None):
        self.output_text = output_text
        self.output = output or []
        self.status = status
        self.usage = usage
        self.incomplete_details = incomplete_details


def test_openai_llm_invokes_response(monkeypatch):
    client = FakeOpenAIClient(
        FakeOpenAIResponse(
            output_text="pong",
            usage={"input_tokens": 3, "output_tokens": 4, "total_tokens": 7},
        )
    )
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: client)
    llm = OpenAILLM(default_model="gpt-test")

    response = _run(
        llm.invoke(
            [{"role": "user", "content": "Ping"}],
            max_tokens=128,
            temperature=0.2,
            reasoning="low",
        )
    )

    assert response.content == "pong"
    assert response.finish_reason is FinishReason.STOP
    assert response.usage == {"input_tokens": 3, "output_tokens": 4, "total_tokens": 7}
    assert client.responses.kwargs == {
        "model": "gpt-test",
        "input": [{"role": "user", "content": "Ping"}],
        "max_output_tokens": 128,
        "temperature": 0.2,
        "reasoning": {"effort": "low"},
    }


def test_openai_llm_accepts_agent_tools_on_invoke(monkeypatch):
    def search(query: Annotated[str, "Search query."]) -> str:
        """Search indexed documents."""
        return query

    tool_calls = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "search",
            "arguments": '{"query": "python"}',
        }
    ]
    client = FakeOpenAIClient(
        FakeOpenAIResponse(
            output=tool_calls,
        )
    )
    monkeypatch.setattr("openai.AsyncOpenAI", lambda **kwargs: client)
    llm = OpenAILLM(default_model="gpt-test")

    response = _run(
        llm.invoke(
            [{"role": "user", "content": "Search for python"}],
            tools=[FunctionAgentTool.from_function(search)],
        )
    )

    assert response.content is None
    assert response.finish_reason is FinishReason.TOOL_CALLS
    assert response.tool_calls == [ToolRequest(id="call_1", name="search", arguments={"query": "python"})]
    assert client.responses.kwargs["tools"][0]["type"] == "function"
    assert client.responses.kwargs["tools"][0]["name"] == "search"


def test_parse_provider_accepts_enum_and_string():
    assert _parse_provider(LLMProvider.OPENAI) is LLMProvider.OPENAI
    assert _parse_provider("ollama") is LLMProvider.OLLAMA


def test_parse_provider_rejects_unknown_provider():
    with pytest.raises(ValueError):
        _parse_provider("unknown")


def test_create_llm_rejects_unknown_provider_before_importing_provider_packages():
    with pytest.raises(ValueError):
        create_llm("unknown", "model")


def test_create_llm_rejects_unimplemented_provider():
    with pytest.raises(NotImplementedError):
        create_llm(LLMProvider.OLLAMA, "model")

def test_openai_api():
    llm = OpenAILLM(default_model="gpt-5.4-mini")
    response = _run(llm.invoke(
        [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Explain what a Python dataclass is."},
        ],
        max_tokens=512,
        temperature=0.2,
    ))
    print(response.content)
    print(response.finish_reason)
    print(response.usage)
