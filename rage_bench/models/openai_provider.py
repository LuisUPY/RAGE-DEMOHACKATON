"""OpenAI chat-completions provider."""

from __future__ import annotations

import os

from .base import LLMModel, Message


class OpenAIModel(LLMModel):
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.0):
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - exercised only without the SDK
            raise ImportError(
                "The 'openai' package is required for the openai provider. "
                "Install it with: pip install openai"
            ) from exc

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set. Add it to your environment or .env file.")

        self._client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        self.name = f"openai:{model_name}"

    def generate(self, messages: list[Message]) -> str:
        resp = self._client.chat.completions.create(
            model=self.model_name,
            temperature=self.temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content or ""
