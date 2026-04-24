from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RawContent:
    path: str
    title: str
    body: str
    content_type: str = ""
    metadata: dict = field(default_factory=dict)


class ContentSource(ABC):
    @abstractmethod
    def extract(self, path: str) -> RawContent | None: ...

    @abstractmethod
    def supported_extensions(self) -> set[str]: ...
