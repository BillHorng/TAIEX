from __future__ import annotations

import argparse
import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from backend.calendar import CalendarData, TradingCalendarEngine
from backend.collectors import TwseCollector
from backend.config import ROOT, load_schedule, load_symbols
from backend.integrations import GooglePublisher
from backend.models import CalendarStatus, DataStatus, MarketRecord, RunSummary
from backend.storage import LocalStorage
from backend.validators import validate_records

TAIPEI = ZoneInfo("Asia/Taipei")


def load_calendar(year: int) -> CalendarData:
    path = ROOT / "data" / "calendar" / f"twse-{year}.json"
    if not path.exists():
        return CalendarData(year=year, known=False)
    payload = json.loads(path.read_text(encoding="utf-8"))
    values = lambda key: {date.fromisoformat(value) for value in payload.get(key, [])}
    return CalendarData(year=year, holidays=values("holidays"), trading_days=values("trading_days"),
                        special_closures=values("special_closures"), known=True)


def run(scheduled_time: str, *, force: bool = False, publish: bool = False, now: datetime | None = None,
        collector: TwseCollector | None = None, storage: LocalStorage | None = None) -> RunSummary:
    now = now or datetime.now(TAIPEI)
    schedule = load_schedule()
    calendar = TradingCalendarEngine(load_calendar(now.year))
    calendar_status, note = calendar.classify(now.date())
    records: list[MarketRecord] = []
    warnings: list[str] = []
    status = "SKIPPED"
    if calendar_status == CalendarStatus.TRADING_DAY or force:
        try:
            records = (collector or TwseCollector(
                timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15")),
                delayed_minutes=int(schedule.get("freshness_minutes", 30)),
                stale_minutes=int(schedule.get("stale_minutes", 120)),
            )).collect(
                load_symbols(), scheduled_time, now
            )
            warnings = validate_records(records)
            wrong_dates = sorted({row.trading_date.isoformat() for row in records if row.trading_date != now.date()})
            if wrong_dates:
                warnings.append(f"TWSE returned a different trading date: {', '.join(wrong_dates)}")
                status = "FAILED"
            elif records and all(row.data_status == DataStatus.UNAVAILABLE for row in records):
                warnings.append("All tracked symbols are unavailable")
                status = "FAILED"
            else:
                status = "SUCCESS"
        except Exception as exc:  # boundary: retain an auditable failed run
            warnings.append(str(exc))
            status = "FAILED"
    summary = RunSummary(
        run_id=str(uuid.uuid4()), generated_at=now, trading_date=now.date(), scheduled_time=scheduled_time,
        calendar_status=calendar_status, calendar_note=note, pipeline_status=status, records=records,
        warnings=warnings, sources=sorted({row.data_source for row in records}) or ["TWSE MIS"],
    )
    storage = storage or LocalStorage(ROOT / "data" / "output", ROOT / "frontend" / "public" / "data" / "latest.json")
    csv_path, json_path = storage.write(summary)
    if publish and status == "SUCCESS":
        try:
            GooglePublisher().publish(csv_path, json_path, summary)
        except Exception as exc:
            summary.pipeline_status = "PARTIAL_SUCCESS"
            summary.warnings.append(f"Google publish failed: {exc}")
            storage.write(summary)
    return summary


def cli() -> int:
    parser = argparse.ArgumentParser(description="Collect and publish TWSE market data")
    parser.add_argument("--scheduled-time", default=datetime.now(TAIPEI).strftime("%H:%M"))
    parser.add_argument("--force", action="store_true", help="collect even when calendar gate is closed")
    parser.add_argument("--publish-google", action="store_true")
    args = parser.parse_args()
    result = run(args.scheduled_time, force=args.force, publish=args.publish_google)
    print(result.model_dump_json(indent=2))
    return 1 if result.pipeline_status == "FAILED" else 0


if __name__ == "__main__":
    raise SystemExit(cli())
