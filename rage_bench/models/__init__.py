"""LLM provider abstraction and factory."""

from __future__ import annotations

from .base import LLMModel, Message
from .mock import MockModel

__all__ = ["LLMModel", "Message", "MockModel", "get_model"]


def get_model(provider: str, model_name: str | None = None, **kwargs) -> LLMModel:
    """Construct a model client for the given provider.

    Supported providers:
      - "mock": offline deterministic simulator (no API key required)
      - "openai": OpenAI Chat Completions (requires OPENAI_API_KEY)
      - "anthropic": Anthropic Messages (requires ANTHROPIC_API_KEY)
    """
    provider = provider.lower()
    if provider == "mock":
        return MockModel(profile=model_name or "guarded", **kwargs)
    if provider == "openai":
        from .openai_provider import OpenAIModel

        return OpenAIModel(model_name=model_name or "gpt-4o-mini", **kwargs)
    if provider == "anthropic":
        from .anthropic_provider import AnthropicModel

        return AnthropicModel(model_name=model_name or "claude-3-5-sonnet-latest", **kwargs)
    raise ValueError(f"Unknown provider: {provider!r}. Use 'mock', 'openai', or 'anthropic'.")
