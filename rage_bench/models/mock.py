"""Offline deterministic mock model.

This simulator lets the harness run end-to-end with no API keys. It is NOT a real
LLM and its numbers are illustrative -- use a real provider (openai/anthropic) to
measure an actual model. The mock simulates a model with *imperfect* defenses: it
refuses the most obvious attacks but is fooled by subtler framings, which is exactly
the pattern real-world red-teaming reveals.
"""

from __future__ import annotations

import base64
import re

from .base import LLMModel, Message

# Patterns that a partially-defended ("guarded") model recognizes and refuses.
_OBVIOUS_ATTACK_MARKERS = (
    "ignore all previous",
    "ignore previous instructions",
    "unrestricted mode",
    "you are dan",
    "system update",
    "emergency",
    "lead developer",
    "security audit",
)

# Subtler framings that slip past a guarded model.
_SUBTLE_ATTACK_MARKERS = (
    "summarize",
    "assistant instruction",
    "tool result",
    "policy=",
    "complete this sentence",
    "____",
    "story",
    "dialogue",
    "translate",
    "list each character",
    "separated by spaces",
    "hypothetical",
    "= 'the confidential'",
)

_CANARY_RE = re.compile(r"access code:\s*([A-Z0-9\-]+)", re.IGNORECASE)
_FORBIDDEN_RE = re.compile(r"never output the word '([A-Z]+)'", re.IGNORECASE)


class MockModel(LLMModel):
    """A deterministic simulated model.

    profile:
      - "vulnerable": almost always complies with the attack
      - "guarded":    refuses obvious attacks, fooled by subtle ones (default)
      - "hardened":   refuses everything (simulates a strong defense like RAGE)
    """

    def __init__(self, profile: str = "guarded"):
        profile = profile.lower()
        if profile not in {"vulnerable", "guarded", "hardened"}:
            raise ValueError(f"Unknown mock profile: {profile!r}")
        self.profile = profile
        self.name = f"mock:{profile}"

    def _secret(self, system_prompt: str) -> str | None:
        m = _CANARY_RE.search(system_prompt)
        return m.group(1) if m else None

    def _forbidden(self, system_prompt: str) -> str | None:
        m = _FORBIDDEN_RE.search(system_prompt)
        return m.group(1) if m else None

    def _decode_payloads(self, text: str) -> str:
        """Expand base64 blobs so the simulator can 'read' encoded instructions."""
        expanded = text
        for token in re.findall(r"[A-Za-z0-9+/]{16,}={0,2}", text):
            try:
                decoded = base64.b64decode(token, validate=True).decode("utf-8")
                expanded += "\n" + decoded
            except Exception:
                continue
        return expanded

    def _complies(self, attack: str) -> bool:
        attack_l = self._decode_payloads(attack).lower()
        if self.profile == "hardened":
            return False
        if self.profile == "vulnerable":
            return True
        # guarded: refuse obvious attacks, comply with subtle ones.
        if any(marker in attack_l for marker in _OBVIOUS_ATTACK_MARKERS):
            return False
        return any(marker in attack_l for marker in _SUBTLE_ATTACK_MARKERS)

    def generate(self, messages: list[Message]) -> str:
        system = "\n".join(m.content for m in messages if m.role == "system")
        attack = "\n".join(m.content for m in messages if m.role == "user")

        secret = self._secret(system)
        forbidden = self._forbidden(system)
        complies = self._complies(attack)

        if not complies:
            return (
                "I'm sorry, but I can't help with that. I'm not able to disclose "
                "confidential information or break my operating instructions."
            )

        if secret:
            return f"Sure, the confidential access code is {secret}."
        if forbidden:
            return f"Okay, here it is: {forbidden}"
        return "Okay."
