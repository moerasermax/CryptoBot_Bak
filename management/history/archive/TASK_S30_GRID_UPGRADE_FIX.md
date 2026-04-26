# 任務膠囊：[S30-GRID] 3萬格網格升級與填入功能修復

## 🎯 任務目標
1. **解除性能封印**：將回測實驗室 (Lab) 的網格數量上限從 2,000 提升至 **30,000** 組組合，以支援高精度的 AI 網格決策。
2. **修復填入邏輯**：解決點擊「填入建議參數」後，表單數值未跳轉的問題。

## 🛠️ 技術細節 (Technical Context)
- **硬編碼限制**：`BacktestLab.razor` 中存在 2,000 格的警告門檻。
- **鍵名衝突 (Key Mismatch)**：AI 輸出的 JSON 鍵名（如 `rsi_period`）常與表單期待的強型別鍵名（如 `RsiPeriod`）不符。
- **狀態更新**：部分表單在 `ApplyGridParametersAsync` 後未正確觸發 `NotifyChangedAsync()`，導致 UI 指示器不同步。

## 📋 實作清單

### T1. UI 限制放寬 (ConsoleApp/Pages)
- [ ] 修改 `BacktestLab.razor`：
    - 將 `ApplyAiSuggestedParametersAsync` 中的警告門檻由 `2000` 改為 `30000`。
    - 更新 Toast 訊息文字，明確告知使用者 3 萬格以內為正常範圍。

### T2. 策略表單韌性強化 (ConsoleApp/Lab Components)
針對以下所有表單組件更新其 `ApplyGridParametersAsync` 實作：
- `B46ParameterForm.razor`
- `MeanReversionParameterForm.razor`
- `TrendFollowingParameterForm.razor`
- `SmaParameterForm.razor`

**具體要求：**
- [ ] **不感大小寫查詢**：將傳入的 `IDictionary` 轉換為 `StringComparer.OrdinalIgnoreCase` 的新字典。
- [ ] **同義詞對應 (Synonyms)**：
    - `RsiPeriod` 應同時支援 `rsi_period` / `rsi` / `RsiPeriod`。
    - `Oversold` 應支援 `rsi_oversold` / `low_rsi`。
    - `Overbought` 應支援 `rsi_overbought` / `high_rsi`。
    - 其餘參數依此類推（BB Period, BB StdDev, FastPeriod, SlowPeriod...）。
- [ ] **UI 連動**：方法結尾必須呼叫 `await NotifyChangedAsync();` 確保父頁面 `Grid size` 數字立即跳轉。

### T3. 後端邊界檢查 (Api)
- [ ] 巡檢 `src/CryptoBot.ConsoleApp/Api/LabEndpoints.cs` 與 `OptimizationOrchestrator.cs`，確保沒有殘留的低上限攔截邏輯。

## ✅ 驗證檢核點 (VCP)
- **[VCP-Sync]**：點擊「填入建議參數」後，表單內的 Min/Max/Step 數值必須確實發生變化。
- **[VCP-GridSize]**：填入後，UI 下方的 "Grid size" 指示器應正確顯示（例如 16,740）。
- **[VCP-Limit]**：調整 Step 使總組合數達到 25,000，確認仍能按「開始優化掃描」且不跳出錯誤 Toast。
- **[VCP-Build]**：全專案編譯 0 Error / 0 Warning。

## 📤 交付要求
- 完成後回報「3萬格網格升級與填入修復已就緒」。
- **請附上 B46 策略表單更新後的 `ApplyGridParametersAsync` 代碼片段作為驗證。**
