from datetime import date, datetime
from zoneinfo import ZoneInfo

from backend.models import MarketRecord


def test_record_calculates_change() -> None:
    row = MarketRecord(
        record_id="r1", symbol="0050", symbol_name="元大台灣50", trading_date=date(2026, 11, 25),
        scheduled_time="15:00", retrieved_at=datetime(2026, 11, 25, 15, tzinfo=ZoneInfo("Asia/Taipei")),
        last_price=62.95, previous_close=62.60, data_source="fixture",
    )
    assert row.change_direction == "UP"
    assert row.change_value == 0.35
    assert row.change_percent == 0.5591

