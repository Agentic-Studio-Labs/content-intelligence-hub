from providers.base import LLMProvider, Message
from providers.anthropic import AnthropicProvider
from unittest.mock import patch, MagicMock


def test_message_creation():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_provider_interface():
    assert hasattr(LLMProvider, "complete")
    assert hasattr(LLMProvider, "stream")


def test_anthropic_provider_init():
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-6")
    assert provider.model == "claude-sonnet-4-6"


@patch("providers.anthropic.Anthropic")
def test_anthropic_complete(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Generated response")]
    mock_client.messages.create.return_value = mock_response
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="sk-test")
    result = provider.complete(
        messages=[Message(role="user", content="hello")],
        system="You are helpful.",
    )
    assert result == "Generated response"
    mock_client.messages.create.assert_called_once()
