# Data sources

- TWSE Market Information System (MIS): primary intraday source for TAIEX and tracked ETFs. It provides latest price, previous close, open/high/low, cumulative volume, and the actual market-data timestamp.
- TWSE OpenAPI `exchangeReport/STOCK_DAY_ALL`: fallback listed-security closing prices and volume.
- TWSE OpenAPI `exchangeReport/MI_INDEX`: fallback TAIEX closing values.
- TWSE OpenAPI `holidaySchedule/holidaySchedule`: official exchange open/closure calendar.

Official catalog: <https://openapi.twse.com.tw/>. Official real-time information site: <https://mis.twse.com.tw/>. Endpoints use a timeout and three bounded attempts. The UI exposes `market_data_time`, `retrieved_at`, and `data_status` separately; data older than 30 minutes is `DELAYED`, and data older than 120 minutes is `STALE`.

