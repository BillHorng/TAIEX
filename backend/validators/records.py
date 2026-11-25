from __future__ import annotations

from backend.models import DataStatus, MarketRecord


def validate_records(records: list[MarketRecord]) -> list[str]:
    warnings: list[str] = []
    seen: set[str] = set()
    for row in records:
        if row.record_id in seen:
            warnings.append(f"duplicate record_id: {row.record_id}")
        seen.add(row.record_id)
        if row.data_status == DataStatus.UNAVAILABLE:
            warnings.append(f"{row.symbol}: price unavailable")
        if row.low is not None and row.high is not None and row.low > row.high:
            warnings.append(f"{row.symbol}: low is greater than high")
        if row.last_price is not None and row.last_price < 0:
            warnings.append(f"{row.symbol}: negative last price")
    return warnings

