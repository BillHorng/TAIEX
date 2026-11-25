# 台灣股市追蹤儀表板－交接手冊

最後更新：2026-11-25（Asia/Taipei）  
專案儲存庫：<https://github.com/BillHorng/TAIEX>  
正式網站：<https://billhorng.github.io/TAIEX/>

## 1. 專案目的

本系統定時收集臺灣證券交易所公開資料，追蹤以下標的：

- TAIEX（加權股價指數）
- 0050（元大台灣50）
- 0056（元大高股息）

系統會判斷交易日、驗證資料、產生 CSV 與 JSON，並將最新 JSON 發布至 React 儀表板。Google Drive 與 Google Sheets 屬於選用發布目的地；未設定 Google 身分驗證時，不影響本機輸出與 GitHub Pages。

## 2. 目前交付狀態

| 項目 | 狀態 | 說明 |
|---|---|---|
| Python 收集管線 | 完成 | 使用 TWSE 官方 OpenAPI |
| 交易日判定 | 完成 | 週末及年度休市日快取 |
| CSV／JSON 輸出 | 完成 | CSV 為 UTF-8 BOM，JSON 為 UTF-8 |
| React 儀表板 | 完成 | 支援桌面及行動裝置 |
| GitHub CI | 完成 | Python 測試、TypeScript 檢查、前端建置 |
| GitHub Pages | 已上線 | `https://billhorng.github.io/TAIEX/` |
| GitHub 排程 | 完成 | 台北時間 09:00、11:00、13:00、15:00 |
| Google Drive 目錄 | 完成 | 已建立並上傳第一筆 CSV／JSON |
| Google Drive 自動發布 | 程式完成、設定待確認 | 需設定 GitHub WIF 與 repository variables |
| Google Sheets 自動寫入 | 程式完成、尚未啟用 | 需建立試算表、工作表及設定 Sheet ID |

## 3. 系統架構

```text
GitHub Actions 排程／手動執行
              |
              v
      TradingCalendarEngine
              |
              v
        TWSE OpenAPI Adapter
              |
              v
     Pydantic 驗證與狀態判定
        |                 |
        |                 +--> Google Drive／Sheets（選用）
        v
 CSV + JSON + latest.json
              |
              v
       Vite 建置與 Pages 部署
              |
              v
          React 儀表板
```

瀏覽器只讀取 `frontend/public/data/latest.json`，不直接呼叫 TWSE 或 Google API，因此任何雲端憑證都不會進入前端套件。

## 4. 重要目錄與檔案

| 路徑 | 用途 |
|---|---|
| `backend/main.py` | 管線入口、交易日閘門、輸出與發布協調 |
| `backend/collectors/twse.py` | TWSE 官方資料轉接器、重試與欄位正規化 |
| `backend/calendar/engine.py` | 交易日、週末、休市日判定 |
| `backend/models.py` | 資料模型、狀態與漲跌計算 |
| `backend/integrations/google.py` | Drive 上傳與 Sheets 追加 |
| `config/symbols.yaml` | 追蹤標的設定 |
| `config/schedule.yaml` | 台北時區排程與新鮮度設定 |
| `data/calendar/twse-YYYY.json` | 年度休市日快取 |
| `frontend/src/App.tsx` | 儀表板主要介面 |
| `frontend/public/data/latest.json` | Pages 顯示的最新行情快照 |
| `.github/workflows/ci.yml` | 測試與建置驗證 |
| `.github/workflows/track-market.yml` | 定時收集、Google 發布與快照提交 |
| `.github/workflows/deploy-pages.yml` | GitHub Pages 建置與部署 |

## 5. 本機開發

需求：Python 3.12+、Node.js 22+。

```powershell
git clone https://github.com/BillHorng/TAIEX.git
cd TAIEX
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

cd frontend
npm ci
npm run dev
```

開發伺服器的 Vite base path 固定為 `/TAIEX/`。若未來重新命名 GitHub 儲存庫，必須同步修改 `frontend/vite.config.ts`。

