from enum import Enum
from typing import Optional

from langchain_core.language_models.chat_models import BaseChatModel

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    MISTRAL = "mistral"
    COHERE = "cohere"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"

def init_llm_client(
    provider: LLMProvider,
    model: str,
    temperature: float = 0,
    base_url: Optional[str] = None,
) -> BaseChatModel:
    match provider:
        case LLMProvider.OPENAI:
            from langchain_openai import ChatOpenAI
            from utils.env import load_env
            load_env()
            return ChatOpenAI(model=model, temperature=temperature)
        case LLMProvider.OLLAMA:
            from langchain_ollama import ChatOllama
            return ChatOllama(model=model, base_url=base_url or "http://localhost:11434", temperature=temperature)
        case _:
            raise ValueError(f"Unsupported LLM provider: {provider}")


def coder_bot_main(
    prompt: str = "Hello, can you return a greeting?",
    provider: str = LLMProvider.OPENAI.value,
    model: str = "gpt-5.4-nano",
    temperature: float = 0,
    base_url: Optional[str] = None,
) -> str:
    from .github import sample_fetch_github_issues
    sample_fetch_github_issues()

    # llm_provider = _parse_provider(provider)
    # llm = init_llm_client(
    #     provider=llm_provider,
    #     model=model,
    #     temperature=temperature,
    #     base_url=base_url,
    # )

    # response = llm.invoke(prompt)
    # content = _response_content(response)
    # print(content)
    # return content


def _parse_provider(provider: str) -> LLMProvider:
    try:
        return LLMProvider(provider.lower())
    except ValueError as exc:
        supported = ", ".join(p.value for p in LLMProvider)
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported providers: {supported}") from exc


def _response_content(response) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


class LLM:
    _RETRYABLE_STATUS_CODES = frozenset({408, 409, 429})
