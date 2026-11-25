from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from backend.models import CalendarStatus


@dataclass(frozen=True)
class CalendarData:
    year: int
    holidays: set[date] = field(default_factory=set)
    trading_days: set[date] = field(default_factory=set)
    special_closures: set[date] = field(default_factory=set)
    known: bool = True


class TradingCalendarEngine:
    """Conservative TWSE calendar gate with weekend make-up trading support."""

    def __init__(self, calendar: CalendarData | set[date] | None = None,
                 special_closures: set[date] | None = None) -> None:
        if isinstance(calendar, CalendarData):
            self.calendar = calendar
        else:
            self.calendar = CalendarData(year=0, holidays=calendar or set(), special_closures=special_closures or set())

    def classify(self, day: date) -> tuple[CalendarStatus, str]:
        data = self.calendar
        if not data.known or data.year not in (0, day.year):
            return CalendarStatus.CALENDAR_UNKNOWN, f"No verified TWSE calendar cache for {day.year}"
        if day in data.special_closures:
            return CalendarStatus.SPECIAL_CLOSURE, "TWSE special closure"
        if day in data.trading_days:
            return CalendarStatus.TRADING_DAY, "TWSE published trading day (including make-up sessions)"
        if day in data.holidays:
            return CalendarStatus.MARKET_HOLIDAY, "TWSE published market holiday"
        if day.weekday() >= 5:
            return CalendarStatus.WEEKEND, "Saturday or Sunday with no published make-up session"
        return CalendarStatus.TRADING_DAY, "Regular weekday; no closure in verified calendar cache"
