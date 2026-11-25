from datetime import date

from backend.calendar import TradingCalendarEngine
from backend.models import CalendarStatus


def test_weekend_is_closed() -> None:
    assert TradingCalendarEngine().classify(date(2026, 11, 28))[0] == CalendarStatus.WEEKEND


def test_holiday_is_closed_before_weekday_rule() -> None:
    day = date(2026, 12, 25)
    assert TradingCalendarEngine({day}).classify(day)[0] == CalendarStatus.MARKET_HOLIDAY


def test_regular_weekday_is_trading_day() -> None:
    assert TradingCalendarEngine().classify(date(2026, 11, 25))[0] == CalendarStatus.TRADING_DAY

