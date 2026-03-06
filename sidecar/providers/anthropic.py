from anthropic import Anthropic
from providers.base import LLMProvider, Message


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def complete(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def stream(
        self,
        messages: list[Message],
        system: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        api_messages = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system:
            kwargs["system"] = system
        with self.client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
