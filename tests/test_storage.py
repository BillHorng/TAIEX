import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.models import MarketRecord, RunSummary
from backend.storage import LocalStorage


def summary(price: float) -> RunSummary:
    now = datetime(2026, 11, 25, 15, tzinfo=ZoneInfo("Asia/Taipei"))
    record = MarketRecord(
        record_id="2026-11-25-15:00-0050", symbol="0050", symbol_name="元大台灣50",
        trading_date=date(2026, 11, 25), scheduled_time="15:00", retrieved_at=now,
        last_price=price, previous_close=90, data_source="fixture",
    )
    return RunSummary(
        run_id="run", generated_at=now, trading_date=now.date(), scheduled_time="15:00",
        calendar_status="TRADING_DAY", calendar_note="fixture", pipeline_status="SUCCESS", records=[record],
    )


def test_history_upserts_same_record_id(tmp_path) -> None:
    store = LocalStorage(tmp_path / "output", tmp_path / "public" / "latest.json")
    store.write(summary(91))
    store.write(summary(92))
    history = json.loads((tmp_path / "public" / "history.json").read_text(encoding="utf-8"))
    assert len(history["records"]) == 1
    assert history["records"][0]["last_price"] == 92


def test_failed_run_preserves_last_successful_snapshot(tmp_path) -> None:
    store = LocalStorage(tmp_path / "output", tmp_path / "public" / "latest.json")
    store.write(summary(91))
    failed = summary(0)
    failed.pipeline_status = "FAILED"
    failed.records = []
    store.write(failed)
    latest = json.loads((tmp_path / "public" / "latest.json").read_text(encoding="utf-8"))
    status = json.loads((tmp_path / "public" / "run-status.json").read_text(encoding="utf-8"))
    assert latest["records"][0]["last_price"] == 91
    assert status["pipeline_status"] == "FAILED"
