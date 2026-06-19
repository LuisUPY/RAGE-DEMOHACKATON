"""Anthropic messages provider."""

from __future__ import annotations

import os

from .base import LLMModel, Message


class AnthropicModel(LLMModel):
    def __init__(self, model_name: str = "claude-3-5-sonnet-latest", temperature: float = 0.0):
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - exercised only without the SDK
            raise ImportError(
                "The 'anthropic' package is required for the anthropic provider. "
                "Install it with: pip install anthropic"
            ) from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your environment or .env file."
            )

        self._client = Anthropic(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.name = f"anthropic:{model_name}"

    def generate(self, messages: list[Message]) -> str:
        system = "\n".join(m.content for m in messages if m.role == "system")
        chat = [
            {"role": m.role, "content": m.content} for m in messages if m.role != "system"
        ]
        resp = self._client.messages.create(
            model=self.model_name,
            max_tokens=1024,
            temperature=self.temperature,
            system=system or None,
            messages=chat,
        )
        parts = [block.text for block in resp.content if getattr(block, "type", None) == "text"]
        return "".join(parts)
