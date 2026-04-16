from typing import Any
from broad.llm.base import LLM

class OllamaLocal(LLM):
    """
    LLM For Ollama
    """

    def __init__(
        self,
        api_base: str = "http://localhost:11434",
        default_model: str | None = None
    ):
        super().__init__(None, api_base, default_model)

        from ollama import Client
        self._client = Client(
            host=api_base
        )
    
    def prompt(
        self,
        input: str | list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        response = self._client.chat(model=self._ensure_model(model), messages=input)
        print(response)