# 任務膠囊：S25 數據持久化與分析強化 (Data Insight)

## 🎯 任務目標
1. **排行榜持久化**：實作最佳化結果自動存檔，確保刷新網頁後仍能載入歷史最佳參數。
2. **權益曲線數據**：擴充回測報告，包含每個交易點（或每根 K 線）的權益序列資料。
3. **實驗室記憶功能**：在 `/lab` 頁面實作「載入上次最佳組合」的顯示邏輯。

## 🛠️ 技術上下文 (Full Picture)
- **實體與倉儲**：已存在 `StrategyOptimizationSettings` 與 `IStrategyOptimizationSettingsRepository`。
- **回測引擎**：`BacktestEngine.cs` 是生產權益數據的核心位置。
- **前端連動**：`LabStateContainer` 是目前 Singleton 的狀態中轉站。

## 📋 實作清單
### T1. 最佳化結果存檔 (Persistence)
- [ ] 修改 `OptimizationOrchestrator.BroadcastCompletedAsync`：
    - 在廣播完成前，將 Leaderboard 中的 Top 1（或特定權重的 Top 組合）透過 Repository 存入資料庫。
    - 注意：必須考慮 (StrategyId, Symbol, Interval) 的唯一性。
- [ ] 實作 API 端點：`GET /api/lab/cached-settings/{strategyId}`，支援根據目前的 Symbol/Interval 過濾。

### T2. 權益序列採集 (Analytics)
- [ ] 修改 `BacktestReport` 記錄，新增 `IReadOnlyList<EquityPoint> EquityCurve` 欄位。
- [ ] 在 `BacktestEngine.RunAsync` 中，每根 K 線處理完畢後，記錄當前的 `currentEquity` 與時間戳。
- [ ] **[VCP-Charter]**：確保記錄頻率不會導致記憶體爆炸（若回測期間超長，建議每 N 根記錄一次或僅記錄成交點）。

### T3. UI 記憶顯示 (Frontend)
- [ ] 修改 `BacktestLab.razor`：
    - 當使用者選擇策略或切換 Window 時，異步呼叫快取 API。
    - 若有快取紀錄，在 UI 顯示「上次最佳結果：Sharpe=X, Params=Y」，並提供「快速填入」按鈕。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Build]**：`dotnet build` 0 錯誤 0 警告。
- **[VCP-Persistence]**：手動跑一次優化掃描，重啟系統後進入 `/lab`，確認能看到上次的最佳參數記憶。
- **[VCP-Data]**：確認 API 回傳的 `BacktestReport` 包含 `EquityCurve` 陣列，且數據點時間序列連續。

## 📤 交付要求
- 完成後回報「實作已就緒，請 Gemini 進行 VCP 驗證」。
- **必須附上受影響檔案清單。**