## 6. 手動執行行情管線

在專案根目錄執行：

```powershell
python -m backend.main --scheduled-time 15:00
```

週末或休市日會回傳 `SKIPPED`。需要測試收集器時可強制執行：

```powershell
python -m backend.main --force --scheduled-time 15:00
```

啟用已設定的 Google 發布：

```powershell
python -m backend.main --scheduled-time 15:00 --publish-google
```

輸出位置：

- 歷次本機資料：`data/output/`（Git 已忽略）
- Pages 最新快照：`frontend/public/data/latest.json`

## 7. 測試與發布前檢查

後端：

```powershell
python -m pytest --cov=backend --cov-report=term-missing
```

前端：

```powershell
cd frontend
npm ci
npm run check
npm run build
```

目前基準：6 項 Python 測試通過，後端覆蓋率 82%，TypeScript 與 Vite 正式建置通過。

## 8. GitHub Actions 維運

### CI

每次 push 與 pull request 都會執行：

1. 安裝 Python 相依套件。
2. 執行 pytest 與 coverage。
3. 安裝前端鎖定套件。
4. 執行 TypeScript 檢查與正式建置。

### 行情排程

`track-market.yml` 的 UTC cron 對應台北時間如下：

| UTC | Asia/Taipei |
|---|---|
| 01:00 | 09:00 |
| 03:00 | 11:00 |
| 05:00 | 13:00 |
| 07:00 | 15:00 |

GitHub 排程可能因平台負載延遲。前端會顯示資料產生時間，不能假定排程準點即等同即時行情。

手動補跑方式：GitHub → Actions → **Track market** → **Run workflow**。需要在休市日測試時才勾選 `force`。

### GitHub Pages

Pages Source 已設為 **GitHub Actions**。`main` 分支的前端或部署工作流程變更會觸發部署。

## 9. Google Drive 與 Sheets

Drive 專案根目錄：

<https://drive.google.com/drive/folders/1_OsZSyHL4YflXOz3xeBih1xURNc83hLf>

```text
台灣股市追蹤儀表板/
├── 00_管理說明/
├── 01_匯入資料/
├── 02_市場資料/
│   ├── raw_csv/
│   ├── processed_json/
│   └── reports/
└── 03_自動化紀錄/
```

目前 `raw_csv` folder ID：

```text
1_Heg7wdNdWgJ8HXgubeNaZUsVoXSMweW
```

若要讓 GitHub 排程自動發布至 Google，請依 `docs/GOOGLE_API_SETUP.md` 完成 Workload Identity Federation，並設定：

### GitHub Environment Secrets

- `GOOGLE_WORKLOAD_IDENTITY_PROVIDER`
- `GOOGLE_SERVICE_ACCOUNT`

### GitHub Repository／Environment Variables

- `GOOGLE_PUBLISH_ENABLED=true`
- `GOOGLE_DRIVE_FOLDER_ID`
- `GOOGLE_SHEETS_ID`（選用）

必須將目標 Drive 資料夾及 Sheet 分享給該 service account。請勿建立或提交長效 service-account JSON 金鑰。

Sheets 寫入範圍目前設定為 `MarketData!A1`；啟用前必須先建立 `MarketData` 工作表。程式採追加模式，不會覆寫既有資料。

## 10. 資料狀態與執行結果

### Calendar status

- `TRADING_DAY`：可執行收集。
- `WEEKEND`：週末，正常跳過。
- `MARKET_HOLIDAY`：TWSE 公告休市日，正常跳過。
- `SPECIAL_CLOSURE`：特殊休市。
- `CALENDAR_UNKNOWN`：日曆來源無法確認。

### Data status

- `OK`：價格欄位有效。
- `DELAYED`：資料延遲。
- `STALE`：資料已過期。
- `UNAVAILABLE`：TWSE 沒有回傳可用價格。

### Pipeline status

