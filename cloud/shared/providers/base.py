from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str
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
