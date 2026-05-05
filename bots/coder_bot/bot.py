def coder_bot_main():
    print("coder bot main entry")

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

def _run_bot():
    pass