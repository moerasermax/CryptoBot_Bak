# 任務膠囊：S23 資料抓取引擎升級 (DataCrawler v2.0)

## 🎯 任務目標
1. **增強容錯能力**：在下載過程中引入 Retry 與速率限制 (Rate Limiting) 適應。
2. **缺口填充 (Gap Filling)**：升級數據抓取流程，自動偵測本地 SQLite 已有的數據，僅下載缺失的時段。
3. **數據完整性檢查**：在寫入 SQLite 前，驗證 K 線時間序列的連續性，記錄並報告數據空洞 (Gaps)。

## 🛠️ 技術上下文 (Full Picture)
- **核心介面**：`IHistoricalDataProvider` (下載) 與 `IHistoricalKlineStore` (存儲)。
- **後端整合**：`OptimizationOrchestrator.EnsureHistoricalAsync` 是主要的消費端。
- **限制條件**：遵守憲章 §1.2，不得將 Retry 邏輯寫在 Domain。

## 📋 實作清單
### T1. 下載引擎健壯化 (Robustness)
- [ ] 在 `BingXHistoricalDataProvider` 引入 Polly 或簡易重試機制，處理 HTTP 429/5xx 錯誤。
- [ ] 增加下載過程中的進度回報 (Logging)，標註目前下載的年份/月份跨度。

### T2. 智慧掃描與填充 (Smart Fetching)
- [ ] 升級 `OptimizationOrchestrator.EnsureHistoricalAsync`：
    - 下載前先呼叫 `IHistoricalKlineStore.GetLatestAsync()` 或查詢現有範圍。
    - 實作「前向填充 (Forward fill)」與「後向填充 (Backward fill)」邏輯，只抓取本地庫存以外的數據。
- [ ] **[VCP-Charter]**：確保查詢邏輯仍然使用 (Symbol, Interval) 作為隔離鍵。

### T3. 連續性驗證 (Data Integrity)
- [ ] 在 `IHistoricalKlineStore.UpsertAsync` 中增加邏輯：偵測傳入的批次是否與前一批次存在時間斷層 (Gaps)。
- [ ] 若偵測到斷層，在 Log 中以 `Warning` 標註缺失的起始與結束時間。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-Functional]**：跑兩次相同的回測區間，第二次下載應該極快（因為數據已在本地）。
- **[VCP-Integrity]**：手動刪除資料庫中某段 K 線，重新啟動，確認系統能自動補齊該段缺口。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
