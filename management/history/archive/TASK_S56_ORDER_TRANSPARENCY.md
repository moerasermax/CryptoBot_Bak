# 任務膠囊：[S56-UI] 執行層決策透明化與 UI 視覺體感優化 (Revised)

## 🎯 任務目標
1. 解決「下單被攔截卻無聲無息」的排錯困境。
2. 優化 UI 基礎樣式（下拉選單配色），提升高難度環境下的可讀性。
3. 調整策略預設配置，使其更符合多幣種實戰需求。

## 📋 首席工程師實作清單 (Chief Engineer ClaudeCode)

### T1. Executor 異常回流化 (`Application/Trading/StrategyExecutor.cs`)
- [ ] **攔截捕捉**：在 `HandleOpenSignalAsync` 中，當 `RiskCheckResult` 被 Rejected 時，調用 `strategyState.ReportError(riskCheck.Reason)`。
- [ ] **事件廣播**：發送 `Warning` 等級的系統通知，讓 Dashboard 彈出警告。

### T2. 視覺優化：下拉選單配色重構 (CSS/UI)
- [ ] **目標**：修正下拉選單（Select/Dropdown）「白底灰字」難以辨識的問題。
- [ ] **方案**：採用深色擬態或高對比配色（例如：深灰底/亮白字，或亮白底/純黑字），確保在 Glassmorphism 風格下依然清晰。
- [ ] **範圍**：包含 `/lab` 的幣種選單、週期選單，以及全站所有 `select` 標籤。

### T3. 策略預設配置調整
- [ ] **MaxConcurrentPositions**：將 `StrategyConfiguration.cs` 的 `maxConcurrentPositions` 預設值從 1 調整為 **2**，避免單一幣種持倉即鎖死全系統。

### T4. 決策日誌診斷強化 (`DecisionLog.razor`)
- [ ] **診斷顯示**：在日誌中，若訊號被風控攔截，需以特殊顏色（如橘色）標註原因。

## ✅ 驗證檢核點 (VCP)
- **[VCP-1] 故障顯性化**：製造持倉衝突，確認 Dashboard 會跳出「Risk check rejected: ...」警告。
- **[VCP-2] 視覺查核**：檢查全站下拉選單，確認不再出現灰字，且在不同瀏覽器下背景色一致。
- **[VCP-3] 預設值校驗**：新建策略時，預設持倉數應為 2。

## 📤 交付要求
- 完成後回報「執行層診斷與 UI 配色優化已就緒」。
- **必須提供下拉選單 CSS 修改後的代碼片段供審核。**
