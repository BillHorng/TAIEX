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


def test_collector_prefers_mis_and_marks_delayed_data() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"msgArray": [
            {"c":"t00","n":"發行量加權股價指數","z":"38195.43","y":"40122.35","o":"39983.91","h":"39983.91","l":"36681.90","d":"20261125","t":"13:33:00"},
            {"c":"0050","n":"元大台灣50","z":"90.30","y":"95.70","o":"91.70","h":"91.85","l":"86.20","v":"436167","d":"20261125","t":"14:30:00"},
        ]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    symbols = [Symbol("TAIEX", "加權股價指數", "TWSE", "index"), Symbol("0050", "元大台灣50", "TWSE", "security")]
    rows = TwseCollector(client, delayed_minutes=30, stale_minutes=120).collect(
        symbols, "15:00", datetime(2026, 11, 25, 14, 35, tzinfo=ZoneInfo("Asia/Taipei"))
    )
    assert rows[0].last_price == 38195.43
    assert rows[0].previous_close == 40122.35
    assert rows[0].data_status == "DELAYED"
    assert rows[1].data_status == "OK"
    assert rows[1].volume == 436_167_000
    assert rows[1].data_source == "TWSE MIS"

