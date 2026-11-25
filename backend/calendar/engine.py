from __future__ import annotations

from datetime import date

from backend.models import CalendarStatus


class TradingCalendarEngine:
    """Conservative market-day gate.

    Holiday dates are refreshed by ``scripts/update_calendar.py`` from the official
    TWSE holiday endpoint and committed as a small year-specific cache.
    """

    def __init__(self, holidays: set[date] | None = None, special_closures: set[date] | None = None) -> None:
        self.holidays = holidays or set()
        self.special_closures = special_closures or set()

    def classify(self, day: date) -> tuple[CalendarStatus, str]:
        if day in self.special_closures:
            return CalendarStatus.SPECIAL_CLOSURE, "TWSE special closure"
        if day in self.holidays:
            return CalendarStatus.MARKET_HOLIDAY, "TWSE published market holiday"
        if day.weekday() >= 5:
            return CalendarStatus.WEEKEND, "Saturday or Sunday"
        return CalendarStatus.TRADING_DAY, "Regular weekday; no closure in calendar cache"

