from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Symbol:
    symbol: str
    name: str
    market: str
    kind: str


def load_symbols(path: Path = ROOT / "config" / "symbols.yaml") -> list[Symbol]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Symbol(**row) for row in data["symbols"]]


def load_schedule(path: Path = ROOT / "config" / "schedule.yaml") -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))

