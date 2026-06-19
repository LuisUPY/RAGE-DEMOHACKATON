"""Run attack cases against a model and collect results."""

from __future__ import annotations

from collections.abc import Callable

from .evaluator import evaluate
from .models.base import LLMModel, Message
from .schema import AttackCase, CaseResult


def run_case(model: LLMModel, case: AttackCase) -> CaseResult:
    """Run a single attack case against the model."""
    messages = [
        Message(role="system", content=case.system_prompt),
        Message(role="user", content=case.attack_prompt),
    ]
    try:
        response_text = model.generate(messages)
        error = None
    except Exception as exc:  # network/SDK/runtime errors should not abort the run
        response_text = ""
        error = f"{type(exc).__name__}: {exc}"

    if error is not None:
        succeeded, reason = False, f"Skipped (model error): {error}"
    else:
        succeeded, reason = evaluate(case, response_text)

    return CaseResult(
        case_id=case.id,
        category=case.category,
        technique=case.technique,
        severity_weight=case.severity_weight,
        succeeded=succeeded,
        reason=reason,
        response_text=response_text,
        error=error,
    )


def run_benchmark(
    model: LLMModel,
    cases: list[AttackCase],
    on_result: Callable[[CaseResult], None] | None = None,
) -> list[CaseResult]:
    """Run every attack case against the model, returning per-case results."""
    results: list[CaseResult] = []
    for case in cases:
        result = run_case(model, case)
        results.append(result)
        if on_result is not None:
            on_result(result)
    return results
