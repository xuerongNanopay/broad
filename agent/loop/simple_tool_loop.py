from typing import Any

from agent.tools import AgentTool
from llm import LLM, LLMResponse, ToolRequest


class SimpleToolLoop:
    def __init__(
        self,
        llm: LLM,
        messages: list[dict[str, Any]],
        tools: list[AgentTool] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        reasoning: str | None = None,
    ):
        self.llm = llm
        self.messages = messages
        self.tools = tools or []
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.reasoning = reasoning

    async def invoke(self) -> LLMResponse:
        history = list(self.messages)
        response = await self.llm.invoke(
            history,
            tools=self.tools,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            reasoning=self.reasoning,
        )

        if not response.tool_calls:
            return response

        history.append(self._assistant_tool_call_message(response))
        for tool_call in response.tool_calls:
            history.append(self._tool_result_message(tool_call, self._invoke_tool(tool_call, self.tools)))

        return await self.llm.invoke(
            history,
            tools=self.tools,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            reasoning=self.reasoning,
        )

    def _invoke_tool(self, tool_call: ToolRequest, tools: list[AgentTool]) -> Any:
        tool = self._find_tool(tool_call.name, tools)
        return tool.exec(**tool_call.arguments)

    @staticmethod
    def _find_tool(name: str, tools: list[AgentTool]) -> AgentTool:
        for tool in tools:
            if tool.name == name:
                return tool

        raise ValueError(f"Tool not found: {name}")

    @staticmethod
    def _assistant_tool_call_message(response: LLMResponse) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": response.content or "",
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                }
                for tool_call in response.tool_calls
            ],
        }

    @staticmethod
    def _tool_result_message(tool_call: ToolRequest, result: Any) -> dict[str, Any]:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.name,
            "content": str(result),
        }


__all__ = ["SimpleToolLoop"]
