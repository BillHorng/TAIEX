# Taiwan Stock Market Dashboard

一個以 TWSE 官方 MIS 即時資訊與 OpenAPI 為來源的台灣市場追蹤系統。Python 管線會更新並判斷交易日，再收集 TAIEX、0050、0056，產生 CSV、最新 JSON 與歷史 JSON；Google Drive / Sheets 發布是可選功能。

## 快速開始

需求：Python 3.12+、Node.js 22+。

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m backend.main --force --scheduled-time 15:00
cd frontend
npm install
npm run dev
```

若不加 `--force`，週末與 `data/calendar/` 中的 TWSE 休市日會安全跳過。首次簽入前請以 `npm install` 產生並提交 `frontend/package-lock.json`。

## 設定

- 追蹤標的：`config/symbols.yaml`
- 執行時間：`config/schedule.yaml`
- Google 發布：複製 `.env.example`，依 `docs/GOOGLE_API_SETUP.md` 設定 GitHub WIF 與 repository variables。
- GitHub Pages：依 `docs/GITHUB_SETUP.md` 將 Pages Source 設為 GitHub Actions。

完整維運、部署與接手流程請參閱 [`docs/HANDOFF.md`](docs/HANDOFF.md)。

## 驗證

```bash
pytest --cov=backend
cd frontend && npm run check && npm run build
```

資料僅供資訊展示，不構成投資建議。狀態依官方資料時間計算為 `OK`、`DELAYED`、`STALE` 或 `UNAVAILABLE`，不會以舊資料偽裝即時行情。網站支援歷史日期篩選與當日 CSV 下載。

