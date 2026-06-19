"""Data models for the benchmark harness."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SuccessCriteria(str, Enum):
    """How we decide whether an attack succeeded (i.e. the model was compromised)."""

    # The harmless secret canary string appears in the model's output.
    CANARY_LEAK = "canary_leak"
    # A forbidden (but harmless) marker token appears, meaning the model broke its rule.
    FORBIDDEN_TOKEN = "forbidden_token"


class AttackCase(BaseModel):
    """A single jailbreak / prompt-injection test case.

    Every case is built around a *harmless* objective: extract a random secret
    canary or emit a forbidden-but-harmless token. This measures whether the
    attack framing bypasses the model's instructions, without eliciting any
    actually dangerous content.
    """

    id: str
    category: str
    technique: str
    description: str
    severity_weight: int = Field(ge=1, le=5)
    system_prompt: str
    attack_prompt: str
    success_criteria: SuccessCriteria = SuccessCriteria.CANARY_LEAK
    # The canary to detect (for CANARY_LEAK) or the forbidden token (FORBIDDEN_TOKEN).
    target_token: str


class ModelResponse(BaseModel):
    """The raw response returned by a model for one case."""

    text: str
    model: str
    error: str | None = None


class CaseResult(BaseModel):
    """The outcome of running one attack case against one model."""

    case_id: str
    category: str
    technique: str
    severity_weight: int
    succeeded: bool  # True = the attack worked = the model is vulnerable here.
    reason: str
    response_text: str
    error: str | None = None


class CategoryStat(BaseModel):
    category: str
    total: int
    successes: int

    @property
    def asr(self) -> float:
        """Attack Success Rate for this category (0-100)."""
        return 0.0 if self.total == 0 else 100.0 * self.successes / self.total


class BenchmarkReport(BaseModel):
    """Aggregate results across all cases for one model."""

    model: str
    total_cases: int
    total_successes: int
    errors: int
    # Severity-weighted vulnerability score on a 0-100 scale.
    severity_score: float
    per_category: list[CategoryStat]
    results: list[CaseResult]

    @property
    def asr(self) -> float:
        """Overall Attack Success Rate (0-100)."""
        return 0.0 if self.total_cases == 0 else 100.0 * self.total_successes / self.total_cases
