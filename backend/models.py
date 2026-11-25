from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class CalendarStatus(StrEnum):
    TRADING_DAY = "TRADING_DAY"
    WEEKEND = "WEEKEND"
    MARKET_HOLIDAY = "MARKET_HOLIDAY"
    SPECIAL_CLOSURE = "SPECIAL_CLOSURE"
    CALENDAR_UNKNOWN = "CALENDAR_UNKNOWN"


class DataStatus(StrEnum):
    OK = "OK"
    DELAYED = "DELAYED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class MarketRecord(BaseModel):
    record_id: str
    symbol: str
    symbol_name: str
    market: str = "TWSE"
    trading_date: date
    scheduled_time: str
    market_data_time: datetime | None = None
    retrieved_at: datetime
    open: float | None = None
    high: float | None = None
    low: float | None = None
    last_price: float | None = None
    previous_close: float | None = None
    change_value: float | None = None
    change_percent: float | None = None
    volume: int | None = Field(default=None, ge=0)
    turnover: float | None = Field(default=None, ge=0)
    change_direction: Literal["UP", "DOWN", "FLAT", "UNKNOWN"] = "UNKNOWN"
    data_source: str
    data_status: DataStatus = DataStatus.OK

    @model_validator(mode="after")
    def calculate_change(self) -> "MarketRecord":
        if self.last_price is not None and self.previous_close not in (None, 0):
            self.change_value = round(self.last_price - self.previous_close, 4)
            self.change_percent = round(self.change_value / self.previous_close * 100, 4)
            self.change_direction = "UP" if self.change_value > 0 else "DOWN" if self.change_value < 0 else "FLAT"
        return self


class RunSummary(BaseModel):
    run_id: str
    generated_at: datetime
    trading_date: date
    scheduled_time: str
    timezone: str = "Asia/Taipei"
    calendar_status: CalendarStatus
    calendar_note: str
    pipeline_status: Literal["SUCCESS", "PARTIAL_SUCCESS", "SKIPPED", "FAILED"]
    records: list[MarketRecord] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

