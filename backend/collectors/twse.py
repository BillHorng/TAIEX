from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote
from zoneinfo import ZoneInfo

import httpx

from backend.config import Symbol
from backend.models import DataStatus, MarketRecord

TAIPEI = ZoneInfo("Asia/Taipei")
OPENAPI = "https://openapi.twse.com.tw/v1"
MIS_API = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"


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


def _freshness(data_time: datetime | None, now: datetime, delayed_minutes: int, stale_minutes: int) -> DataStatus:
    if data_time is None:
        return DataStatus.UNAVAILABLE
    age_minutes = max(0, (now - data_time).total_seconds() / 60)
    if age_minutes <= delayed_minutes:
        return DataStatus.OK
    if age_minutes <= stale_minutes:
        return DataStatus.DELAYED
    return DataStatus.STALE


class TwseCollector:
    """Official TWSE MIS real-time adapter with closing-data fallback."""

    def __init__(self, client: httpx.Client | None = None, timeout: float = 15.0,
                 delayed_minutes: int = 30, stale_minutes: int = 120) -> None:
        self.client = client or httpx.Client(
            timeout=timeout,
            headers={"User-Agent": "Mozilla/5.0 taiwan-stock-dashboard/2.0", "Referer": "https://mis.twse.com.tw/stock/index.jsp"},
        )
        self.delayed_minutes = delayed_minutes
        self.stale_minutes = stale_minutes

    def _request_json(self, url: str) -> Any:
        error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.get(url)
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                error = exc
                if attempt < 2:
                    time.sleep(0.4 * (2**attempt))
        raise RuntimeError(f"TWSE request failed for {url}: {error}")

    def _mis_rows(self, symbols: list[Symbol]) -> list[dict]:
        channels = ["tse_t00.tw" if item.kind == "index" else f"tse_{item.symbol}.tw" for item in symbols]
        payload = self._request_json(f"{MIS_API}?ex_ch={quote('|'.join(channels), safe='')}&json=1&delay=0")
        rows = payload.get("msgArray") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or not rows:
            raise ValueError("TWSE MIS response contained no market rows")
        return rows

    def _openapi_rows(self) -> tuple[list[dict], list[dict]]:
        stocks = self._request_json(f"{OPENAPI}/exchangeReport/STOCK_DAY_ALL")
        indices = self._request_json(f"{OPENAPI}/exchangeReport/MI_INDEX")
        if not isinstance(stocks, list) or not isinstance(indices, list):
            raise ValueError("TWSE OpenAPI response was not a list")
        return stocks, indices

    def collect(self, symbols: list[Symbol], scheduled_time: str, now: datetime | None = None) -> list[MarketRecord]:
        now = now or datetime.now(TAIPEI)
        try:
            rows = self._mis_rows(symbols)
            by_code = {str(row.get("c", "")).strip(): row for row in rows}
            return [self._normalize_mis(item, by_code.get("t00" if item.kind == "index" else item.symbol), scheduled_time, now)
                    for item in symbols]
        except (RuntimeError, ValueError):
            stocks, indices = self._openapi_rows()
            stock_by_code = {str(_pick(row, "Code", "證券代號")).strip(): row for row in stocks}
            records: list[MarketRecord] = []
            for item in symbols:
                row = (next((r for r in indices if "發行量加權股價指數" in str(_pick(r, "指數", "Index", "Name"))), None)
                       if item.kind == "index" else stock_by_code.get(item.symbol))
                records.append(self._normalize_closing(item, row, scheduled_time, now))
            return records

    def _mis_time(self, row: dict) -> datetime | None:
        milliseconds = _number(row.get("tlong"))
        if milliseconds:
            return datetime.fromtimestamp(milliseconds / 1000, TAIPEI)
        try:
            return datetime.strptime(f"{row.get('d')} {row.get('t')}", "%Y%m%d %H:%M:%S").replace(tzinfo=TAIPEI)
        except (TypeError, ValueError):
            return None

    def _normalize_mis(self, item: Symbol, row: dict | None, scheduled_time: str, now: datetime) -> MarketRecord:
        if not row:
            return self._unavailable(item, scheduled_time, now, "TWSE MIS")
        market_time = self._mis_time(row)
        last, previous = _number(row.get("z")), _number(row.get("y"))
        raw_volume = _number(row.get("v"))
        return MarketRecord(
            record_id=f"{now.date()}-{scheduled_time}-{item.symbol}", symbol=item.symbol,
            symbol_name=item.name, market=item.market, trading_date=now.date(), scheduled_time=scheduled_time,
            market_data_time=market_time, retrieved_at=now,
            open=_number(row.get("o")), high=_number(row.get("h")), low=_number(row.get("l")),
            last_price=last, previous_close=previous,
            volume=int(raw_volume * 1000) if raw_volume is not None and item.kind != "index" else None,
            turnover=None, data_source="TWSE MIS",
            data_status=_freshness(market_time, now, self.delayed_minutes, self.stale_minutes) if last is not None else DataStatus.UNAVAILABLE,
        )

    def _normalize_closing(self, item: Symbol, row: dict | None, scheduled_time: str, now: datetime) -> MarketRecord:
        if row is None:
            return self._unavailable(item, scheduled_time, now, "TWSE OpenAPI fallback")
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
            turnover=_number(_pick(row, "TradeValue", "成交金額")), data_source="TWSE OpenAPI fallback",
            data_status=DataStatus.DELAYED if last is not None else DataStatus.UNAVAILABLE,
        )

    @staticmethod
    def _unavailable(item: Symbol, scheduled_time: str, now: datetime, source: str) -> MarketRecord:
        return MarketRecord(
            record_id=f"{now.date()}-{scheduled_time}-{item.symbol}", symbol=item.symbol,
            symbol_name=item.name, market=item.market, trading_date=now.date(), scheduled_time=scheduled_time,
            retrieved_at=now, data_source=source, data_status=DataStatus.UNAVAILABLE,
        )
