"""Command-line interface for the RAGE jailbreak benchmark."""

from __future__ import annotations

import argparse
import sys

from rich.console import Console

from .dataset import load_attacks
from .models import get_model
from .report import build_report, render_failures, render_report, save_report
from .runner import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rage-bench",
        description=(
            "Measure how susceptible an LLM is to jailbreak / prompt-injection attacks. "
            "Susceptibility is measured with harmless canary targets only."
        ),
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="LLM provider: mock | openai | anthropic (default: mock)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=(
            "Model name / mock profile. For mock: vulnerable | guarded | hardened. "
            "For openai/anthropic: the model id."
        ),
    )
    parser.add_argument(
        "--dataset",
        default=None,
        help="Path to a custom attacks JSON file (defaults to the bundled dataset).",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to write the full JSON report.",
    )
    parser.add_argument(
        "--show-failures",
        action="store_true",
        help="Print sample successful attacks for qualitative insight.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Load .env if present so OPENAI_API_KEY / ANTHROPIC_API_KEY are picked up.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass

    args = build_parser().parse_args(argv)
    console = Console()

    cases = load_attacks(args.dataset)
    try:
        model = get_model(args.provider, args.model)
    except (ValueError, RuntimeError, ImportError) as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        return 2

    console.print(
        f"Running [bold]{len(cases)}[/bold] attack cases against "
        f"[bold]{model.name}[/bold]...\n"
    )

    def _progress(result) -> None:
        mark = "[red]COMPROMISED[/red]" if result.succeeded else "[green]held[/green]"
        console.print(f"  {result.case_id:<8} {result.technique:<28} {mark}")

    results = run_benchmark(model, cases, on_result=_progress)
    report = build_report(model.name, results)

    console.print()
    render_report(report, console)
    if args.show_failures:
        render_failures(report, console)

    if args.output:
        path = save_report(report, args.output)
        console.print(f"\nFull report written to [bold]{path}[/bold]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
