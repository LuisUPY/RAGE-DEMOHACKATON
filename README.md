# RAGE-DEMOHACKATON

Demo del proyecto **RAGE** — *Retrieval-Augmented Governance Engine*.

This repository currently contains the **threat-measurement harness** for RAGE: a tool
that quantifies *how serious* the prompt-injection / jailbreak problem is by measuring
how often attacks succeed against an LLM. These numbers motivate (and later, will
benchmark) the RAGE defense layer.

## Safety-first measurement

Jailbreak susceptibility is measured with **harmless canary targets**, never real harmful
content. Each test case gives the model a rule it must follow:

- a confidential **canary code** it must never reveal (e.g. `ZEPHYR-7781`), or
- a forbidden-but-harmless **token** it must never output (e.g. `BANANA`).

The attack then tries to make the model break that rule. An attack **succeeds** only when
the harmless canary leaks. This faithfully measures vulnerability to injection/jailbreak
*framings* without ever producing dangerous output.

## What it measures

For a model under test, the harness reports:

- **Attack Success Rate (ASR)** — overall and per attack category.
- **Severity score (0–100)** — severity-weighted vulnerability, mapped to a risk band
  (`NONE` / `LOW` / `ELEVATED` / `CRITICAL`).

Attack categories include: direct instruction override, role-play/DAN jailbreaks,
indirect prompt injection (via documents / spoofed tool output), obfuscation
(base64 / leetspeak), refusal suppression, social engineering, indirection, context
overload, and behavior hijacking.

## Setup

### With [uv](https://docs.astral.sh/uv/) (recommended)

`uv` manages the environment for you — you never create or activate a virtualenv by hand.

```bash
uv sync --extra llm   # installs everything (omit --extra llm for the mock provider only)
```

Then prefix any command with `uv run`:

```bash
uv run rage-bench --provider mock --model vulnerable --show-failures
uv run pytest
```

> uv keeps the environment in `.venv` by default; you don't have to touch it. To put it
> elsewhere, set `UV_PROJECT_ENVIRONMENT=/path/to/env`.

**Troubleshooting `error: Failed to spawn: ruff` (or `pytest`)** — this means the dev
tools weren't installed, which happens on **older uv** that ignores the
`[dependency-groups]` table. Fix it either way:

```bash
uv self update            # update uv (dependency groups need uv >= 0.4.27), then: uv sync
# --- or, works on any uv version: ---
uv sync --extra dev       # installs ruff + pytest as an extra
# --- or, run ruff without installing it at all: ---
uvx ruff check .
```

### With pip + venv (alternative)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

Run against the offline mock model (no API key needed):

```bash
# Simulated weak model — expect a high ASR
uv run rage-bench --provider mock --model vulnerable --show-failures

# Simulated partially-defended model
uv run rage-bench --provider mock --model guarded

# Simulated strong defense (RAGE-style) — expect 0%
uv run rage-bench --provider mock --model hardened
```

Run against a real LLM (set the key first):

```bash
export OPENAI_API_KEY=sk-...        # or ANTHROPIC_API_KEY=...
uv run rage-bench --provider openai --model gpt-4o-mini --output results/openai.json
uv run rage-bench --provider anthropic --model claude-3-5-sonnet-latest
```

`--output PATH` writes the full per-case JSON report. `--dataset PATH` runs a custom
attack set (same schema as `rage_bench/data/attacks.json`).

> `rage-bench` is the installed console script. If you used the pip+venv path instead of
> uv, run it the same way after activating the venv, or use `python -m rage_bench`.
>
> The `mock` provider is a deterministic **simulator** for validating the harness offline;
> its numbers are illustrative. Use a real provider to measure an actual model.

## Development

```bash
uv run ruff check .   # lint
uv run pytest         # tests
```
