from backend.calendar.refresh import parse_calendar, roc_date


def test_roc_date_conversion() -> None:
    assert roc_date("1160104").isoformat() == "2027-01-04"


def test_calendar_parser_separates_closures_and_trading_days() -> None:
    result = parse_calendar([
        {"Date": "1160101", "Name": "開國紀念日", "Description": "依規定放假1日。"},
        {"Date": "1160104", "Name": "國曆新年開始交易日", "Description": "開始交易。"},
        {"Date": "1160202", "Name": "市場無交易", "Description": ""},
        {"Date": "1160701", "Name": "天然災害停止交易", "Description": "特殊休市"},
    ])[2027]
    assert result["holidays"] == {"2027-01-01", "2027-02-02"}
    assert result["trading_days"] == {"2027-01-04"}
    assert result["special_closures"] == {"2027-07-01"}
