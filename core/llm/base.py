from enum import Enum
from abc import abstractmethod, ABC

class MessageRole(str, Enum):
    """Message role."""

    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"

class PromptMsg:
    pass

class LLM(ABC):
    pass
