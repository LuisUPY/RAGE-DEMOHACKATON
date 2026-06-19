# AGENTS.md

## Project

RAGE threat-measurement harness (`rage_bench`): a Python CLI that quantifies an LLM's
susceptibility to jailbreak / prompt-injection attacks using **harmless canary targets**
(no real harmful content is ever requested or produced). See `README.md` for the full
overview and command reference.

## Layout

- `rage_bench/dataset.py` + `rage_bench/data/attacks.json` — attack cases (extend the JSON to add cases).
- `rage_bench/models/` — provider abstraction: `mock` (offline), `openai`, `anthropic`.
- `rage_bench/evaluator.py` — canary/forbidden-token detection (the success metric).
- `rage_bench/runner.py`, `rage_bench/report.py`, `rage_bench/cli.py` — run, aggregate, render.
- `tests/` — pytest suite.

## Cursor Cloud specific instructions

- Standard setup/lint/test/run commands live in `README.md`.
- The project is **uv-native** (`pyproject.toml` + committed `uv.lock`). The preferred
  workflow is `uv sync --extra llm` then `uv run rage-bench ...` / `uv run pytest` /
  `uv run ruff check .` — uv manages the env, no manual `.venv` activation needed. Dev tools
  (`pytest`, `ruff`) are in the `[dependency-groups] dev` group and install by default with
  `uv sync`. Use `--extra llm` (or `--extra openai`/`--extra anthropic`) to install the real
  providers; omit it for mock-only.
- `[dependency-groups]` needs uv >= 0.4.27. On older uv, `uv run ruff`/`pytest` fails with
  "Failed to spawn"; the dev tools are also exposed as a `dev` extra, so `uv sync --extra dev`
  (or `uvx ruff check .`) works on any uv version.
- The cloud **update script** uses pip + a repo-local `.venv` (from `requirements.txt`) so it
  works even if `uv` is absent. If you use that path instead of uv, `source .venv/bin/activate`
  before running tools, or invoke the CLI as `python -m rage_bench`.
- Tests import the package via pytest's `pythonpath = ["."]` (set in `pyproject.toml`), so run
  pytest/CLI from the repo root.
- The `mock` provider is fully offline and needs no secrets — use it to validate the harness
  end-to-end (`--model vulnerable|guarded|hardened`). It is a deterministic simulator, **not**
  a real LLM; its ASR numbers are illustrative only.
- Measuring a **real** model requires an API key: set `OPENAI_API_KEY` (provider `openai`)
  or `ANTHROPIC_API_KEY` (provider `anthropic`). Without a key the real providers exit with
  a clear error (exit code 2) — this is expected, not a bug.
