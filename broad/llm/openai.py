import logging
from typing import Any
from broad.llm.base import LLM

# from typing import TYPE_CHECKING

# if TYPE_CHECKING:
#     from openai.types.responses import Response as OpenAIResponse

from openai.types.responses import Response as OpenAIResponse

from broad.llm.base import LLMResponse

class OpenAI(LLM):
    """
    LLM for Open AI
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_base: str | None = None,
        default_model: str = "gpt-5.4-nano",
    ):
        from openai import OpenAI
        super().__init__(api_key, api_base, default_model)

        self._client=OpenAI(
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

    def prompt(
        self,
        input: str | list[dict[str, Any]],
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7
    ):
        request = self._build_request(input, model, max_tokens, temperature)

        response = self._client.responses.create(**request)

        print(parse_response_output(response))

def parse_response_output(response: OpenAIResponse) -> LLMResponse:
    """Extract from OpenAIResponse to LLMPresponse"""

    model_dump = getattr(response, "model_dump", None)
    response = model_dump() if callable(model_dump) else vars(response)

    output = response.get("output") or []
    text_contents: list[str] = []
    
    for item in output:
        if not isinstance(item, dict):
            model_dump = getattr(item, "model_dump", None)
            item = model_dump() if callable(model_dump) else vars(item)
        
        item_type = item.get("type")
        if item_type == "message":
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    model_dump = getattr(content, "model_dump", None)
                    content = model_dump() if callable(model_dump) else vars(content)
                if content.get("type") == "output_text":
                    text_contents.append(content.get("text") or "")
        else:
            logging.warning("unhandle OpenAI response output: %s", item)

    usage = response.get("usage") or {}
    if not isinstance(usage, dict):
        dump = getattr(usage, "model_dump", None)
        usage = dump() if callable(dump) else vars(usage)

    token_usage = {}
    if usage:
        token_usage = {
            "input_tokens": int(usage.get("input_tokens") or 0),
            "output_tokens": int(usage.get("output_tokens") or 0),
            "total_tokens": int(usage.get("total_tokens") or 0),
        }
    
    status = response.get("status")

    return LLMResponse(
        responseId=response.get("id") or None,
        content="".join(text_contents) or None,
        token_usage=token_usage,
        status=status,
    )
