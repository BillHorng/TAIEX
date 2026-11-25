from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from backend.collectors import TwseCollector
from backend.config import Symbol


def test_collector_normalizes_official_payload() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("STOCK_DAY_ALL"):
            return httpx.Response(200, json=[{"Code":"0050","Name":"元大台灣50","OpeningPrice":"62.50","HighestPrice":"63.10","LowestPrice":"62.40","ClosingPrice":"62.95","Change":"0.35","TradeVolume":"12,345","TradeValue":"777,000"}])
        return httpx.Response(200, json=[{"指數":"發行量加權股價指數","開盤指數":"27342.2","最高指數":"27511.8","最低指數":"27298.4","收盤指數":"27466.1","漲跌點數":"110.8"}])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    symbols = [Symbol("TAIEX", "加權股價指數", "TWSE", "index"), Symbol("0050", "元大台灣50", "TWSE", "security")]
    rows = TwseCollector(client).collect(symbols, "15:00", datetime(2026, 11, 25, 15, tzinfo=ZoneInfo("Asia/Taipei")))
    assert [r.symbol for r in rows] == ["TAIEX", "0050"]
    assert rows[0].last_price == 27466.1
    assert rows[1].volume == 12345

