# Data sources

- TWSE OpenAPI `exchangeReport/STOCK_DAY_ALL`: listed-security daily prices and volume.
- TWSE OpenAPI `exchangeReport/MI_INDEX`: TAIEX daily index values.
- TWSE OpenAPI `holidaySchedule/holidaySchedule`: official exchange open/closure calendar.

Official catalog: <https://openapi.twse.com.tw/>. Endpoints are requested with a timeout and three bounded attempts. No unofficial scraper is used. Closing-data APIs are not guaranteed real-time; the UI therefore exposes `market_data_time`, `retrieved_at`, and `data_status` separately.

