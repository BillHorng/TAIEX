from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

import httpx

URL = "https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule"
TRADING_MARKERS = ("開始交易", "最後交易", "恢復交易", "補行交易")
CLOSED_MARKERS = ("放假", "無交易", "休市", "停止交易")
SPECIAL_MARKERS = ("停止交易", "天然災害", "颱風", "特殊休市")


def roc_date(value: str) -> date:
    digits = re.sub(r"\D", "", value)
    if len(digits) != 7:
        raise ValueError(f"Unexpected ROC date: {value}")
    return date(int(digits[:3]) + 1911, int(digits[3:5]), int(digits[5:7]))


def parse_calendar(rows: list[dict]) -> dict[int, dict[str, set[str]]]:
    years: dict[int, dict[str, set[str]]] = {}
    for row in rows:
        day = roc_date(str(row.get("Date", "")))
        text = f"{row.get('Name', '')} {row.get('Description', '')}"
        bucket = years.setdefault(day.year, {"holidays": set(), "trading_days": set(), "special_closures": set()})
        if any(marker in text for marker in TRADING_MARKERS):
            bucket["trading_days"].add(day.isoformat())
        elif any(marker in text for marker in SPECIAL_MARKERS):
            bucket["special_closures"].add(day.isoformat())
        elif any(marker in text for marker in CLOSED_MARKERS):
            bucket["holidays"].add(day.isoformat())
    return years


def refresh(output_dir: Path, client: httpx.Client | None = None) -> list[Path]:
    response = (client or httpx.Client(timeout=20, headers={"User-Agent": "taiwan-stock-dashboard/2.0"})).get(URL)
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        raise ValueError("TWSE holiday response was empty")
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for year, values in parse_calendar(rows).items():
        path = output_dir / f"twse-{year}.json"
        payload = {"source": URL, "year": year, **{key: sorted(items) for key, items in values.items()}}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        paths.append(path)
    return paths


def cli() -> int:
    parser = argparse.ArgumentParser(description="Refresh deterministic TWSE calendar cache")
    parser.add_argument("--output-dir", type=Path, default=Path("data/calendar"))
    args = parser.parse_args()
    for path in refresh(args.output_dir):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
