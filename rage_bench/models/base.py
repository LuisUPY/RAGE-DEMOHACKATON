"""Base model interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMModel(ABC):
    """Minimal chat-model interface used by the benchmark runner."""

    #: Human-readable identifier, e.g. "openai:gpt-4o-mini".
    name: str

    @abstractmethod
    def generate(self, messages: list[Message]) -> str:
        """Return the model's text response to a list of chat messages."""
        raise NotImplementedError