- `SUCCESS`：本機資料產生成功。
- `PARTIAL_SUCCESS`：本機成功，但 Google 目的地失敗。
- `SKIPPED`：非交易日，安全跳過。
- `FAILED`：核心資料收集失敗。

Google 發布失敗不得刪除或覆蓋已成功產生的本機資料。

## 11. 年度例行維護

每年 TWSE 公布下一年度行事曆後：

1. 從 TWSE 官方 `holidaySchedule/holidaySchedule` 取得休市日。
2. 新增 `data/calendar/twse-YYYY.json`。
3. 檢查補行交易日；週末補行交易需明確支援，不能只依 weekday 判斷。
4. 增加年度邊界、休市日與補行交易日測試。
5. 執行完整 CI 後提交。

新增追蹤標的只需修改 `config/symbols.yaml`，但應先確認 TWSE 端點中的代碼與市場類型。

## 12. 常見故障處理

### Pages 顯示 404 或空白頁

1. 確認 Pages Source 仍為 GitHub Actions。
2. 查看 **Deploy Pages** workflow。
3. 確認 `frontend/vite.config.ts` 的 base 為 `/TAIEX/`。
4. 確認 `frontend/public/data/latest.json` 存在且是合法 JSON。

### 行情排程沒有執行

1. 確認 Actions 未被停用。
2. 排程 workflow 長期無 repository 活動時可能被 GitHub 停用。
3. 使用 `workflow_dispatch` 手動補跑。
4. 檢查交易日狀態是否為 `SKIPPED`。

### Drive／Sheets 顯示 `PARTIAL_SUCCESS`

1. 檢查 WIF provider attribute condition 是否限制正確 repository／branch／environment。
2. 確認兩個 Google API 已啟用。
3. 確認資料夾與 Sheet 已分享給 service account。
4. 確認 GitHub variables 的 ID 沒有填入完整 URL。
5. 檢查 `production` environment 是否需要人工核准。

### TWSE 回傳 `UNAVAILABLE`

1. 先查看該次 workflow artifact 或 `data/output/`。
2. 確認標的仍存在於官方端點。
3. 檢查 TWSE 欄位名稱是否變更。
4. 不要以舊行情直接替換成 `OK`。

## 13. 安全規範

- 不得提交 `.env`、OAuth token、service-account JSON 或其他私密金鑰。
- GitHub Actions 優先使用 OIDC／WIF 短效憑證。
- 前端不得直接持有 Google 或 TWSE 私有 token。
- 外部請求必須有 timeout、有限重試與錯誤紀錄。
- 刪除 Drive 檔案或改寫 Git 歷史前必須再次確認目標。

## 14. 接手檢查表

- [ ] 具備 GitHub `BillHorng/TAIEX` 維護權限。
- [ ] 能看到 CI、Track market、Deploy Pages 三個 workflows。
- [ ] 正式網站可以開啟並顯示三個標的。
- [ ] 本機 Python 測試與前端 build 通過。
- [ ] 已閱讀 `ARCHITECTURE.md`、`DATA_SOURCES.md` 與 `GOOGLE_API_SETUP.md`。
- [ ] 若啟用 Google 發布，已驗證 WIF secrets、variables 與分享權限。
- [ ] 已安排每年更新 TWSE 休市日檔案。
- [ ] 知道如何使用 `workflow_dispatch` 手動補跑與判讀 pipeline status。

## 15. 已知限制

- TWSE closing-data OpenAPI 不保證盤中即時；畫面必須以實際時間與狀態呈現。
- TAIEX 日資料端點未必提供完整 OHLC，因此部分圖表欄位可能顯示空值。
- Google Sheets 尚未建立為本專案的正式資料庫；程式支援追加，但啟用前需要完成 Sheet 與 WIF 設定。
- 前端使用 Recharts，主 JavaScript bundle 約 637 KB（gzip 約 187 KB）；目前可正常使用，未來可用動態載入進一步最佳化。

