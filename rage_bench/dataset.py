"""Loading of the attack-case dataset."""

from __future__ import annotations

import json
from pathlib import Path

from .schema import AttackCase

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_DATASET = DATA_DIR / "attacks.json"


def load_attacks(path: str | Path | None = None) -> list[AttackCase]:
    """Load attack cases from a JSON file (defaults to the bundled dataset)."""
    dataset_path = Path(path) if path is not None else DEFAULT_DATASET
    raw = json.loads(dataset_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError(f"Dataset {dataset_path} must contain a JSON array of cases")
    return [AttackCase.model_validate(item) for item in raw]


def categories(cases: list[AttackCase]) -> list[str]:
    """Return the sorted unique categories present in the dataset."""
    return sorted({c.category for c in cases})
