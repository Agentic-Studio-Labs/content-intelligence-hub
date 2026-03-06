from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class Message:
    role: str  # "user" | "assistant"
    content: str


class LLMProvider(ABC):
    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str: ...

    @abstractmethod
    def stream(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ): ...
