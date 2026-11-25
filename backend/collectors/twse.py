from __future__ import annotations

import re
import time
from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from backend.config import Symbol
from backend.models import DataStatus, MarketRecord

TAIPEI = ZoneInfo("Asia/Taipei")
OPENAPI = "https://openapi.twse.com.tw/v1"


def _number(value: Any) -> float | None:
    if value in (None, "", "--", "-"):
        return None
    cleaned = re.sub(r"[^0-9.+-]", "", str(value).replace(",", ""))
    try:
        return float(cleaned)
    except ValueError:
        return None


def _pick(row: dict, *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


class TwseCollector:
    """Official TWSE OpenAPI closing-data adapter with bounded retries."""

    def __init__(self, client: httpx.Client | None = None, timeout: float = 15.0) -> None:
        self.client = client or httpx.Client(timeout=timeout, headers={"User-Agent": "taiwan-stock-dashboard/1.0"})

    def _get(self, path: str) -> list[dict]:
        error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.get(f"{OPENAPI}{path}")
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, list):
                    raise ValueError("TWSE response was not a list")
                return payload
            except (httpx.HTTPError, ValueError) as exc:
                error = exc
                if attempt < 2:
                    time.sleep(0.4 * (2**attempt))
        raise RuntimeError(f"TWSE request failed for {path}: {error}")

    def collect(self, symbols: list[Symbol], scheduled_time: str, now: datetime | None = None) -> list[MarketRecord]:
        now = now or datetime.now(TAIPEI)
        stocks = self._get("/exchangeReport/STOCK_DAY_ALL")
        indices = self._get("/exchangeReport/MI_INDEX")
        stock_by_code = {str(_pick(r, "Code", "證券代號")).strip(): r for r in stocks}
        records: list[MarketRecord] = []
        for item in symbols:
            if item.kind == "index":
                row = next((r for r in indices if "發行量加權股價指數" in str(_pick(r, "指數", "Index", "Name"))), None)
            else:
                row = stock_by_code.get(item.symbol)
            records.append(self._normalize(item, row, scheduled_time, now))
        return records

    def _normalize(self, item: Symbol, row: dict | None, scheduled_time: str, now: datetime) -> MarketRecord:
        if row is None:
            return MarketRecord(
                record_id=f"{now.date()}-{scheduled_time}-{item.symbol}", symbol=item.symbol,
                symbol_name=item.name, market=item.market, trading_date=now.date(), scheduled_time=scheduled_time,
                retrieved_at=now, data_source="TWSE OpenAPI", data_status=DataStatus.UNAVAILABLE,
            )
        last = _number(_pick(row, "ClosingPrice", "收盤價", "ClosingIndex", "收盤指數"))
        change = _number(_pick(row, "Change", "漲跌價差", "ChangeAmount", "漲跌點數"))
        previous = round(last - change, 4) if last is not None and change is not None else None
        return MarketRecord(
            record_id=f"{now.date()}-{scheduled_time}-{item.symbol}", symbol=item.symbol,
            symbol_name=item.name, market=item.market, trading_date=now.date(), scheduled_time=scheduled_time,
            market_data_time=now, retrieved_at=now,
            open=_number(_pick(row, "OpeningPrice", "開盤價", "OpeningIndex", "開盤指數")),
            high=_number(_pick(row, "HighestPrice", "最高價", "HighestIndex", "最高指數")),
            low=_number(_pick(row, "LowestPrice", "最低價", "LowestIndex", "最低指數")),
            last_price=last, previous_close=previous,
            volume=int(_number(_pick(row, "TradeVolume", "成交股數", "TradeVolume(Shares)")) or 0),
            turnover=_number(_pick(row, "TradeValue", "成交金額")), data_source="TWSE OpenAPI",
            data_status=DataStatus.OK if last is not None else DataStatus.UNAVAILABLE,
        )
