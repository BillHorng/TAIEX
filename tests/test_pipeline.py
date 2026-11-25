from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import Symbol
from backend.main import run
from backend.models import MarketRecord
from backend.storage import LocalStorage


class FixtureCollector:
    def collect(self, symbols: list[Symbol], scheduled_time: str, now: datetime) -> list[MarketRecord]:
        return [MarketRecord(
            record_id=f"fixture-{s.symbol}", symbol=s.symbol, symbol_name=s.name, market=s.market,
            trading_date=now.date(), scheduled_time=scheduled_time, retrieved_at=now,
            last_price=100, previous_close=99, data_source="fixture",
        ) for s in symbols]


def test_pipeline_success(tmp_path) -> None:
    storage = LocalStorage(tmp_path / "output", tmp_path / "public" / "latest.json")
    result = run("15:00", now=datetime(2026, 11, 25, 15, tzinfo=ZoneInfo("Asia/Taipei")), collector=FixtureCollector(), storage=storage)
    assert result.pipeline_status == "SUCCESS"
    assert len(result.records) == 3

