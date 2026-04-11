from typing import Any
from broad.llm.base import LLM

class OpenAILLM(LLM):
    """
    LLM for Open AI
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "gpt-5.4-nano",
    ):
        from openai import AsyncOpenAI
        super().__init__(api_key, api_base, default_model)

        self._client=AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
            max_retries=0
        );

    def _build_request(
            self,
            input: list[dict[str, Any]],
            model: str | None,
            max_tokens: int,
            temperature: float,
        ) -> dict[str, Any]:
        
        request = {
            "model": self._ensure_model(model),
            "max_output_tokens": max(1, max_tokens),
            "input": input,
            "store": False,
            "stream": False,
            "temperature": temperature
        }

        return request

    async def prompt(
        self,
        input: str | list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        request = self._build_request(input, model, max_tokens, temperature)

        response = await self._client.responses.create(**request)

        print(response)