from anthropic import Anthropic

from shared.providers.base import LLMProvider, Message


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
        response = self.client.messages.create(
            model=self.model,
            messages=[
                {"role": message.role, "content": message.content}
                for message in messages
            ],
            system=system or None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.content[0].text
