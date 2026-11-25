from datetime import date

from backend.calendar import CalendarData, TradingCalendarEngine
from backend.models import CalendarStatus


def test_weekend_is_closed() -> None:
    assert TradingCalendarEngine().classify(date(2026, 11, 28))[0] == CalendarStatus.WEEKEND


def test_holiday_is_closed_before_weekday_rule() -> None:
    day = date(2026, 12, 25)
    assert TradingCalendarEngine({day}).classify(day)[0] == CalendarStatus.MARKET_HOLIDAY


def test_regular_weekday_is_trading_day() -> None:
    assert TradingCalendarEngine().classify(date(2026, 11, 25))[0] == CalendarStatus.TRADING_DAY


def test_weekend_makeup_session_is_trading_day() -> None:
    day = date(2026, 12, 5)
    calendar = CalendarData(year=2026, trading_days={day})
    assert TradingCalendarEngine(calendar).classify(day)[0] == CalendarStatus.TRADING_DAY


def test_missing_calendar_is_unknown() -> None:
    calendar = CalendarData(year=2026, known=False)
    assert TradingCalendarEngine(calendar).classify(date(2026, 11, 25))[0] == CalendarStatus.CALENDAR_UNKNOWN

